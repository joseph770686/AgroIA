import os
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr, Field
from pwdlib import PasswordHash
from jose import jwt
from mysql.connector import IntegrityError
from dotenv import load_dotenv
import logging

from backend.database.connection import obtener_conexion

load_dotenv()

router = APIRouter(prefix="/auth", tags=["Autenticación"])
password_hash = PasswordHash.recommended()

SECRET_KEY = os.getenv("AGROVISION_SECRET_KEY")
ALGORITHM = "HS256"


def crear_token(usuario_id: int, correo: str):
    if not SECRET_KEY or SECRET_KEY.startswith("CAMBIA_"):
        raise HTTPException(
            status_code=500,
            detail="Configurá AGROVISION_SECRET_KEY en el archivo .env"
        )

    expiracion = datetime.now(timezone.utc) + timedelta(hours=8)

    return jwt.encode(
        {
            "sub": str(usuario_id),
            "correo": correo,
            "exp": expiracion
        },
        SECRET_KEY,
        algorithm=ALGORITHM
    )


class Registro(BaseModel):
    nombre: str = Field(min_length=2, max_length=50)
    correo: EmailStr
    contrasena: str = Field(min_length=8, max_length=128)


class Login(BaseModel):
    correo: EmailStr
    contrasena: str = Field(min_length=1, max_length=128)


@router.post("/registro", status_code=201)
def registrar(datos: Registro):
    conexion = None
    cursor = None

    try:
        conexion = obtener_conexion()
        cursor = conexion.cursor()

        cursor.execute(
            """
            INSERT INTO usuarios
                (nombre, correo, rol, contraseña)
            VALUES (%s, %s, %s, %s)
            """,
            (
                datos.nombre.strip(),
                str(datos.correo).lower(),
                "usuario",
                password_hash.hash(datos.contrasena)
            )
        )

        
        conexion.commit()

        usuario_id = cursor.lastrowid
        correo = str(datos.correo).lower()
        nombre = datos.nombre.strip()

        token = crear_token(usuario_id, correo)

        return {
            "mensaje": "Cuenta creada correctamente",
            "access_token": token,
            "token_type": "bearer",
            "usuario": {
                "id_usuario": usuario_id,
                "nombre": nombre,
                "correo": correo,
                "rol": "usuario"
            }
        }


    except IntegrityError:
        if conexion and conexion.is_connected():
            conexion.rollback()

        raise HTTPException(
            status_code=409,
            detail="Ese correo ya está registrado"
        )

    except HTTPException:
        raise

    except Exception as e:
        if conexion and conexion.is_connected():
            conexion.rollback()

        logging.exception("ERROR REAL AL REGISTRAR USUARIO")

        raise HTTPException(
            status_code=500,
            detail=f"Error al registrar: {str(e)}"
        )

    finally:
        if cursor:
            cursor.close()
        if conexion and conexion.is_connected():
            conexion.close()


@router.post("/login")
def iniciar_sesion(datos: Login):
    conexion = None
    cursor = None

    try:
        conexion = obtener_conexion()
        cursor = conexion.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT id_usuario, nombre, correo, contraseña, rol
            FROM usuarios
            WHERE correo = %s
            """,
            (str(datos.correo).lower(),)
        )

        usuario = cursor.fetchone()

        if not usuario or not password_hash.verify(
            datos.contrasena, usuario["contraseña"]
        ):
            raise HTTPException(
                status_code=401,
                detail="Correo o contraseña incorrectos"
            )

        token = crear_token(
            usuario["id_usuario"],
            usuario["correo"]
        )

        return {
            "mensaje": "Inicio de sesión correcto",
            "access_token": token,
            "token_type": "bearer",
            "usuario": {
                "id_usuario": usuario["id_usuario"],
                "nombre": usuario["nombre"],
                "correo": usuario["correo"],
                "rol": usuario["rol"]
            }
        }

    except HTTPException:
        raise

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="No se pudo iniciar sesión. Verificá la conexión con MySQL."
        )

    finally:
        if cursor:
            cursor.close()
        if conexion and conexion.is_connected():
            conexion.close()