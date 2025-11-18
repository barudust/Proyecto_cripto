# cliente_gui/logica_descifrado.py
import json, base64, zipfile, io
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding as asympadding
from cryptography.hazmat.primitives import hashes

# --- Funciones Auxiliares ---
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

# --- 1. FUNCIÓN SOLO PARA DESCIFRAR (Devuelve contenido y firma cruda) ---
def descifrar_contenido(
    zip_bytes: bytes,
    mi_uuid: str,
    ruta_clave_privada: str,
    password_clave_privada: str
) -> (bytes, bytes, str):
    """
    Abre el ZIP, encuentra la llave del usuario, descifra el archivo y la firma.
    Devuelve: (plaintext_bytes, firma_bytes, uuid_del_autor)
    """
    try:
        with zipfile.ZipFile(io.BytesIO(zip_bytes), "r") as z:
            meta = json.loads(z.read("meta.json").decode("utf-8"))
            ciphertext = z.read(meta["cipherfile"])
            iv = z.read(meta["ivfile"])
            sig_enc = z.read(meta["sigfile_enc"])
            iv_sig = base64.b64decode(meta["iv_sig"])
            author_uuid = meta["author_uuid"]
            wrapped_map = meta.get("wrapped_keys", {}) #
    except Exception as e:
        raise Exception(f"Error leyendo ZIP: {e}")

    if mi_uuid not in wrapped_map:
         raise Exception("No tienes permiso para abrir este archivo (Tu UUID no está en la lista).")

    # 1. Obtener la DEK
    try:
        dek = unwrap_dek(wrapped_map[mi_uuid], ruta_clave_privada, password_clave_privada.encode('utf-8'))
    except Exception as e:
        raise Exception(f"Error de clave privada/contraseña: {e}")

    # 2. Descifrar contenido y firma
    try:
        plaintext = aes_decrypt(dek, iv, ciphertext)
        firma_bytes = aes_decrypt(dek, iv_sig, sig_enc)
    except Exception as e:
        raise Exception(f"Error al descifrar los datos con la DEK: {e}")

    return plaintext, firma_bytes, author_uuid

# --- 2. FUNCIÓN SOLO PARA VERIFICAR FIRMA ---
def verificar_firma(plaintext: bytes, signature: bytes, public_key_pem: str) -> bool:
    """
    Verifica matemáticamente si la firma corresponde al archivo y al autor.
    """
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