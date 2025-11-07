# claves.py
# Genera par RSA, guarda archivos y registra usuario en usuarios.json con UUID.
import os, json, uuid
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization

USERS_FILE = "usuarios.json"

def sanitize(name: str) -> str:
    return "_".join(name.strip().split())

def load_users():
    if not os.path.isfile(USERS_FILE):
        return {"users": []}
    with open(USERS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_users(data):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def find_user_by_username(username):
    data = load_users()
    for u in data["users"]:
        if u["username"] == username:
            return u
    return None

def find_user_by_uuid(uid):
    data = load_users()
    for u in data["users"]:
        if u["uuid"] == uid:
            return u
    return None

def generate_and_register():
    print("=== Registrar usuario y generar claves RSA ===")
    while True:
        username = input("Nombre de usuario (no vacío): ").strip()
        if username:
            break
        print("Nombre inválido.")
    username_s = sanitize(username)
    users = load_users()
    if find_user_by_username(username_s):
        print("Usuario ya registrado con ese nombre.")
        return

    priv_name = f"{username_s}_private.pem"
    pub_name = f"{username_s}_public.pem"

    # contraseña para proteger la privada
    password = input("Contraseña para proteger la clave privada (no la olvides): ").strip()
    if not password:
        print("Se requiere contraseña.")
        return

    print("Generando claves RSA (2048 bits)...")
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

    # guardar archivos (sobrescribe si ya existen con nombres iguales)
    with open(priv_name, "wb") as f:
        f.write(private_bytes)
    with open(pub_name, "wb") as f:
        f.write(public_bytes)

    # registrar en usuarios.json con UUID
    user_uuid = str(uuid.uuid4())
    users["users"].append({
        "username": username_s,
        "uuid": user_uuid,
        "public_key": os.path.abspath(pub_name),
        "private_key": os.path.abspath(priv_name)  # local reference for testing
    })
    save_users(users)

    print("✅ Usuario registrado.")
    print(" username:", username_s)
    print(" uuid:   ", user_uuid)
    print(" private:", priv_name)
    print(" public: ", pub_name)
    print("Nota: la clave privada está protegida por la contraseña que ingresaste.")
