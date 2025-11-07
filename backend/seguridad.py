from passlib.context import CryptContext

# 1. Define el algoritmo de hashing (bcrypt es el estándar)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verificar_contrasena(contrasena_plana: str, hash_contrasena: str) -> bool:
    """
    Comprueba si la contraseña plana (la que envía el usuario) 
    coincide con el hash guardado en la BD.
    """
    return pwd_context.verify(contrasena_plana, hash_contrasena)

def obtener_hash_contrasena(contrasena: str) -> str:
    """
    Genera un hash para una contraseña plana.
    Esto se usa AL REGISTRAR un usuario.
    """
    return pwd_context.hash(contrasena)