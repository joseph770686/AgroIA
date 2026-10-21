# ============================================================
# AGROVISION AI
# Entrenamiento del modelo de clasificación de cultivos
# MobileNetV2 + PyTorch
# ============================================================

from pathlib import Path
import json
import copy
import time

import torch
import torch.nn as nn
import torch.optim as optim

from torch.utils.data import DataLoader
from torchvision import datasets, transforms
from torchvision.models import mobilenet_v2, MobileNet_V2_Weights

from sklearn.metrics import classification_report


# ============================================================
# 1. CONFIGURACIÓN
# ============================================================

# Carpeta principal del proyecto
BASE_DIR = Path(__file__).resolve().parent

# Carpetas del dataset
TRAIN_DIR = BASE_DIR / "dataset" / "train"
VAL_DIR = BASE_DIR / "dataset" / "val"

# Carpeta donde guardaremos el modelo
MODEL_DIR = BASE_DIR / "modelos"
MODEL_DIR.mkdir(parents=True, exist_ok=True)

# Archivos de salida
MODEL_PATH = MODEL_DIR / "modelo_cultivos.pth"
CLASSES_PATH = MODEL_DIR / "clases.json"

# Tamaño de las imágenes
IMAGE_SIZE = 224

# Cantidad de imágenes procesadas por lote
BATCH_SIZE = 32

# Número máximo de épocas
EPOCHS = 15

# Tasa de aprendizaje
LEARNING_RATE = 0.001

# Número de trabajadores
# En Windows dejamos 0 para evitar problemas.
NUM_WORKERS = 0


# ============================================================
# 2. DISPOSITIVO
# ============================================================

if torch.cuda.is_available():
    DEVICE = torch.device("cuda")
    print("GPU detectada:", torch.cuda.get_device_name(0))
else:
    DEVICE = torch.device("cpu")
    print("No se detectó GPU. Se utilizará CPU.")

print("Dispositivo utilizado:", DEVICE)


# ============================================================
# 3. COMPROBAR CARPETAS
# ============================================================

if not TRAIN_DIR.exists():
    raise FileNotFoundError(
        f"No se encontró la carpeta de entrenamiento:\n{TRAIN_DIR}"
    )

if not VAL_DIR.exists():
    raise FileNotFoundError(
        f"No se encontró la carpeta de validación:\n{VAL_DIR}"
    )


# ============================================================
# 4. TRANSFORMACIONES DE IMÁGENES
# ============================================================

# Transformaciones para entrenamiento.
# Estas modificaciones ayudan a que el modelo no memorice
# exactamente las imágenes originales.

train_transforms = transforms.Compose([
    transforms.Resize((IMAGE_SIZE, IMAGE_SIZE)),

    transforms.RandomHorizontalFlip(p=0.5),

    transforms.RandomRotation(15),

    transforms.ColorJitter(
        brightness=0.2,
        contrast=0.2,
        saturation=0.2
    ),

    transforms.ToTensor(),

    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225]
    )
])


# Transformaciones para validación.
# Aquí NO hacemos modificaciones aleatorias.

val_transforms = transforms.Compose([
    transforms.Resize((IMAGE_SIZE, IMAGE_SIZE)),

    transforms.ToTensor(),

    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225]
    )
])


# ============================================================
# 5. CARGAR DATASET
# ============================================================

print("\nCargando dataset...")

train_dataset = datasets.ImageFolder(
    root=str(TRAIN_DIR),
    transform=train_transforms
)

val_dataset = datasets.ImageFolder(
    root=str(VAL_DIR),
    transform=val_transforms
)


# ============================================================
# 6. COMPROBAR CLASES
# ============================================================

print("\nClases encontradas:")

for i, clase in enumerate(train_dataset.classes):
    print(f"{i}: {clase}")


if train_dataset.classes != val_dataset.classes:
    raise ValueError(
        "\nERROR: Las clases de train y val no coinciden.\n"
        f"Train: {train_dataset.classes}\n"
        f"Val:   {val_dataset.classes}"
    )


NUM_CLASSES = len(train_dataset.classes)

print(f"\nNúmero de clases: {NUM_CLASSES}")

if NUM_CLASSES != 7:
    print(
        "\nADVERTENCIA: Se esperaban 7 clases para AgroVision AI."
    )


# ============================================================
# 7. GUARDAR NOMBRES DE LAS CLASES
# ============================================================

informacion_clases = {
    "clases": train_dataset.classes,
    "tamano_imagen": IMAGE_SIZE,
    "num_clases": NUM_CLASSES
}

with open(CLASSES_PATH, "w", encoding="utf-8") as archivo:
    json.dump(
        informacion_clases,
        archivo,
        indent=4,
        ensure_ascii=False
    )

print(f"\nClases guardadas en: {CLASSES_PATH}")


# ============================================================
# 8. MOSTRAR CANTIDAD DE IMÁGENES POR CLASE
# ============================================================

print("\nCantidad de imágenes para entrenamiento:")

conteos = [0] * NUM_CLASSES

for _, indice_clase in train_dataset.samples:
    conteos[indice_clase] += 1

for indice, cantidad in enumerate(conteos):
    print(
        f"{train_dataset.classes[indice]:<20} "
        f"{cantidad:>5} imágenes"
    )


# ============================================================
# 9. PESOS PARA LAS CLASES
# ============================================================

# Como nuestro dataset está desbalanceado, calculamos pesos.
#
# Las clases con menos imágenes tendrán mayor peso durante
# el entrenamiento.

total_imagenes = sum(conteos)

class_weights = []

for cantidad in conteos:

    if cantidad == 0:
        peso = 0.0
    else:
        peso = total_imagenes / (NUM_CLASSES * cantidad)

    class_weights.append(peso)


class_weights = torch.tensor(
    class_weights,
    dtype=torch.float32
).to(DEVICE)


print("\nPesos de las clases:")

for clase, peso in zip(
    train_dataset.classes,
    class_weights
):
    print(f"{clase:<20} {peso.item():.4f}")


# ============================================================
# 10. DATALOADERS
# ============================================================

train_loader = DataLoader(
    train_dataset,
    batch_size=BATCH_SIZE,
    shuffle=True,
    num_workers=NUM_WORKERS
)

val_loader = DataLoader(
    val_dataset,
    batch_size=BATCH_SIZE,
    shuffle=False,
    num_workers=NUM_WORKERS
)


# ============================================================
# 11. CARGAR MOBILENETV2
# ============================================================

print("\nCargando MobileNetV2 preentrenado...")

weights = MobileNet_V2_Weights.DEFAULT

model = mobilenet_v2(weights=weights)


# ============================================================
# 12. CONGELAR LAS CARACTERÍSTICAS
# ============================================================

# Primero congelamos las capas que ya aprendieron
# características generales de imágenes.

for parametro in model.features.parameters():
    parametro.requires_grad = False


# ============================================================
# 13. CAMBIAR CLASIFICADOR
# ============================================================

# MobileNetV2 originalmente clasifica 1000 categorías.
# Nosotros necesitamos solamente nuestras 7 clases.

numero_entradas = model.classifier[1].in_features

model.classifier[1] = nn.Linear(
    numero_entradas,
    NUM_CLASSES
)

model = model.to(DEVICE)


# ============================================================
# 14. FUNCIÓN DE PÉRDIDA
# ============================================================

criterion = nn.CrossEntropyLoss(
    weight=class_weights
)


# ============================================================
# 15. OPTIMIZADOR
# ============================================================

optimizer = optim.Adam(
    model.classifier.parameters(),
    lr=LEARNING_RATE
)


# ============================================================
# 16. ENTRENAMIENTO
# ============================================================

print("\n")
print("=" * 60)
print("INICIANDO ENTRENAMIENTO")
print("=" * 60)

best_val_loss = float("inf")
best_model_weights = copy.deepcopy(model.state_dict())

inicio_total = time.time()


for epoch in range(EPOCHS):

    inicio_epoca = time.time()

    # --------------------------------------------------------
    # TRAIN
    # --------------------------------------------------------

    model.train()

    train_loss = 0.0
    train_correctos = 0
    train_total = 0

    for imagenes, etiquetas in train_loader:

        imagenes = imagenes.to(DEVICE)
        etiquetas = etiquetas.to(DEVICE)

        # Limpiar gradientes
        optimizer.zero_grad()

        # Predicción
        salidas = model(imagenes)

        # Error
        loss = criterion(salidas, etiquetas)

        # Backpropagation
        loss.backward()

        # Actualizar pesos
        optimizer.step()

        # Acumular pérdida
        train_loss += loss.item() * imagenes.size(0)

        # Calcular aciertos
        _, predicciones = torch.max(
            salidas,
            1
        )

        train_total += etiquetas.size(0)

        train_correctos += (
            predicciones == etiquetas
        ).sum().item()


    train_loss = train_loss / train_total

    train_accuracy = (
        train_correctos / train_total
    )


    # --------------------------------------------------------
    # VALIDATION
    # --------------------------------------------------------

    model.eval()

    val_loss = 0.0
    val_correctos = 0
    val_total = 0

    with torch.no_grad():

        for imagenes, etiquetas in val_loader:

            imagenes = imagenes.to(DEVICE)
            etiquetas = etiquetas.to(DEVICE)

            salidas = model(imagenes)

            loss = criterion(
                salidas,
                etiquetas
            )

            val_loss += (
                loss.item() * imagenes.size(0)
            )

            _, predicciones = torch.max(
                salidas,
                1
            )

            val_total += etiquetas.size(0)

            val_correctos += (
                predicciones == etiquetas
            ).sum().item()


    val_loss = val_loss / val_total

    val_accuracy = (
        val_correctos / val_total
    )


    # --------------------------------------------------------
    # GUARDAR MEJOR MODELO
    # --------------------------------------------------------

    if val_loss < best_val_loss:

        best_val_loss = val_loss

        best_model_weights = copy.deepcopy(
            model.state_dict()
        )

        torch.save(
            model.state_dict(),
            MODEL_PATH
        )

        mejor = " ← MEJOR MODELO"

    else:

        mejor = ""


    tiempo_epoca = time.time() - inicio_epoca


    print(
        f"\nÉpoca [{epoch + 1}/{EPOCHS}]"
    )

    print(
        f"Train Loss: {train_loss:.4f}"
    )

    print(
        f"Train Accuracy: {train_accuracy * 100:.2f}%"
    )

    print(
        f"Val Loss: {val_loss:.4f}"
    )

    print(
        f"Val Accuracy: {val_accuracy * 100:.2f}%"
    )

    print(
        f"Tiempo: {tiempo_epoca:.1f} segundos"
    )

    if mejor:
        print(mejor)


# ============================================================
# 17. CARGAR MEJOR MODELO
# ============================================================

print("\nCargando el mejor modelo...")

model.load_state_dict(best_model_weights)

model.eval()


# ============================================================
# 18. EVALUACIÓN FINAL
# ============================================================

print("\n")
print("=" * 60)
print("EVALUACIÓN FINAL")
print("=" * 60)

todas_etiquetas = []
todas_predicciones = []

with torch.no_grad():

    for imagenes, etiquetas in val_loader:

        imagenes = imagenes.to(DEVICE)

        salidas = model(imagenes)

        _, predicciones = torch.max(
            salidas,
            1
        )

        todas_etiquetas.extend(
            etiquetas.numpy()
        )

        todas_predicciones.extend(
            predicciones.cpu().numpy()
        )


reporte = classification_report(
    todas_etiquetas,
    todas_predicciones,
    target_names=train_dataset.classes,
    zero_division=0
)

print("\nReporte de clasificación:\n")

print(reporte)


# ============================================================
# 19. GUARDAR REPORTE
# ============================================================

REPORT_PATH = MODEL_DIR / "reporte_entrenamiento.txt"

with open(
    REPORT_PATH,
    "w",
    encoding="utf-8"
) as archivo:

    archivo.write(
        "AGROVISION AI - REPORTE DE ENTRENAMIENTO\n"
    )

    archivo.write("=" * 60 + "\n\n")

    archivo.write(
        f"Clases: {NUM_CLASSES}\n"
    )

    archivo.write(
        f"Épocas: {EPOCHS}\n"
    )

    archivo.write(
        f"Tamaño de imagen: {IMAGE_SIZE}x{IMAGE_SIZE}\n"
    )

    archivo.write(
        f"Batch size: {BATCH_SIZE}\n"
    )

    archivo.write(
        f"Learning rate: {LEARNING_RATE}\n\n"
    )

    archivo.write(
        "Clases:\n"
    )

    for indice, clase in enumerate(
        train_dataset.classes
    ):

        archivo.write(
            f"{indice}: {clase}\n"
        )

    archivo.write(
        "\nReporte de clasificación:\n\n"
    )

    archivo.write(reporte)


# ============================================================
# 20. INFORMACIÓN FINAL
# ============================================================

tiempo_total = time.time() - inicio_total

print("\n")
print("=" * 60)
print("ENTRENAMIENTO TERMINADO")
print("=" * 60)

print(
    f"\nModelo guardado en:"
    f"\n{MODEL_PATH}"
)

print(
    f"\nClases guardadas en:"
    f"\n{CLASSES_PATH}"
)

print(
    f"\nReporte guardado en:"
    f"\n{REPORT_PATH}"
)

print(
    f"\nTiempo total:"
    f" {tiempo_total / 60:.2f} minutos"
)

print("\nAgroVision AI ya tiene su primer modelo. 🤖🌱")