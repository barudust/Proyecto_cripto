import sys
from sqlalchemy.orm import Session
from database import SessionLocal, motor
import modelos, seguridad
import uuid
import getpass 
def crear_super_admin():
    db = SessionLocal()
    
    print("--- CREACIÓN DE SUPER ADMIN (CLI) ---")
    nombre = input("Nombre de usuario admin: ")
    
    # Verificar si existe
    existe = db.query(modelos.Usuario).filter(modelos.Usuario.nombre == nombre).first()
    if existe:
        print("Error: Ese usuario ya existe.")
        return

    pass1 = getpass.getpass("Contraseña: ")
    pass2 = getpass.getpass("Repetir Contraseña: ")
    
    if pass1 != pass2:
        print("Las contraseñas no coinciden.")
        return


    nuevo_uuid = str(uuid.uuid4())
    hash_pw = seguridad.obtener_hash_contrasena(pass1)
    
    admin = modelos.Usuario(
        nombre=nombre,
        hash_contrasena=hash_pw,
        uuid=nuevo_uuid,
        es_admin=True 
    )
    
    db.add(admin)
    db.commit()
    print(f"Administrador '{nombre}' creado con éxito")
    db.close()

if __name__ == "__main__":
    crear_super_admin()