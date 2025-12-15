import os, json, base64, zipfile
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes as _hashes
from cryptography.hazmat.primitives.asymmetric import padding as asympadding

# --- FUNCIONES AUXILIARES ---
def hex_str(data: bytes, max_len=32) -> str:
    h = data.hex().upper()
    if len(h) > max_len:
        return h[:max_len] + "..."
    return h

def sign_plaintext(plaintext: bytes, priv_pem_path: str, password: bytes) -> bytes:
    with open(priv_pem_path, "rb") as f:
        priv = serialization.load_pem_private_key(f.read(), password=password)
    sig = priv.sign(
        plaintext,
        asympadding.PSS(
            mgf=asympadding.MGF1(_hashes.SHA256()),
            salt_length=asympadding.PSS.MAX_LENGTH
        ),
        _hashes.SHA256()
    )
    return sig

def aes_encrypt(dek: bytes, data: bytes):
    aes = AESGCM(dek)
    iv = os.urandom(12)
    ct = aes.encrypt(iv, data, None)
    return ct, iv

def wrap_dek(dek: bytes, public_pem_texto: str):
    pub = serialization.load_pem_public_key(public_pem_texto.encode("utf-8"))
    wrapped = pub.encrypt(
        dek,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    return wrapped

def crear_paquete_cifrado(
    ruta_archivo_original: str,
    ruta_clave_privada_autor: str,
    password_clave_privada: str,
    uuid_autor: str,
    receptores: list,
    log_callback=None
) -> (str, dict):

    if log_callback: log_callback(f"--- INICIANDO PROCESO DE CIFRADO HÍBRIDO ---", "CRYPTO_START")

    # 1. LEER ARCHIVO
    with open(ruta_archivo_original, "rb") as f:
        plaintext = f.read()
    if log_callback: log_callback(f"Archivo leído: {os.path.basename(ruta_archivo_original)}", "IO")

    # 2. FIRMAR DOCUMENTO (RSA-PSS) - SIN CIFRAR
    if log_callback: log_callback("Generando Firma Digital (Visible en Base64)...", "SIGN")
    try:
        sig = sign_plaintext(
            plaintext,
            ruta_clave_privada_autor,
            password_clave_privada.encode("utf-8")
        )
        # Convertimos la firma RAW a Base64 para que sea legible en el JSON
        firma_visible_b64 = base64.b64encode(sig).decode("ascii")
        
        if log_callback: log_callback(f"Firma B64 generada: {firma_visible_b64[:30]}...", "SIGN_OK")
    except Exception as e:
        raise Exception(f"Error en firma: {e}")

    # 3. GENERAR LLAVE SIMÉTRICA (AES-256)
    dek = AESGCM.generate_key(bit_length=256)
    if log_callback: log_callback(f"Llave Simétrica generada: {hex_str(dek)}", "AES_KEY")

    # 4. CIFRADO SIMÉTRICO (AES-GCM) SOLO DEL CONTENIDO
    if log_callback: log_callback("Cifrando contenido del archivo...", "AES_ENC")
    ciphertext, iv = aes_encrypt(dek, plaintext)
    
    # 5. ENCAPSULAMIENTO DE LLAVES (RSA-OAEP)
    deks_cifradas_api = []
    wrapped_keys_map = {}

    for receptor in receptores:
        wrapped = wrap_dek(dek, receptor["clave_publica"])
        wrapped_b64 = base64.b64encode(wrapped).decode("ascii")
        deks_cifradas_api.append({
            "usuario_uuid": receptor["uuid"],
            "dek_cifrada": wrapped_b64
        })
        wrapped_keys_map[receptor["uuid"]] = wrapped_b64

    # 6. EMPAQUETADO
    f_blob = "data.bin"
    f_iv_cont = "data.iv"
    f_meta = "meta.json"

    meta_zip = {
        "recurso_id": os.path.basename(ruta_archivo_original),
        "cifrado": f_blob,        # <--- CAMBIO: Ahora se llama "cifrado"
        "iv_contenido": f_iv_cont,
        "firma_b64": firma_visible_b64, # <--- CAMBIO: Firma visible (texto), no archivo cifrado
        "propietario_uuid": uuid_autor,
        "almacen_llaves": wrapped_keys_map
    }

    metadata_api = {
        "nombre_original": os.path.basename(ruta_archivo_original),
        "deks_cifradas": deks_cifradas_api
    }

    base = os.path.splitext(os.path.basename(ruta_archivo_original))[0]
    out_zip = f"{base}_temp_secure.zip"

    # Escribir archivos físicos
    with open(f_blob, "wb") as f: f.write(ciphertext)
    with open(f_iv_cont, "wb") as f: f.write(iv)
    with open(f_meta, "w", encoding="utf-8") as f: json.dump(meta_zip, f, indent=2)

    try:
        with zipfile.ZipFile(out_zip, "w", compression=zipfile.ZIP_DEFLATED) as z:
            z.write(f_blob)
            z.write(f_iv_cont)
            z.write(f_meta) # Nota: Ya no metemos sig.enc, porque está en el meta.json
    finally:
        for t in (f_blob, f_iv_cont, f_meta):
            if os.path.exists(t):
                os.remove(t)
    
    if log_callback: log_callback(f"Paquete generado exitosamente.", "DONE")

    return out_zip, metadata_api