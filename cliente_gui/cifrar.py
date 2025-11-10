# cifrar.py
# Firma el plaintext con la clave privada del autor; cifra plaintext con DEK (AES-GCM);
# cifra la firma con la MISMA DEK (IV distinto); envuelve DEK para cada receptor (por UUID);
# crea meta.json y empaqueta todo en ZIP: data.enc, data.iv, sig.enc, meta.json

import os, json, base64, zipfile
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes as _hashes
from getpass import getpass
from firmas import verify_signature_bytes  # optional use
from cryptography.hazmat.primitives.asymmetric import padding as asympadding

USERS_FILE = "usuarios.json"

def sanitize(name: str) -> str:
    return "_".join(name.strip().split())

def load_users():
    if not os.path.isfile(USERS_FILE):
        return {"users": []}
    with open(USERS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def find_user_by_username(username):
    users = load_users()
    for u in users["users"]:
        if u["username"] == username:
            return u
    return None

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

def wrap_dek(dek: bytes, public_pem_path: str):
    with open(public_pem_path, "rb") as f:
        pub = serialization.load_pem_public_key(f.read())
    wrapped = pub.encrypt(
        dek,
        padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None)
    )
    return wrapped

def main():
    print("=== CIFRAR Y EMPAQUETAR DOCUMENTO (ZIP) ===")
    # archivo a cifrar
    while True:
        in_path = input("Ruta del archivo a cifrar: ").strip()
        if os.path.isfile(in_path):
            break
        print("Archivo no encontrado. Intenta de nuevo.")

    base = sanitize(os.path.splitext(os.path.basename(in_path))[0])
    out_zip = f"{base}_secure.zip"

    # autor (quien firma)
    users = load_users()
    if not users["users"]:
        print("No hay usuarios registrados. Registra al menos uno primero.")
        return

    # elegir autor por username
    while True:
        author = input("Nombre de usuario del autor (quien firma): ").strip()
        au = find_user_by_username(author)
        if au:
            break
        print("Autor no encontrado. Revisa usuarios.json o registra.")

    # pedir password para la clave privada del autor
    pw = getpass("Contraseña de la clave privada del autor: ").encode("utf-8")

    # pedir receptores (por username) - varios
    recs = []
    while True:
        try:
            n = int(input("Número de receptores autorizados: ").strip())
            if n > 0:
                break
            print("Debe ser >=1")
        except ValueError:
            print("Ingresa un número válido.")
    for i in range(n):
        while True:
            r = input(f"Username del receptor #{i+1}: ").strip()
            ru = find_user_by_username(r)
            if ru:
                recs.append(ru)
                break
            print("Usuario no encontrado. Revisa usuarios.json.")

    # leer plaintext
    with open(in_path, "rb") as f:
        plaintext = f.read()

    # 1) firmar plaintext con clave privada del autor
    try:
        sig = sign_plaintext(plaintext, au["private_key"], pw)
    except Exception as e:
        print("Error firmando plaintext:", e)
        return

    # 2) generar DEK y cifrar plaintext
    dek = AESGCM.generate_key(bit_length=256)
    ciphertext, iv = aes_encrypt(dek, plaintext)

    # 3) cifrar la firma con la MISMA DEK (nuevo IV)
    sig_enc, iv_sig = aes_encrypt(dek, sig)

    # 4) envolver DEK para cada receptor -> wrapped_keys map uuid -> base64
    wrapped_map = {}
    for ru in recs:
        wrapped = wrap_dek(dek, ru["public_key"])
        wrapped_map[ru["uuid"]] = base64.b64encode(wrapped).decode("ascii")

    # 5) metadata
    meta = {
        "original_filename": os.path.basename(in_path),
        "cipherfile": "data.enc",
        "ivfile": "data.iv",
        "sigfile_enc": "sig.enc",
        "iv_sig": base64.b64encode(iv_sig).decode("ascii"),
        "author_uuid": au["uuid"],
        "wrapped_keys": wrapped_map
    }

    # 6) escribir temporales y zip
    with open("data.enc", "wb") as f: f.write(ciphertext)
    with open("data.iv", "wb") as f: f.write(iv)
    with open("sig.enc", "wb") as f: f.write(sig_enc)
    with open("meta.json", "w", encoding="utf-8") as f: json.dump(meta, f, indent=2)

    try:
        with zipfile.ZipFile(out_zip, "w", compression=zipfile.ZIP_DEFLATED) as z:
            z.write("data.enc")
            z.write("data.iv")
            z.write("sig.enc")
            z.write("meta.json")
    except Exception as e:
        print("Error creando ZIP:", e)
        return
    finally:
        # eliminar temporales
        for t in ("data.enc", "data.iv", "sig.enc", "meta.json"):
            if os.path.exists(t):
                os.remove(t)

    print("✅ Empaquetado creado:", out_zip)
    print("Entrega este ZIP a los receptores (o súbelo al servidor).")
