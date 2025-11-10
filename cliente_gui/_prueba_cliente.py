# cliente_gui/_prueba_cliente.py

import api_cliente
import json       # Para imprimir bonito
import zipfile    # Para crear un ZIP falso para la prueba
import os

# --- CONFIGURA TUS DATOS DE PRUEBA ---
USUARIO_PRUEBA = "strinng" # El usuario que registraste
PASS_PRUEBA = "123456789B@r" # Tu contraseña
# -------------------------------------

def crear_zip_falso():
    """Crea un archivo 'dummy.zip' para usar en la prueba."""
    print("Creando archivo ZIP falso (dummy.zip)...")
    with zipfile.ZipFile("dummy.zip", "w") as z:
        z.writestr("info.txt", "Este es un archivo de prueba.")
    return "dummy.zip"

def main():
    print("--- INICIANDO PRUEBA DEL CLIENTE API ---")
    
    try:
        # 1. Probar el Login
        print(f"Intentando login como: {USUARIO_PRUEBA}...")
        token = api_cliente.login(USUARIO_PRUEBA, PASS_PRUEBA)
        print("✅ ¡Login exitoso! Token obtenido.")
        
        # 2. Probar 'obtener_contactos' (¡LA NUEVA FUNCIÓN!)
        print("\nProbando GET /usuarios (Contactos)...")
        contactos = api_cliente.obtener_contactos(token)
        print(f"✅ ¡Contactos obtenidos! Se encontraron {len(contactos)} usuarios.")
        print(json.dumps(contactos, indent=2))

        # 3. Probar 'subir_documento_cifrado' (¡LA OTRA FUNCIÓN!)
        print("\nProbando POST /documentos/subir...")
        
        # Para probar, necesitamos un ZIP y metadatos falsos
        ruta_zip = crear_zip_falso()
        
        # Usaremos el UUID del primer usuario (tú mismo) como receptor
        if not contactos:
             raise Exception("No hay usuarios para usar como receptor de prueba.")
             
        uuid_receptor = contactos[0]["uuid"]
        
        deks_falsas = [
            {"usuario_uuid": uuid_receptor, "dek_cifrada": "dek-de-prueba-en-base64"}
        ]

        resultado_subida = api_cliente.subir_documento_cifrado(
            token=token,
            ruta_archivo_zip=ruta_zip,
            nombre_original="Prueba_Desde_Cliente.pdf",
            deks_cifradas=deks_falsas
        )
        
        print("✅ ¡Documento subido exitosamente!")
        print(json.dumps(resultado_subida, indent=2))

    except Exception as e:
        print(f"\n❌ ERROR EN LA PRUEBA:\n{e}")
    finally:
        # Limpiar el archivo falso
        if os.path.exists("dummy.zip"):
            os.remove("dummy.zip")

if __name__ == "__main__":
    main()