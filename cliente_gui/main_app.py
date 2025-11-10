# (Esto iría en tu futuro archivo main_app.py)

import api_cliente

try:
    # 1. Registrar un usuario
    nuevo_usuario = api_cliente.registrar_usuario("papu", "MiClaveSegura123@")
    print("¡Usuario registrado!", nuevo_usuario["uuid"])

    # 2. Iniciar sesión con ese usuario
    token = api_cliente.login("papu", "MiClaveSegura123@")
    print("¡Login exitoso! Token:", token)

except Exception as e:
    print(f"Ocurrió un error: {e}")