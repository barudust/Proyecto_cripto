import os
from datetime import datetime, timedelta
from typing import Optional

# Importaciones de FastAPI y BD
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import modelos # Importa tus modelos
from database import SessionLocal # Importa la sesión de BD
from passlib.context import CryptContext
from jose import JWTError, jwt
from sqlalchemy.orm import Session # <--- ¡AÑADE ESTA LÍNEA!

# --- 1. Configuración de Hashing ---
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verificar_contrasena(contrasena_plana: str, hash_contrasena: str) -> bool:
    """Comprueba si la contraseña plana coincide con el hash guardado."""
    return pwd_context.verify(contrasena_plana, hash_contrasena)

def obtener_hash_contrasena(contrasena: str) -> str:
    """Genera un hash para una contraseña plana."""
    return pwd_context.hash(contrasena)
 
# --- 2. Configuración de JWT (Token de Sesión) ---
SECRET_KEY = "tu-clave-secreta-aqui-cambiala-por-algo-largo"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60  # El token durará 1 hora

def crear_token_acceso(data: dict, expires_delta: Optional[timedelta] = None):
    """Crea un nuevo token JWT."""
    a_codificar = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    a_codificar.update({"exp": expire})
    token_codificado = jwt.encode(a_codificar, SECRET_KEY, algorithm=ALGORITHM)
    return token_codificado

def verificar_token(token: str) -> Optional[str]:
    """Decodifica un token. Devuelve el 'sub' (UUID del usuario) si es válido."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        sub = payload.get("sub")
        if sub is None:
            return None
        return sub
    except JWTError:
        return None


# --- 3. Dependencias de Autenticación (¡EL ORDEN IMPORTA!) ---

# ¡DEBES DEFINIR 'oauth2_scheme' PRIMERO!
# Esta línea le dice a FastAPI que busque el Token
# en la cabecera "Authorization: Bearer <token>"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def get_db_para_seguridad():
    """Dependencia interna para que esta función acceda a la BD."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ¡Y AHORA SÍ PUEDES USAR 'oauth2_scheme' EN LA FUNCIÓN!
def obtener_usuario_actual(
    token: str = Depends(oauth2_scheme), 
    db: Session = Depends(get_db_para_seguridad)
):
    """
    Dependencia de FastAPI:
    1. Toma el token de la cabecera.
    2. Lo verifica.
    3. Busca al usuario en la BD.
    4. Devuelve el objeto 'usuario' completo.
    """
    credenciales_excepcion = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudieron validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    uuid_usuario = verificar_token(token)
    if uuid_usuario is None:
        raise credenciales_excepcion
        
    usuario = db.query(modelos.Usuario).filter(modelos.Usuario.uuid == uuid_usuario).first()
    if usuario is None:
        raise credenciales_excepcion
    
    return usuario