from pathlib import Path
from uuid import uuid4
from backend.database.connection import obtener_conexion
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from PIL import Image
from io import BytesIO
import sys
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from backend.authz import obtener_usuario_actual
from fastapi import Depends, HTTPException
from backend.database.connection import obtener_conexion
from backend.authz import obtener_usuario_actual
from backend.authz import requiere_admin
# ==========================================
# CONFIGURACIÓN DE RUTAS
# ==========================================

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"

sys.path.append(str(BASE_DIR))

from predictor import predecir, interpretar_clase

# Importar las rutas de autenticación
from backend.routes.auth import router as auth_router

# ==========================================
# FASTAPI
# ==========================================

app = FastAPI(
    title="AgroVision AI",
    description="Sistema de análisis inteligente de cultivos",
    version="1.0.0"
)

# ==========================================
# CORS
# ==========================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================================
# FRONTEND
# ==========================================

app.mount(
    "/frontend",
    StaticFiles(directory=FRONTEND_DIR),
    name="frontend"
)

# ==========================================
# AUTENTICACIÓN
# ==========================================

app.include_router(auth_router)

# ==========================================
# PÁGINAS
# ==========================================

@app.get("/")
def inicio():
    # Por ahora, la entrada muestra el login.
    return FileResponse(FRONTEND_DIR / "login.html")


@app.get("/login")
def pagina_login():
    return FileResponse(FRONTEND_DIR / "login.html")


@app.get("/registro")
def pagina_registro():
    return FileResponse(FRONTEND_DIR / "registro.html")


@app.get("/panel")
def pagina_panel():
    return FileResponse(FRONTEND_DIR / "index.html")


# ==========================================
# ANALIZAR IMAGEN
# ==========================================


@app.post("/analizar")
async def analizar_cultivo(
    file: UploadFile = File(...),
    usuario: dict = Depends(obtener_usuario_actual)
):
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=400,
            detail="El archivo debe ser una imagen."
        )

    conexion = None
    cursor = None
    ruta_imagen = None

    try:
        # Obtener el usuario autenticado
        id_usuario = usuario.get("id_usuario")

        if id_usuario is None:
            raise HTTPException(
                status_code=401,
                detail="No se pudo identificar al usuario."
            )

        # Leer y validar la imagen
        contenido = await file.read()

        imagen = Image.open(BytesIO(contenido)).convert("RGB")

        # Ejecutar la predicción
        resultado = predecir(imagen)
        informacion = interpretar_clase(resultado["clase"])

        clase = str(resultado["clase"]).lower()
        confianza = float(resultado["confianza"])

        # Identificar el cultivo a partir de la clase del modelo
        if clase.startswith("arroz_"):
            nombre_planta = "Arroz"
        elif clase.startswith("frijol_"):
            nombre_planta = "Frijol"
        elif clase.startswith("maiz_") or clase.startswith("maíz_"):
            nombre_planta = "Maíz"
        else:
            raise HTTPException(
                status_code=422,
                detail=f"No se reconoce el cultivo: {clase}"
            )

        # Determinar estado del cultivo
        if "sano" in clase:
            estado = "Sano"
        elif "plaga" in clase:
            estado = "Plaga"
        else:
            estado = "Enfermo"

        # Extraer información del diagnóstico
        if isinstance(informacion, dict):
            enfermedad = (
                informacion.get("enfermedad")
                or informacion.get("titulo")
                or clase
            )
            recomendacion = (
                informacion.get("recomendacion")
                or informacion.get("tratamiento")
                or "Consultar las recomendaciones agrícolas para este cultivo."
            )
        else:
            enfermedad = clase
            recomendacion = str(informacion)

        # Preparar carpeta y guardar la imagen
        carpeta = Path(__file__).resolve().parent / "uploads" / "analisis"
        carpeta.mkdir(parents=True, exist_ok=True)

        nombre_archivo = f"{uuid4().hex}.jpg"
        ruta_imagen = carpeta / nombre_archivo
        imagen.save(ruta_imagen, format="JPEG", quality=90)

        # Guardar análisis y diagnóstico en MySQL
        conexion = obtener_conexion()
        cursor = conexion.cursor()

        cursor.execute(
            """
            SELECT id_planta
            FROM plantas
            WHERE LOWER(nombre) = LOWER(%s)
            LIMIT 1
            """,
            (nombre_planta,)
        )

        planta = cursor.fetchone()

        if planta is None:
            raise HTTPException(
                status_code=500,
                detail=(
                    f"No existe la planta '{nombre_planta}' "
                    "en la tabla plantas."
                )
            )

        id_planta = planta[0]

        # Guardar resultado del análisis
        cursor.execute(
            """
            INSERT INTO analisis
                (id_usuario, id_planta, imagen, resultado, confianza)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (
                id_usuario,
                id_planta,
                f"uploads/analisis/{nombre_archivo}",
                clase,
                confianza
            )
        )

        id_analisis = cursor.lastrowid

        # Guardar diagnóstico relacionado con el análisis
        cursor.execute(
            """
            INSERT INTO diagnostico
                (id_analisis, estado, enfermedad, recomendacion)
            VALUES (%s, %s, %s, %s)
            """,
            (
                id_analisis,
                estado,
                str(enfermedad)[:50],
                str(recomendacion)[:255]
            )
        )

        # Confirmar ambas inserciones juntas
        conexion.commit()

        return {
            "exito": True,
            "mensaje": "Análisis guardado correctamente.",
            "id_analisis": id_analisis,
            "archivo": file.filename,
            "clase": clase,
            "confianza": confianza,
            "probabilidades": resultado["probabilidades"],
            "informacion": informacion
        }

    except HTTPException:
        if conexion and conexion.is_connected():
            conexion.rollback()
        raise

    except Exception as e:
        if conexion and conexion.is_connected():
            conexion.rollback()

        raise HTTPException(
            status_code=500,
            detail=f"Error al analizar o guardar el resultado: {str(e)}"
        )

    finally:
        if cursor:
            cursor.close()

        if conexion and conexion.is_connected():
            conexion.close()
            
@app.get("/historial")
def obtener_historial(
    usuario=Depends(obtener_usuario_actual)
):
    conexion = None
    cursor = None

    try:
        id_usuario = usuario.get("id_usuario")

        if id_usuario is None:
            raise HTTPException(
                status_code=401,
                detail="No se pudo identificar al usuario."
            )

        conexion = obtener_conexion()
        cursor = conexion.cursor(dictionary=True)

        consulta = """
            SELECT
                a.id_analisis,
                a.resultado,
                a.confianza,
                a.fecha_analisis,
                p.nombre AS cultivo,
                d.estado,
                d.enfermedad,
                d.recomendacion
            FROM analisis a
            LEFT JOIN plantas p
                ON a.id_planta = p.id_planta
            LEFT JOIN diagnostico d
                ON a.id_analisis = d.id_analisis
            WHERE a.id_usuario = %s
            ORDER BY a.fecha_analisis DESC
        """

        cursor.execute(consulta, (id_usuario,))
        registros = cursor.fetchall()

        return {
            "exito": True,
            "historial": [
                {
                    **registro,
                    "fecha_analisis": (
                        registro["fecha_analisis"].isoformat()
                        if registro["fecha_analisis"]
                        else None
                    ),
                    "confianza": float(registro["confianza"])
                    if registro["confianza"] is not None
                    else 0
                }
                for registro in registros
            ]
        }

    except HTTPException:
        raise

    except Exception as error:
        print("Error consultando historial:", error)
        raise HTTPException(
            status_code=500,
            detail="No se pudo consultar el historial."
        )

    finally:
        if cursor:
            cursor.close()
        if conexion and conexion.is_connected():
            conexion.close()
            
# ==========================================
# ADMINISTRADOR: ESTADÍSTICAS GENERALES
# ==========================================

@app.get("/admin/estadisticas")
def estadisticas_admin(
    admin: dict = Depends(requiere_admin)
):
    conexion = None
    cursor = None

    try:
        conexion = obtener_conexion()
        cursor = conexion.cursor(dictionary=True)

        cursor.execute("""
            SELECT COUNT(*) AS total_usuarios
            FROM usuarios
        """)
        total_usuarios = cursor.fetchone()["total_usuarios"]

        cursor.execute("""
            SELECT COUNT(*) AS total_analisis
            FROM analisis
        """)
        total_analisis = cursor.fetchone()["total_analisis"]

        cursor.execute("""
            SELECT COUNT(DISTINCT id_planta) AS cultivos_analizados
            FROM analisis
        """)
        cultivos_analizados = cursor.fetchone()["cultivos_analizados"]

        cursor.execute("""
            SELECT COUNT(*) AS total_alertas
            FROM diagnostico
            WHERE LOWER(estado) IN ('enfermo', 'plaga')
        """)
        total_alertas = cursor.fetchone()["total_alertas"]

        return {
            "exito": True,
            "total_usuarios": total_usuarios,
            "total_analisis": total_analisis,
            "cultivos_analizados": cultivos_analizados,
            "total_alertas": total_alertas
        }

    except Exception as error:
        print("Error en estadísticas administrativas:", error)
        raise HTTPException(
            status_code=500,
            detail="No se pudieron consultar las estadísticas."
        )

    finally:
        if cursor:
            cursor.close()
        if conexion and conexion.is_connected():
            conexion.close()


# ==========================================
# ADMINISTRADOR: LISTA DE USUARIOS
# ==========================================

@app.get("/admin/usuarios")
def listar_usuarios_admin(
    admin: dict = Depends(requiere_admin)
):
    conexion = None
    cursor = None

    try:
        conexion = obtener_conexion()
        cursor = conexion.cursor(dictionary=True)

        cursor.execute("""
            SELECT id_usuario, nombre, correo, rol
            FROM usuarios
            ORDER BY id_usuario DESC
        """)

        usuarios = cursor.fetchall()

        return {
            "exito": True,
            "usuarios": usuarios
        }

    except Exception as error:
        print("Error consultando usuarios:", error)
        raise HTTPException(
            status_code=500,
            detail="No se pudieron consultar los usuarios."
        )

    finally:
        if cursor:
            cursor.close()
        if conexion and conexion.is_connected():
            conexion.close()
