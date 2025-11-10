# cliente_gui/api_cliente.py
import requests
import json

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