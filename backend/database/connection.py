import os
import mysql.connector
from dotenv import load_dotenv

load_dotenv()


def obtener_conexion():
    return mysql.connector.connect(
        host=os.getenv("AGROVISION_DB_HOST", "127.0.0.1"),
        port=int(os.getenv("AGROVISION_DB_PORT", "3306")),
        user=os.getenv("AGROVISION_DB_USER", "root"),
        password=os.getenv("AGROVISION_DB_PASSWORD", "0000"),
        database=os.getenv("AGROVISION_DB_NAME", "Agro"),
        charset="utf8mb4"
    )