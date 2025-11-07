from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/usuarios", tags=["Usuarios"])

# Esquemas temporales (luego los conectaremos con la base de datos)
class UsuarioRegistro(BaseModel):
    nombre_usuario: str
    contraseña: str
    clave_publica: str

@router.post("/registro")
def registrar_usuario(datos: UsuarioRegistro):
    # Aquí iría la lógica para guardar el usuario en la base de datos
    return {"mensaje": f"Usuario {datos.nombre_usuario} registrado correctamente"}
