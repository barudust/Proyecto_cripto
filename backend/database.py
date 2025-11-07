from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# 1. Esta es la línea clave: se conecta a "proyecto.db"
#    El archivo .db se creará en tu carpeta 'backend/'
SQLALCHEMY_DATABASE_URL = "sqlite:///./proyecto.db"

# 2. Crea el "motor" principal de SQLAlchemy
motor = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False} # Necesario para SQLite
)

# 3. Crea la clase SessionLocal, que usaremos para hablar con la BD
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=motor)

# 4. Crea la 'Base' que nuestros modelos (tablas) heredarán
Base = declarative_base()