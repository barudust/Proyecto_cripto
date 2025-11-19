import requests
import json
import os
import sys

def cargar_url_api():
    if getattr(sys, 'frozen', False):
        application_path = os.path.dirname(sys.executable)
    else:
        application_path = os.path.dirname(os.path.abspath(__file__))

    config_path = os.path.join(application_path, 'config.json')

    if os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
                return config.get("api_url", "http://127.0.0.1:8000")
        except Exception:
            return "http://127.0.0.1:8000"
    else:
        url_default = "http://127.0.0.1:8000"
        try:
            with open(config_path, 'w') as f:
                json.dump({"api_url": url_default}, f, indent=4)
        except:
            pass
        return url_default

API_URL = cargar_url_api()

def registrar_usuario(nombre: str, contrasena: str, codigo: str):
    url = f"{API_URL}/usuarios/registrar"
    
    datos = {
        "nombre": nombre,
        "contrasena": contrasena,
        "codigo_invitacion": codigo
    }
    
    try:
        response = requests.post(url, json=datos)
        response.raise_for_status() 
        return response.json() 
    
    except requests.exceptions.HTTPError as err:
        try:
            detalle = err.response.json().get("detail", str(err))
        except:
            detalle = str(err)
        raise Exception(f"Error al registrar: {detalle}")
    except requests.exceptions.RequestException as e:
        raise Exception(f"Error de conexión: {e}")

def login(username: str, password: str) -> str:
    url = f"{API_URL}/token"
    
    datos_formulario = {
        "grant_type": "password",
        "username": username,
        "password": password
    }
    
    try:
        response = requests.post(url, data=datos_formulario)
        response.raise_for_status()
        return response.json()["access_token"]
        
    except requests.exceptions.HTTPError as err:
        if err.response.status_code == 401:
            raise Exception("Usuario o contraseña incorrectos.")
        try:
            detalle = err.response.json().get("detail", str(err))
        except:
            detalle = str(err)
        raise Exception(f"Error de login: {detalle}")
    except requests.exceptions.RequestException as e:
        raise Exception(f"Error de conexión: {e}")

def subir_clave_publica(token: str, clave_publica_pem: str):
    url = f"{API_URL}/usuarios/mi-clave-publica"
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    datos = {
        "clave_publica": clave_publica_pem
    }
    
    try:
        response = requests.put(url, json=datos, headers=headers)
        response.raise_for_status()
        return response.json()
        
    except requests.exceptions.HTTPError as err:
        try:
            detalle = err.response.json().get("detail", str(err))
        except:
            detalle = str(err)
        raise Exception(f"Error al subir la clave: {detalle}")
    except requests.exceptions.RequestException as e:
        raise Exception(f"Error de conexión: {e}")

def obtener_contactos(token: str) -> list:
    url = f"{API_URL}/usuarios"
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
        
    except requests.exceptions.HTTPError as err:
        try:
            detalle = err.response.json().get("detail", str(err))
        except:
            detalle = str(err)
        raise Exception(f"Error al obtener contactos: {detalle}")
    except requests.exceptions.RequestException as e:
        raise Exception(f"Error de conexión: {e}")

def subir_documento_cifrado(token: str, ruta_archivo_zip: str, nombre_original: str, deks_cifradas: list):
    url = f"{API_URL}/documentos/subir"
    headers = {"Authorization": f"Bearer {token}"}
    
    metadata = {
        "nombre_original": nombre_original,
        "deks_cifradas": deks_cifradas
    }
    metadata_json = json.dumps(metadata)
    
    datos_formulario = {
        "metadata_json": metadata_json
    }
    
    try:
        with open(ruta_archivo_zip, "rb") as f_zip:
            archivos_formulario = {
                "archivo_zip": (os.path.basename(ruta_archivo_zip), f_zip, "application/zip")
            }
            
            response = requests.post(
                url, 
                headers=headers, 
                data=datos_formulario, 
                files=archivos_formulario
            )
            
            response.raise_for_status()
            return response.json()

    except requests.exceptions.HTTPError as err:
        try:
            detalle = err.response.json().get("detail", str(err))
        except:
            detalle = str(err)
        raise Exception(f"Error al subir el documento: {detalle}")
    except FileNotFoundError:
        raise Exception(f"Error: No se encontró el archivo ZIP en {ruta_archivo_zip}")
    except requests.exceptions.RequestException as e:
        raise Exception(f"Error de conexión: {e}")

def listar_documentos_recibidos(token: str) -> list:
    url = f"{API_URL}/documentos/recibidos"
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
        
    except requests.exceptions.HTTPError as err:
        try:
            detalle = err.response.json().get("detail", str(err))
        except:
            detalle = str(err)
        raise Exception(f"Error al listar documentos: {detalle}")
    except requests.exceptions.RequestException as e:
        raise Exception(f"Error de conexión: {e}")

def descargar_documento_zip(token: str, documento_id: int) -> bytes:
    url = f"{API_URL}/documentos/descargar/{documento_id}"
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.content
        
    except requests.exceptions.HTTPError as err:
        try:
            detalle = err.response.json().get("detail", str(err))
        except:
            detalle = str(err)
        raise Exception(f"Error al descargar el documento: {detalle}")
    except requests.exceptions.RequestException as e:
        raise Exception(f"Error de conexión: {e}")