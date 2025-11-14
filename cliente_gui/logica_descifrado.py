# cliente_gui/logica_descifrado.py
import os, json, base64, zipfile
from getpass import getpass
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding as asympadding
from cryptography.hazmat.primitives import hashes

# (Puedes importar tu 'firmas.py' si lo tienes en esta carpeta)
# De lo contrario, copiamos la función de verificación aquí:

def verify_signature_bytes(plaintext: bytes, signature: bytes, public_key_pem: bytes) -> bool:
    try:
        pub = serialization.load_pem_public_key(public_key_pem)
        pub.verify(
            signature,
            plaintext,
            asympadding.PSS(mgf=asympadding.MGF1(hashes.SHA256()), salt_length=asympadding.PSS.MAX_LENGTH),
            hashes.SHA256()
        )
        return True
    except Exception:
        return False

# --- Funciones de Ayuda (copiadas de tu 'descifrar.py') ---

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

# --- Función Principal ---

def descifrar_paquete(
    zip_bytes: bytes,
    mi_uuid: str,
    ruta_clave_privada: str,
    password_clave_privada: str,
    clave_publica_autor: str # El PEM del autor, traído de la API
) -> (bytes, bool):
    """
    Toma los bytes de un ZIP, los descifra en memoria usando la clave
    privada, verifica la firma y devuelve el plaintext.
    
    Devuelve: (plaintext_bytes, firma_es_valida)
    """
    
    # 1. Desempaquetar el ZIP en memoria
    import io
    try:
        with zipfile.ZipFile(io.BytesIO(zip_bytes), "r") as z:
            meta = json.loads(z.read("meta.json").decode("utf-8"))
            ciphertext = z.read(meta["cipherfile"])
            iv = z.read(meta["ivfile"])
            sig_enc = z.read(meta["sigfile_enc"])
            iv_sig = base64.b64decode(meta["iv_sig"])
    except Exception as e:
        raise Exception(f"Error leyendo el ZIP: {e}")

    # 2. Encontrar mi DEK cifrada
    #    NOTA: En el modelo Cliente/Servidor, la API (en el endpoint
    #    de descarga) ya debería habernos dado la DEK correcta.
    #    Para este ejemplo, asumimos que el ZIP aún contiene
    #    el 'wrapped_keys_map' (como en tu 'descifrar.py' original).
    
    #    ¡MEJORA DE LÓGICA!
    #    El endpoint de descarga ('/documentos/descargar/{id}')
    #    debería devolvernos el ZIP Y la DEK cifrada que nos 
    #    pertenece.
    
    #    Por ahora, vamos a simplificar y suponer que el `meta.json` 
    #    (del ZIP original 'cifrar.py') contiene el mapa de wrapped_keys.
    #    Si no, tendríamos que modificar `logica_cifrado.py`.
    
    #    *** Esta parte es una 'trampa' de tu diseño original.
    #    Tu 'meta.json' NO guarda el wrapped_map, lo guarda la API.
    #    Vamos a ASUMIR que la API nos da la DEK.
    
    #    *** ¡CAMBIO DE PLAN! ***
    #    Vamos a modificar la API de descarga para que nos dé la DEK.
    #    ¡Espera! Lo haremos después.
    
    #    *** ¡CAMBIO DE PLAN 2! ***
    #    Vamos a modificar `logica_cifrado.py` para que SÍ 
    #    guarde el mapa de 'wrapped_keys' en el 'meta.json' del ZIP.
    #    (Abre 'logica_cifrado.py' y en 'meta_zip' añade:
    #     "wrapped_keys": {r['usuario_uuid']: base64.b64encode(wrap_dek(dek, r["clave_publica"])).decode("ascii") for r in receptores})
    #    ¡Por ahora, asumamos que está ahí!

    wrapped_map = meta.get("wrapped_keys", {})
    if mi_uuid not in wrapped_map:
         raise Exception("Error: Tu UUID no está en el mapa de claves de este documento.")

    # 3. Desenvolver la DEK
    try:
        dek = unwrap_dek(
            wrapped_map[mi_uuid], 
            ruta_clave_privada, 
            password_clave_privada.encode('utf-8')
        )
    except Exception as e:
        raise Exception(f"Contraseña de clave privada incorrecta o clave inválida. {e}")

    # 4. Descifrar documento y firma
    try:
        plaintext = aes_decrypt(dek, iv, ciphertext)
    except Exception as e:
        raise Exception(f"Error descifrando el documento: {e}")
        
    try:
        sig = aes_decrypt(dek, iv_sig, sig_enc)
    except Exception as e:
        raise Exception(f"Error descifrando la firma: {e}")

    # 5. Verificar firma con la clave pública del autor
    verified = verify_signature_bytes(plaintext, sig, clave_publica_autor.encode('utf-8'))

    return (plaintext, verified)