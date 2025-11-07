import re # Importamos la librería de Expresiones Regulares
from pydantic import BaseModel, Field, field_validator
from typing import Optional

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


class UsuarioVer(UsuarioBase):
    """
    Datos que la API enviará al cliente al MOSTRAR un usuario.
    (Nunca incluimos la contraseña hasheada).
    """
    uuid: str
    clave_publica: Optional[str] = None

    # Config para que Pydantic pueda leer desde el modelo de BD
    class Config:
        from_attributes = True  