# descifrar.py
# Desempaqueta ZIP, busca wrapped_key por UUID (desde usuarios.json), desenwrap con clave privada,
# descifra data.enc y sig.enc usando DEK, verifica firma con clave pública del autor.

import os, json, base64, zipfile
from getpass import getpass
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding as asympadding
from cryptography.hazmat.primitives import hashes
from firmas import verify_signature_bytes

USERS_FILE = "usuarios.json"

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

def find_user_by_uuid(uid):
    users = load_users()
    for u in users["users"]:
        if u["uuid"] == uid:
            return u
    return None

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

def main():
    print("=== DESCIFRAR Y VERIFICAR SIGNATURE ===")
    # zip path
    while True:
        zp = input("Ruta al ZIP (_secure.zip): ").strip()
        if os.path.isfile(zp):
            break
        print("ZIP no encontrado.")

    # desempaquetar en memoria
    try:
        with zipfile.ZipFile(zp, "r") as z:
            namelist = z.namelist()
            if "meta.json" not in namelist:
                print("ZIP inválido: falta meta.json")
                return
            meta = json.loads(z.read("meta.json").decode("utf-8"))
            ciphertext = z.read(meta["cipherfile"])
            iv = z.read(meta["ivfile"])
            sig_enc = z.read(meta["sigfile_enc"])
            iv_sig = base64.b64decode(meta["iv_sig"])
    except Exception as e:
        print("Error leyendo ZIP:", e)
        return

    # pedir identificador del receptor (username)
    users = load_users()
    if not users["users"]:
        print("No hay usuarios registrados en usuarios.json")
        return

    while True:
        username = input("Tu nombre de usuario (registrado): ").strip()
        me = find_user_by_username(username)
        if me:
            break
        print("Usuario no registrado.")

    # verificar que mi uuid esté en wrapped_keys
    wrapped_map = meta.get("wrapped_keys", {})
    my_uuid = me["uuid"]
    if my_uuid not in wrapped_map:
        print("No estás autorizado para este documento (tu UUID no está en wrapped_keys).")
        return

    # cargar clave privada local (pedir password)
    priv_path = me.get("private_key")
    if not priv_path or not os.path.isfile(priv_path):
        print("No se encontró la clave privada en la ruta registrada:", priv_path)
        priv_path = input("Introduce ruta a tu clave privada PEM: ").strip()
        if not os.path.isfile(priv_path):
            print("Clave privada no encontrada. Abortando.")
            return

    # pedir contraseña e intentar desenvolver DEK (3 intentos)
    for _ in range(3):
        pw = getpass("Contraseña de tu clave privada: ").encode("utf-8")
        try:
            dek = unwrap_dek(wrapped_map[my_uuid], priv_path, pw)
            break
        except Exception:
            print("Contraseña incorrecta o clave inválida.")
    else:
        print("Demasiados intentos. Abortando.")
        return

    # descifrar documento y firma
    try:
        plaintext = aes_decrypt(dek, iv, ciphertext)
    except Exception as e:
        print("Error descifrando documento:", e)
        return

    try:
        sig = aes_decrypt(dek, iv_sig, sig_enc)
    except Exception as e:
        print("Error descifrando firma cifrada:", e)
        return

    # verificar firma usando public key del autor (buscar en usuarios.json)
    author_uuid = meta.get("author_uuid")
    author = find_user_by_uuid(author_uuid)
    if not author:
        print("Autor no registrado localmente. Necesitas su clave pública (PEM).")
        pub_path = input("Ruta a la clave pública del autor: ").strip()
        if not os.path.isfile(pub_path):
            print("Clave pública no encontrada. No se puede verificar firma.")
            verified = None
        else:
            with open(pub_path, "rb") as f:
                pub_pem = f.read()
            verified = verify_signature_bytes(plaintext, sig, pub_pem)
    else:
        with open(author["public_key"], "rb") as f:
            pub_pem = f.read()
        verified = verify_signature_bytes(plaintext, sig, pub_pem)

    # guardar plaintext en archivo
    original = meta.get("original_filename", "output")
    outname = f"{os.path.splitext(original)[0]}_descifrado{os.path.splitext(original)[1]}"
    with open(outname, "wb") as f:
        f.write(plaintext)

    print("✅ Archivo descifrado:", outname)
    if verified is True:
        print("✅ Firma válida (verificada con la clave pública del autor).")
    elif verified is False:
        print("❌ Firma inválida.")
    else:
        print("⚠️ Firma no verificada (falta clave pública del autor).")

if __name__ == "__main__":
    main()
