import re
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime

class UsuarioBase(BaseModel):
    nombre: str = Field(..., min_length=3)

class UsuarioCrear(BaseModel):
    nombre: str = Field(..., min_length=3)
    contrasena: str = Field(..., min_length=8, max_length=72)
    codigo_invitacion: str

    @field_validator('contrasena')
    @classmethod
    def validar_contrasena_segura(cls, v: str) -> str:
        if not re.search(r'[A-Z]', v):
            raise ValueError('La contraseña debe contener al menos una mayúscula')
        if not re.search(r'[a-z]', v):
            raise ValueError('La contraseña debe contener al menos una minúscula')
        if not re.search(r'[0-9]', v):
            raise ValueError('La contraseña debe contener al menos un número')
        if not re.search(r'[@$!%*?&]', v):
            raise ValueError('La contraseña debe contener al menos un carácter especial (@$!%*?&)')
        return v

class UsuarioVer(BaseModel):
    nombre: str
    uuid: str
    clave_publica: Optional[str] = None
    es_admin: bool

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    uuid: Optional[str] = None

class ClavePublicaUpdate(BaseModel):
    clave_publica: str

class DEKCrear(BaseModel):
    usuario_uuid: str
    dek_cifrada: str

class DocumentoCrear(BaseModel):
    nombre_original: str
    deks_cifradas: List[DEKCrear]

class DocumentoInfo(BaseModel):
    id: int
    nombre_original: str
    creado_en: datetime
    propietario_uuid: str

    class Config:
        from_attributes = True