from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Archivo SQLite
DATABASE_URL = "sqlite:///proyecto.db"

# Motor de conexión
motor = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# Base de modelos
Base = declarative_base()

# Sesión
Sesion = sessionmaker(bind=motor)
