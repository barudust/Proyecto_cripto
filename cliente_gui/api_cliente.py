# cliente_gui/api_cliente.py
import requests
import json
import os

# Esta es la dirección de tu "cocina" (el backend)
# Usamos ngrok o la IP del servidor en el futuro
API_URL = "http://127.0.0.1:8000"

def registrar_usuario(nombre: str, contrasena: str):
    """
    Llama al endpoint POST /usuarios/registrar.
    Envía los datos como un JSON.
    """
    url = f"{API_URL}/usuarios/registrar"
    
    # Los datos que el schema 'UsuarioCrear' espera
    datos = {
        "nombre": nombre,
        "contrasena": contrasena
    }
    
    try:
        response = requests.post(url, json=datos)
        
        # Si el servidor responde con un error (4xx o 5xx), 
        # esta línea lanzará una excepción
        response.raise_for_status() 
        
        # Si todo sale bien (201 Created), devuelve el JSON de respuesta
        return response.json() 
    
    except requests.exceptions.HTTPError as err:
        # Intenta obtener el detalle del error de FastAPI (ej. "Usuario ya existe")
        detalle = err.response.json().get("detail", str(err))
        raise Exception(f"Error al registrar: {detalle}")
    except requests.exceptions.RequestException as e:
        # Error de conexión (ej. el servidor está apagado)
        raise Exception(f"Error de conexión: {e}")

def login(username: str, password: str) -> str:
    """
    Llama al endpoint POST /token.
    Envía los datos como Form-Data (no JSON).
    Devuelve solo el access_token si tiene éxito.
    """
    url = f"{API_URL}/token"
    
    # ¡Importante! El endpoint /token espera Form-Data, no JSON
    # como descubrimos.
    datos_formulario = {
        "grant_type": "password",
        "username": username,
        "password": password
    }
    
    try:
        response = requests.post(url, data=datos_formulario)
        response.raise_for_status() # Lanza error si es 401 (no autorizado)
        
        # Si todo sale bien (200 OK), extrae el token y devuélvelo
        return response.json()["access_token"]
        
    except requests.exceptions.HTTPError as err:
        if err.response.status_code == 401:
            raise Exception("Usuario o contraseña incorrectos.")
        detalle = err.response.json().get("detail", str(err))
        raise Exception(f"Error de login: {detalle}")
    except requests.exceptions.RequestException as e:
        raise Exception(f"Error de conexión: {e}")
    
# (En cliente_gui/api_cliente.py)

def subir_clave_publica(token: str, clave_publica_pem: str):
    """
    Llama al endpoint PUT /usuarios/mi-clave-publica.
    Envía el token en la cabecera (Header) para autenticarse.
    Envía la clave pública como un JSON.
    """
    url = f"{API_URL}/usuarios/mi-clave-publica"
    
    # 1. Prepara la cabecera de autenticación
    #    Así es como "probamos" quiénes somos
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    # 2. Prepara los datos a enviar (el schema 'ClavePublicaUpdate')
    datos = {
        "clave_publica": clave_publica_pem
    }
    
    try:
        response = requests.put(url, json=datos, headers=headers)
        response.raise_for_status() # Lanza error si es 401, 404, etc.
        
        # Si todo sale bien (200 OK), devuelve el perfil actualizado
        return response.json()
        
    except requests.exceptions.HTTPError as err:
        detalle = err.response.json().get("detail", str(err))
        raise Exception(f"Error al subir la clave: {detalle}")
    except requests.exceptions.RequestException as e:
        raise Exception(f"Error de conexión: {e}")
    
# (En cliente_gui/api_cliente.py)

def obtener_contactos(token: str) -> list:
    """
    Llama al endpoint GET /usuarios para obtener la lista de usuarios.
    Requiere un token de autenticación.
    """
    url = f"{API_URL}/usuarios"
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status() # Lanza error si no está autorizado
        
        # Devuelve la lista de usuarios (ej. [{'nombre': 'papu', ...}])
        return response.json()
        
    except requests.exceptions.HTTPError as err:
        detalle = err.response.json().get("detail", str(err))
        raise Exception(f"Error al obtener contactos: {detalle}")
    except requests.exceptions.RequestException as e:
        raise Exception(f"Error de conexión: {e}")


def subir_documento_cifrado(
    token: str, 
    ruta_archivo_zip: str, 
    nombre_original: str, 
    deks_cifradas: list
):
    """
    Llama al endpoint POST /documentos/subir.
    Esto envía el archivo ZIP y los metadatos como un 
    formulario 'multipart/form-data'.
    """
    url = f"{API_URL}/documentos/subir"
    headers = {"Authorization": f"Bearer {token}"}
    
    # 1. Prepara los metadatos como un string de JSON
    #    (Esto coincide con el schema 'DocumentoCrear')
    metadata = {
        "nombre_original": nombre_original,
        "deks_cifradas": deks_cifradas
    }
    metadata_json = json.dumps(metadata)
    
    # 2. Prepara el 'payload' del formulario
    datos_formulario = {
        "metadata_json": metadata_json
    }
    
    try:
        # 3. Abre el archivo ZIP en modo 'lectura binaria' ('rb')
        with open(ruta_archivo_zip, "rb") as f_zip:
            
            # 4. Prepara el archivo para la subida
            archivos_formulario = {
                "archivo_zip": (os.path.basename(ruta_archivo_zip), f_zip, "application/zip")
            }
            
            # 5. Envía la petición
            #    'data' se usa para los campos de texto
            #    'files' se usa para los archivos
            response = requests.post(
                url, 
                headers=headers, 
                data=datos_formulario, 
                files=archivos_formulario
            )
            
            response.raise_for_status()
            
            # Devuelve el JSON con la info del documento subido
            return response.json()

    except requests.exceptions.HTTPError as err:
        detalle = err.response.json().get("detail", str(err))
        raise Exception(f"Error al subir el documento: {detalle}")
    except FileNotFoundError:
        raise Exception(f"Error: No se encontró el archivo ZIP en {ruta_archivo_zip}")
    except requests.exceptions.RequestException as e:
        raise Exception(f"Error de conexión: {e}")

# (En cliente_gui/api_cliente.py)

def listar_documentos_recibidos(token: str) -> list:
    """
    Llama al endpoint GET /documentos/recibidos para obtener la
    "bandeja de entrada" de documentos del usuario.
    """
    url = f"{API_URL}/documentos/recibidos"
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        # Devuelve la lista de info de documentos
        return response.json()
        
    except requests.exceptions.HTTPError as err:
        detalle = err.response.json().get("detail", str(err))
        raise Exception(f"Error al listar documentos: {detalle}")
    except requests.exceptions.RequestException as e:
        raise Exception(f"Error de conexión: {e}")


def descargar_documento_zip(token: str, documento_id: int) -> bytes:
    """
    Llama al endpoint GET /documentos/descargar/{documento_id}.
    NO devuelve JSON. Devuelve los BYTES crudos del archivo ZIP.
    """
    url = f"{API_URL}/documentos/descargar/{documento_id}"
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status() # Lanza error si es 404 (sin acceso)
        
        # 'response.content' son los bytes crudos del ZIP
        return response.content
        
    except requests.exceptions.HTTPError as err:
        detalle = err.response.json().get("detail", str(err))
        raise Exception(f"Error al descargar el documento: {detalle}")
    except requests.exceptions.RequestException as e:
        raise Exception(f"Error de conexión: {e}")
    




