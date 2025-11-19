from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, LargeBinary, Text, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime

from database import Base 

class Usuario(Base):
    __tablename__ = "usuario"
    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String, unique=True, nullable=False)
    uuid = Column(String, unique=True, nullable=False)
    
    clave_publica = Column(Text, nullable=True)
    
    hash_contrasena = Column(String, nullable=False)

    es_admin = Column(Boolean, default=False)

    documentos = relationship("Documento", back_populates="propietario", cascade="all, delete-orphan")

class Documento(Base):
    __tablename__ = "documento"
    id = Column(Integer, primary_key=True, autoincrement=True)
    propietario_id = Column(Integer, ForeignKey("usuario.id"), nullable=False)
    nombre_archivo = Column(String, nullable=False)
    
    zip_bytes = Column(LargeBinary, nullable=False)
    
    creado_en = Column(DateTime, default=datetime.utcnow)
    propietario = relationship("Usuario", back_populates="documentos")
    deks = relationship("DEK", back_populates="documento", cascade="all, delete")

class DEK(Base):
    __tablename__ = "dek"
    id = Column(Integer, primary_key=True, autoincrement=True)
    documento_id = Column(Integer, ForeignKey("documento.id"), nullable=False)
    usuario_uuid = Column(String, nullable=False)
    
    dek_cifrada = Column(Text, nullable=False) 
    
    documento = relationship("Documento", back_populates="deks")