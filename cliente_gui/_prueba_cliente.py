import api_cliente
import json
import zipfile
import os

USUARIO_PRUEBA = "strinng"
PASS_PRUEBA = "123456789B@r"

def crear_zip_falso():
    with zipfile.ZipFile("dummy.zip", "w") as z:
        z.writestr("info.txt", "Este es un archivo de prueba.")
    return "dummy.zip"

def main():
    print("--- INICIANDO PRUEBA DEL CLIENTE API ---")
    
    try:
        print(f"Intentando login como: {USUARIO_PRUEBA}...")
        token = api_cliente.login(USUARIO_PRUEBA, PASS_PRUEBA)
        
        print("\nProbando GET /usuarios (Contactos)...")
        contactos = api_cliente.obtener_contactos(token)
        print(f"Contactos obtenidos. Se encontraron {len(contactos)} usuarios.")
        print(json.dumps(contactos, indent=2))

        print("\nProbando POST /documentos/subir...")
        
        ruta_zip = crear_zip_falso()
        
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
        
        print("Documento subido exitosamente.")
        print(json.dumps(resultado_subida, indent=2))

    except Exception as e:
        print(f"\nERROR EN LA PRUEBA:\n{e}")
    finally:
        if os.path.exists("dummy.zip"):
            os.remove("dummy.zip")

if __name__ == "__main__":
    main()
