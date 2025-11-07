from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, LargeBinary, Text
from sqlalchemy.orm import relationship
from datetime import datetime

# Importamos la 'Base' que creamos en database.py
from database import Base 

class Usuario(Base):
    __tablename__ = "usuario"
    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String, unique=True, nullable=False)
    uuid = Column(String, unique=True, nullable=False)
    
    # Usamos Text para claves PEM, que pueden ser largas
    clave_publica = Column(Text, nullable=True)
    
    # 🚨 Importante: Guardamos el HASH, no la contraseña
    hash_contrasena = Column(String, nullable=False)
    
    documentos = relationship("Documento", back_populates="propietario")

class Documento(Base):
    __tablename__ = "documento"
    id = Column(Integer, primary_key=True, autoincrement=True)
    propietario_id = Column(Integer, ForeignKey("usuario.id"), nullable=False)
    nombre_archivo = Column(String, nullable=False)
    
    # Aquí se guardarán los bytes del archivo ZIP
    zip_bytes = Column(LargeBinary, nullable=False)
    
    creado_en = Column(DateTime, default=datetime.utcnow)
    propietario = relationship("Usuario", back_populates="documentos")
    deks = relationship("DEK", back_populates="documento", cascade="all, delete")

class DEK(Base):
    __tablename__ = "dek"
    id = Column(Integer, primary_key=True, autoincrement=True)
    documento_id = Column(Integer, ForeignKey("documento.id"), nullable=False)
    usuario_uuid = Column(String, nullable=False)
    
    # La DEK cifrada (en Base64)
    dek_cifrada = Column(Text, nullable=False) 
    
    documento = relationship("Documento", back_populates="deks")