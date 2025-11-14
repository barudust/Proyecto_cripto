# cliente_gui/logica_claves.py
import os
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization

def generar_par_claves(password: str, carpeta_guardado: str, nombre_usuario: str):
    """
    Genera un par de claves RSA 2048, guarda la privada (protegida)
    en la carpeta_guardado y devuelve la pública como texto.
    """
    print("Generando claves RSA (2048 bits)...")
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

    # Convertir clave privada a bytes, protegida con contraseña
    private_bytes = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.BestAvailableEncryption(password.encode("utf-8"))
    )
    
    # Convertir clave pública a bytes (formato PEM)
    public_key = private_key.public_key()
    public_bytes = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    
    # Guardar la clave privada localmente
    ruta_privada = os.path.join(carpeta_guardado, f"{nombre_usuario}_private.pem")
    with open(ruta_privada, "wb") as f:
        f.write(private_bytes)
        
    # Devolver el texto de la clave pública (para subirla al servidor)
    # y la ruta donde se guardó la privada
    return public_bytes.decode('utf-8'), ruta_privada