
from fastapi import Header, HTTPException, Depends
from jose import jwt, JWTError
import os

from dotenv import load_dotenv
from backend.database.connection import obtener_conexion
from fastapi import Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()
load_dotenv()

SECRET_KEY = os.getenv("AGROVISION_SECRET_KEY")
ALGORITHM = "HS256"


def obtener_usuario_actual(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    authorization = f"Bearer {credentials.credentials}"
    
    print("AUTHORIZATION RECIBIDO:", repr(authorization))
    print("AUTHORIZATION RECIBIDO:", repr(authorization))
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Debes iniciar sesión para continuar."
        )
    

    if not SECRET_KEY or SECRET_KEY.startswith("CAMBIA_"):
        raise HTTPException(
            status_code=500,
            detail="La clave de seguridad no está configurada."
        )

    token = authorization.split(" ", 1)[1]

    try:
        datos = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        usuario_id = int(datos["sub"])

    except (JWTError, KeyError, ValueError, TypeError):
        raise HTTPException(
            status_code=401,
            detail="La sesión no es válida o ha expirado."
        )

    conexion = None
    cursor = None

    try:
        conexion = obtener_conexion()
        cursor = conexion.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT id_usuario, nombre, correo, rol
            FROM usuarios
            WHERE id_usuario = %s
            """,
            (usuario_id,)
        )

        usuario = cursor.fetchone()

        if not usuario:
            raise HTTPException(
                status_code=401,
                detail="El usuario ya no existe."
            )

        return usuario

    except HTTPException:
        raise

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="No se pudo verificar la sesión."
        )

    finally:
        if cursor:
            cursor.close()
        if conexion and conexion.is_connected():
            conexion.close()


def requiere_admin(
    usuario: dict = Depends(obtener_usuario_actual)
):
    if usuario["rol"] != "administrador":
        raise HTTPException(
            status_code=403,
            detail="No tienes permisos de administrador."
        )

    return usuario
