# cliente_gui/logica_cifrado.py
import os, json, base64, zipfile
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes as _hashes
from cryptography.hazmat.primitives.asymmetric import padding as asympadding

# --- Funciones de Ayuda (copiadas de tu 'cifrar.py') ---

def sign_plaintext(plaintext: bytes, priv_pem_path: str, password: bytes) -> bytes:
    with open(priv_pem_path, "rb") as f:
        priv = serialization.load_pem_private_key(f.read(), password=password)
    sig = priv.sign(
        plaintext,
        asympadding.PSS(mgf=asympadding.MGF1(_hashes.SHA256()), salt_length=asympadding.PSS.MAX_LENGTH),
        _hashes.SHA256()
    )
    return sig

def aes_encrypt(dek: bytes, data: bytes):
    aes = AESGCM(dek)
    iv = os.urandom(12)
    ct = aes.encrypt(iv, data, associated_data=None)
    return ct, iv

def wrap_dek(dek: bytes, public_pem_texto: str):
    # Carga la clave pública desde el TEXTO (que vino de la API)
    pub = serialization.load_pem_public_key(public_pem_texto.encode('utf-8'))
    wrapped = pub.encrypt(
        dek,
        padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None)
    )
    return wrapped

# --- Función Principal ---

def crear_paquete_cifrado(
    ruta_archivo_original: str,
    ruta_clave_privada_autor: str,
    password_clave_privada: str,
    uuid_autor: str,
    receptores: list  # Lista de dicts ej: [{"uuid": "...", "clave_publica": "..."}]
) -> (str, dict):
    """
    Toma un archivo, lo firma, lo cifra, envuelve la DEK para
    los receptores y empaqueta todo en un ZIP temporal.
    
    Devuelve: (ruta_al_zip_temporal, metadata_para_api)
    """

    # Leer plaintext
    with open(ruta_archivo_original, "rb") as f:
        plaintext = f.read()

    # 1) Firmar plaintext con clave privada del autor
    try:
        sig = sign_plaintext(
            plaintext, 
            ruta_clave_privada_autor, 
            password_clave_privada.encode('utf-8')
        )
    except Exception as e:
        print(f"Error firmando: {e}")
        raise Exception(f"Contraseña de clave privada incorrecta o clave inválida. {e}")

    # 2) Generar DEK y cifrar plaintext
    dek = AESGCM.generate_key(bit_length=256)
    ciphertext, iv = aes_encrypt(dek, plaintext)

    # 3) Cifrar la firma con la MISMA DEK (nuevo IV)
    sig_enc, iv_sig = aes_encrypt(dek, sig)

    # 4) Envolver DEK para cada receptor
    deks_cifradas_api = []
    wrapped_keys_map = {}
    for receptor in receptores:
        wrapped = wrap_dek(dek, receptor["clave_publica"])
        
        # Mapa para la API
        deks_cifradas_api.append({
            "usuario_uuid": receptor["uuid"],
            "dek_cifrada": base64.b64encode(wrapped).decode("ascii")
        })
        wrapped_keys_map[receptor["uuid"]] = base64.b64encode(wrapped).decode("ascii")


    # 5) Metadata para el ZIP
    meta_zip = {
        "original_filename": os.path.basename(ruta_archivo_original),
        "cipherfile": "data.enc",
        "ivfile": "data.iv",
        "sigfile_enc": "sig.enc",
        "iv_sig": base64.b64encode(iv_sig).decode("ascii"),
        "author_uuid": uuid_autor,
        "wrapped_keys": wrapped_keys_map  # <--- ¡AÑADE ESTA LÍNEA!
    }
    
    # 6) Metadata para la API (lo que necesita el endpoint de subida)
    metadata_api = {
        "nombre_original": os.path.basename(ruta_archivo_original),
        "deks_cifradas": deks_cifradas_api
    }

    # 7) Escribir temporales y crear el ZIP
    # (Usamos una carpeta temporal o la misma carpeta)
    base = os.path.splitext(os.path.basename(ruta_archivo_original))[0]
    out_zip = f"{base}_temp_secure.zip"
    
    with open("data.enc", "wb") as f: f.write(ciphertext)
    with open("data.iv", "wb") as f: f.write(iv)
    with open("sig.enc", "wb") as f: f.write(sig_enc)
    with open("meta.json", "w", encoding="utf-8") as f: json.dump(meta_zip, f, indent=2)

    try:
        with zipfile.ZipFile(out_zip, "w", compression=zipfile.ZIP_DEFLATED) as z:
            z.write("data.enc")
            z.write("data.iv")
            z.write("sig.enc")
            z.write("meta.json")
    finally:
        # Limpiar temporales
        for t in ("data.enc", "data.iv", "sig.enc", "meta.json"):
            if os.path.exists(t):
                os.remove(t)

    # Devolvemos la ruta al ZIP que acabamos de crear y la metadata para la API
    return (out_zip, metadata_api)