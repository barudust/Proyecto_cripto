print("--- [DEBUG] LEYENDO main_api.py (NIVEL SUPERIOR) ---")
import uuid # Para generar los UUIDs de los usuarios
from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session

# Importamos todo desde nuestros archivos locales
import modelos, schemas, seguridad
from database import SessionLocal, motor 

# --- Creación de la Base de Datos ---
# Esta línea le dice a SQLAlchemy que cree TODAS las tablas
# que definimos en 'modelos.py' (si no existen)
# El archivo 'proyecto.db' aparecerá en tu carpeta 'backend/'
modelos.Base.metadata.create_all(bind=motor)

# --- Inicialización de la App ---
app = FastAPI(
    title="API de Documentos Legales Seguros",
    description="Backend para gestionar usuarios y documentos cifrados."
)

# --- Dependencia de Base de Datos ---
def get_db():
    """
    Esta es una 'dependencia' de FastAPI.
    Crea una nueva sesión de BD para cada petición a la API 
    y la cierra cuando termina.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Endpoints de la API ---

@app.get("/")
def leer_raiz():
    """Endpoint de bienvenida para probar que el servidor funciona."""
    return {"mensaje": "Bienvenido a la API de Documentos Seguros"}


@app.post(
    "/usuarios/registrar", 
    response_model=schemas.UsuarioVer, 
    status_code=status.HTTP_201_CREATED,
    summary="Registrar un nuevo usuario"
)
def registrar_usuario(
    usuario: schemas.UsuarioCrear, 
    db: Session = Depends(get_db)
):
    """
    Crea un nuevo usuario en la base de datos.
    - **usuario**: Datos de entrada validados por Pydantic (schemas.UsuarioCrear).
    - **db**: Sesión de la base de datos inyectada por FastAPI.
    """
    
    # 1. Verificar si el nombre de usuario ya existe
    db_usuario = db.query(modelos.Usuario).filter(
        modelos.Usuario.nombre == usuario.nombre
    ).first()
    
    if db_usuario:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El nombre de usuario ya está registrado."
        )

    # 2. Hashear la contraseña (¡NUNCA guardarla en texto plano!)
    print(f"--- REGISTRANDO USUARIO: {usuario.nombre} ---") # <--- AÑADE ESTO
    hash_contrasena = seguridad.obtener_hash_contrasena(usuario.contrasena)

    # 3. Generar un UUID único para el usuario
    nuevo_uuid = str(uuid.uuid4())

    # 4. Crear el nuevo objeto de usuario (para la BD)
    nuevo_usuario_db = modelos.Usuario(
        nombre=usuario.nombre,
        hash_contrasena=hash_contrasena,
        uuid=nuevo_uuid
    )

    # 5. Guardar en la base de datos
    db.add(nuevo_usuario_db)
    db.commit()
    db.refresh(nuevo_usuario_db) # Refresca para obtener el ID de la BD

    # 6. Devolver el usuario creado (Pydantic lo filtrará
    #    usando 'schemas.UsuarioVer', quitando el hash)
    return nuevo_usuario_db