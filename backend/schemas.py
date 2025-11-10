import re # Importamos la librería de Expresiones Regulares
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime
# --- Schemas para Usuario ---

class UsuarioBase(BaseModel):
    # Aplicamos la validación de >3 caracteres aquí
    nombre: str = Field(..., min_length=3) 

class UsuarioCrear(BaseModel):
    nombre: str = Field(..., min_length=3)
    
    # Aplicamos la validación de contraseña aquí
    contrasena: str = Field(..., min_length=8, max_length=72)

    # Esta es una validación personalizada para la contraseña
    @field_validator('contrasena')
    @classmethod
    def validar_contrasena_segura(cls, v: str) -> str:
        print("--- EJECUTANDO VALIDACIÓN DE CONTRASEÑA ---") # <--- AÑADE ESTO
        """
        Valida que la contraseña tenga:
        - Al menos 8 caracteres (ya cubierto por min_length=8)
        - Al menos una mayúscula
        - Al menos una minúscula
        - Al menos un número
        - Al menos un carácter especial (@$!%*?&)
        """
        if not re.search(r'[A-Z]', v):
            raise ValueError('La contraseña debe contener al menos una mayúscula')
        if not re.search(r'[a-z]', v):
            raise ValueError('La contraseña debe contener al menos una minúscula')
        if not re.search(r'[0-9]', v):
            raise ValueError('La contraseña debe contener al menos un número')
        if not re.search(r'[@$!%*?&]', v):
            raise ValueError('La contraseña debe contener al menos un carácter especial (@$!%*?&)')
        
        # Si todo está bien, devuelve la contraseña
        return v


class UsuarioVer(BaseModel):
    """
    Datos que la API enviará al cliente al MOSTRAR un usuario.
    (Nunca incluimos la contraseña hasheada).
    """
    nombre: str
    uuid: str
    clave_publica: Optional[str] = None

    # Config para que Pydantic pueda leer desde el modelo de BD
    class Config:
        from_attributes = True  

class Token(BaseModel):
    """Schema para devolver un token JWT al cliente."""
    access_token: str
    token_type: str

class TokenData(BaseModel):
    """Schema para los datos que guardamos DENTRO del token."""
    uuid: Optional[str] = None

class ClavePublicaUpdate(BaseModel):
    """Schema para recibir la clave pública del cliente."""
    clave_publica: str


class DEKCrear(BaseModel):
    """Schema para recibir una DEK cifrada para un usuario."""
    usuario_uuid: str
    dek_cifrada: str # El string en Base64

class DocumentoCrear(BaseModel):
    """Schema principal para los metadatos del documento."""
    nombre_original: str
    deks_cifradas: List[DEKCrear] # Una lista de para quién es

class DocumentoInfo(BaseModel):
    """Schema para MOSTRAR info de un documento (sin el ZIP)."""
    id: int
    nombre_original: str
    creado_en: datetime
    propietario_uuid: str # UUID del autor

    class Config:
        from_attributes = True # El nuevo nombre de orm_mode








