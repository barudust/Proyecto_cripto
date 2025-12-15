import json, base64, zipfile, io
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding as asympadding
from cryptography.hazmat.primitives import hashes

def aes_decrypt(dek: bytes, iv: bytes, ciphertext: bytes):
    aes = AESGCM(dek)
    return aes.decrypt(iv, ciphertext, associated_data=None)

def unwrap_dek(wrapped_b64: str, priv_pem_path: str, password: bytes):
    wrapped = base64.b64decode(wrapped_b64)
    with open(priv_pem_path, "rb") as f:
        priv = serialization.load_pem_private_key(f.read(), password=password)
    dek = priv.decrypt(
        wrapped,
        asympadding.OAEP(mgf=asympadding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None)
    )
    return dek

def descifrar_contenido(
    zip_bytes: bytes,
    mi_uuid: str,
    ruta_clave_privada: str,
    password_clave_privada: str
) -> (bytes, bytes, str):
    try:
        with zipfile.ZipFile(io.BytesIO(zip_bytes), "r") as z:
            meta = json.loads(z.read("meta.json").decode("utf-8"))
            
            # 1. Leer contenido cifrado con el nuevo nombre
            ciphertext = z.read(meta["cifrado"]) 
            iv = z.read(meta["iv_contenido"])
            
            # 2. Leer firma directamente del JSON (Base64 -> Bytes)
            firma_b64 = meta["firma_b64"]
            firma_bytes = base64.b64decode(firma_b64)
            
            author_uuid = meta["propietario_uuid"]
            wrapped_map = meta.get("almacen_llaves", {})
            
    except Exception as e:
        raise Exception(f"Error estructura ZIP: {e}")

    if mi_uuid not in wrapped_map:
        raise Exception("Acceso Denegado: No tienes llave para este archivo.")

    try:
        dek = unwrap_dek(wrapped_map[mi_uuid], ruta_clave_privada, password_clave_privada.encode('utf-8'))
    except Exception as e:
        raise Exception(f"Error desencapsulando llave (RSA): {e}")

    try:
        # Solo desciframos el contenido, la firma ya viene lista
        plaintext = aes_decrypt(dek, iv, ciphertext)
    except Exception as e:
        raise Exception(f"Error descifrando contenido (AES): {e}")

    return plaintext, firma_bytes, author_uuid

def verificar_firma(plaintext: bytes, signature: bytes, public_key_pem: str) -> bool:
    try:
        pub = serialization.load_pem_public_key(public_key_pem.encode('utf-8'))
        pub.verify(
            signature,
            plaintext,
            asympadding.PSS(mgf=asympadding.MGF1(hashes.SHA256()), salt_length=asympadding.PSS.MAX_LENGTH),
            hashes.SHA256()
        )
        return True
    except Exception:
        return False