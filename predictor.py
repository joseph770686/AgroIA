# ============================================================
# AGROVISION AI
# Predictor de cultivos
# MobileNetV2 + PyTorch
# ============================================================

from pathlib import Path
import json


import torch
import torch.nn as nn
from PIL import Image
from torchvision import transforms
from torchvision.models import mobilenet_v2


# ============================================================
# 1. RUTAS DEL PROYECTO
# ============================================================

# predictor.py está en:
# backend/services/predictor.py
#
# parents[0] = services
# parents[1] = backend
# parents[2] = AgrovisionIA

BASE_DIR = Path(__file__).resolve().parent

MODEL_PATH = BASE_DIR.joinpath("modelos", "modelo_cultivos.pth")
CLASSES_PATH = BASE_DIR.joinpath("modelos", "clases.json")


# ============================================================
# 2. CONFIGURACIÓN
# ============================================================

IMAGE_SIZE = 224

DEVICE = torch.device(
    "cuda" if torch.cuda.is_available() else "cpu"
)


# ============================================================
# 3. CARGAR CLASES
# ============================================================

if not CLASSES_PATH.exists():
    raise FileNotFoundError(
        f"No se encontró el archivo de clases:\n{CLASSES_PATH}"
    )


with open(
    CLASSES_PATH,
    "r",
    encoding="utf-8"
) as archivo:

    informacion_clases = json.load(archivo)


CLASSES = informacion_clases["clases"]

NUM_CLASSES = len(CLASSES)


# ============================================================
# 4. CREAR MODELO
# ============================================================

model = mobilenet_v2(
    weights=None
)


# MobileNetV2 originalmente tiene 1000 clases.
# Nosotros necesitamos nuestras 7 clases.

numero_entradas = model.classifier[1].in_features

model.classifier[1] = nn.Linear(
    numero_entradas,
    NUM_CLASSES
)


# ============================================================
# 5. CARGAR PESOS ENTRENADOS
# ============================================================

if not MODEL_PATH.exists():
    raise FileNotFoundError(
        f"No se encontró el modelo:\n{MODEL_PATH}"
    )


state_dict = torch.load(
    MODEL_PATH,
    map_location=DEVICE
)

model.load_state_dict(state_dict)

model = model.to(DEVICE)

model.eval()


# ============================================================
# 6. TRANSFORMACIONES
# ============================================================

transformacion = transforms.Compose([

    transforms.Resize(
        (IMAGE_SIZE, IMAGE_SIZE)
    ),

    transforms.ToTensor(),

    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225]
    )
])


# ============================================================
# 7. FUNCIÓN DE PREDICCIÓN
# ============================================================

def predecir(imagen):
    """
    Recibe una imagen PIL y devuelve:

    {
        "clase": "...",
        "confianza": ...,
        "probabilidades": {...}
    }
    """

    # --------------------------------------------------------
    # Convertir imagen a RGB
    # --------------------------------------------------------

    imagen = imagen.convert("RGB")


    # --------------------------------------------------------
    # Aplicar transformaciones
    # --------------------------------------------------------

    imagen_tensor = transformacion(
        imagen
    )


    # Agregar dimensión del batch

    imagen_tensor = imagen_tensor.unsqueeze(0)

    imagen_tensor = imagen_tensor.to(DEVICE)


    # --------------------------------------------------------
    # Realizar predicción
    # --------------------------------------------------------

    with torch.no_grad():

        salida = model(
            imagen_tensor
        )

        probabilidades = torch.softmax(
            salida,
            dim=1
        )[0]


    # --------------------------------------------------------
    # Obtener clase con mayor probabilidad
    # --------------------------------------------------------

    indice_prediccion = torch.argmax(
        probabilidades
    ).item()


    clase_predicha = CLASSES[
        indice_prediccion
    ]


    confianza = probabilidades[
        indice_prediccion
    ].item()


    # --------------------------------------------------------
    # Crear diccionario con todas las probabilidades
    # --------------------------------------------------------

    todas_probabilidades = {}

    for indice, clase in enumerate(CLASSES):

        todas_probabilidades[clase] = round(
            probabilidades[indice].item() * 100,
            2
        )


    # --------------------------------------------------------
    # Resultado
    # --------------------------------------------------------

    resultado = {

        "clase": clase_predicha,

        "confianza": round(
            confianza * 100,
            2
        ),

        "probabilidades": todas_probabilidades
    }


    return resultado


# ============================================================
# 8. FUNCIÓN PARA OBTENER INFORMACIÓN DEL RESULTADO
# ============================================================

def interpretar_clase(clase):
    """
    Convierte la clase técnica del modelo en información
    más fácil de utilizar posteriormente en el frontend.
    """

    informacion = {

        "arroz_sano": {
            "cultivo": "Arroz",
            "estado": "Sano",
            "tipo": "Sano"
        },

        "arroz_enfermo": {
            "cultivo": "Arroz",
            "estado": "Enfermo",
            "tipo": "Enfermedad"
        },

        "frijol_sano": {
            "cultivo": "Frijol",
            "estado": "Sano",
            "tipo": "Sano"
        },

        "frijol_enfermo": {
            "cultivo": "Frijol",
            "estado": "Enfermo",
            "tipo": "Enfermedad"
        },

        "maiz_sano": {
            "cultivo": "Maíz",
            "estado": "Sano",
            "tipo": "Sano"
        },

        "maiz_enfermo": {
            "cultivo": "Maíz",
            "estado": "Enfermo",
            "tipo": "Enfermedad"
        },

        "maiz_plaga": {
            "cultivo": "Maíz",
            "estado": "Afectado",
            "tipo": "Plaga"
        }
    }


    return informacion.get(
        clase,
        {
            "cultivo": "Desconocido",
            "estado": "Desconocido",
            "tipo": "Desconocido"
        }
    )


# ============================================================
# 9. INFORMACIÓN DEL MODELO
# ============================================================

def obtener_informacion_modelo():

    return {

        "modelo": "MobileNetV2",

        "clases": CLASSES,

        "numero_clases": NUM_CLASSES,

        "tamano_imagen": IMAGE_SIZE,

        "dispositivo": str(DEVICE)
    }

if __name__ == "__main__":
    from tkinter import Tk, filedialog
    from PIL import Image

    # Ocultar ventana principal de Tkinter
    root = Tk()
    root.withdraw()

    # Seleccionar imagen desde los archivos
    ruta = filedialog.askopenfilename(
        title="Selecciona una imagen del cultivo",
        filetypes=[
            ("Imágenes", "*.jpg *.jpeg *.png *.webp"),
            ("Todos los archivos", "*.*")
        ]
    )

    if not ruta:
        print("No seleccionaste ninguna imagen.")
        exit()

    print("\nImagen seleccionada:")
    print(ruta)

    # Abrir imagen
    imagen = Image.open(ruta)

    # Ejecutar predicción
    resultado = predecir(imagen)

    print("\n==============================")
    print("     RESULTADO AGROVISION AI")
    print("==============================")
    print(f"Clase: {resultado['clase']}")
    print(f"Confianza: {resultado['confianza']}%")

    print("\nProbabilidades:")
    for clase, probabilidad in resultado["probabilidades"].items():
        print(f"  {clase}: {probabilidad}%")

    print("\nInterpretación:")
    print(interpretar_clase(resultado["clase"]))