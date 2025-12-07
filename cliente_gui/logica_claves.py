
import os
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization

def generar_par_claves(password: str, carpeta_guardado: str, nombre_usuario: str):
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

    private_bytes = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.BestAvailableEncryption(password.encode("utf-8"))
    )
    
    public_key = private_key.public_key()
    public_bytes = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    
    ruta_privada = os.path.join(carpeta_guardado, f"{nombre_usuario}_private.pem")
    with open(ruta_privada, "wb") as f:
        f.write(private_bytes)
        
    return public_bytes.decode("utf-8"), ruta_privada
