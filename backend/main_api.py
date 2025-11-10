from fastapi.security import OAuth2PasswordRequestForm
import uuid # Para generar los UUIDs de los usuarios
from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File, Form, Response
from sqlalchemy.orm import Session
import modelos, schemas, seguridad
from database import SessionLocal, motor 
from seguridad import obtener_usuario_actual
from typing import List
import json

modelos.Base.metadata.create_all(bind=motor)

# --- Inicialización de la App ---
app = FastAPI(
    title="API de Documentos Legales Seguros",
    description="Backend para gestionar usuarios y documentos cifrados."
)

# --- Dependencia de Base de Datos ---
def get_db():
    """
    Esta es una 'dependencia' de FastAPI.
    Crea una nueva sesión de BD para cada petición a la API 
    y la cierra cuando termina.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Endpoints de la API ---

@app.get("/")
def leer_raiz():
    """Endpoint de bienvenida para probar que el servidor funciona."""
    return {"mensaje": "Bienvenido a la API de Documentos Seguros"}


@app.post(
    "/usuarios/registrar", 
    response_model=schemas.UsuarioVer, 
    status_code=status.HTTP_201_CREATED,
    summary="Registrar un nuevo usuario"
)
def registrar_usuario(
    usuario: schemas.UsuarioCrear, 
    db: Session = Depends(get_db)
):
    """
    Crea un nuevo usuario en la base de datos.
    - **usuario**: Datos de entrada validados por Pydantic (schemas.UsuarioCrear).
    - **db**: Sesión de la base de datos inyectada por FastAPI.
    """
    
    # 1. Verificar si el nombre de usuario ya existe
    db_usuario = db.query(modelos.Usuario).filter(
        modelos.Usuario.nombre == usuario.nombre
    ).first()
    
    if db_usuario:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El nombre de usuario ya está registrado."
        )

    # 2. Hashear la contraseña (¡NUNCA guardarla en texto plano!)
    print(f"--- REGISTRANDO USUARIO: {usuario.nombre} ---") # <--- AÑADE ESTO
    hash_contrasena = seguridad.obtener_hash_contrasena(usuario.contrasena)

    # 3. Generar un UUID único para el usuario
    nuevo_uuid = str(uuid.uuid4())

    # 4. Crear el nuevo objeto de usuario (para la BD)
    nuevo_usuario_db = modelos.Usuario(
        nombre=usuario.nombre,
        hash_contrasena=hash_contrasena,
        uuid=nuevo_uuid
    )

    # 5. Guardar en la base de datos
    db.add(nuevo_usuario_db)
    db.commit()
    db.refresh(nuevo_usuario_db) # Refresca para obtener el ID de la BD

    # 6. Devolver el usuario creado (Pydantic lo filtrará
    #    usando 'schemas.UsuarioVer', quitando el hash)
    return nuevo_usuario_db

# (En main_api.py)

@app.post(
    "/token", 
    response_model=schemas.Token,
    summary="Iniciar sesión y obtener un Token de Acceso"
)
def login_para_token_acceso(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Recibe un nombre de usuario y contraseña desde un formulario.
    Verifica al usuario y devuelve un Token JWT.
    """
    
    # 1. Buscar el usuario en la BD
    usuario = db.query(modelos.Usuario).filter(
        modelos.Usuario.nombre == form_data.username
    ).first()

    # --- ¡LÓGICA CORREGIDA! ---
    # La dividimos en dos 'if' para evitar el crash
    
    # 2. Primero, verificar si el usuario EXISTE
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nombre de usuario o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    # 3. Segundo, si el usuario existe, VERIFICAR la contraseña
    if not seguridad.verificar_contrasena(
        form_data.password, usuario.hash_contrasena
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nombre de usuario o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    # --- FIN DE LA CORRECCIÓN ---

    # 4. Si todo es correcto, crear el token
    token = seguridad.crear_token_acceso(
        data={"sub": usuario.uuid}
    )

    # 5. Devolver el token
    return {"access_token": token, "token_type": "bearer"}
# (En main_api.py)

# (En main_api.py)

# (En main_api.py)

@app.put(
    "/usuarios/mi-clave-publica",
    response_model=schemas.UsuarioVer,
    summary="Subir/Reemplazar la clave pública del usuario (¡Invalida claves antiguas!)"
)
def subir_clave_publica(
    datos_clave: schemas.ClavePublicaUpdate,
    db: Session = Depends(get_db),
    # Renombraremos esto para que sea más claro
    usuario_de_token: modelos.Usuario = Depends(obtener_usuario_actual)
):
    """
    Permite al usuario (identificado por su token) 
    guardar su clave pública en su perfil.
    """
    
    # --- ¡ESTA ES LA LÍNEA DE LA SOLUCIÓN! ---
    # "Adjunta" el usuario desconectado (del token) a la sesión
    # de base de datos actual ('db').
    usuario_actual = db.merge(usuario_de_token)
    
    # ------------------------------------------------
    
    # 1. Borrar todos los accesos (DEKs) antiguos de este usuario.
    #    (Ahora 'usuario_actual' SÍ pertenece a la sesión 'db')
    db.query(modelos.DEK).filter(
        modelos.DEK.usuario_uuid == usuario_actual.uuid
    ).delete()
    
    # 2. Actualizar el campo de la clave pública
    usuario_actual.clave_publica = datos_clave.clave_publica
    
    # 3. Guardar en la BD
    db.commit()
    
    # 4. 'db.refresh' ahora SÍ funcionará
    db.refresh(usuario_actual)
    
    # 5. Devolver el perfil actualizado
    return usuario_actual

# (En main_api.py)

@app.get(
    "/usuarios",
    response_model=List[schemas.UsuarioVer],
    summary="Obtener una lista de todos los usuarios (contactos)"
)
def obtener_usuarios(
    db: Session = Depends(get_db),
    # ¡Endpoint protegido! Solo un usuario logueado puede ver la lista.
    usuario_actual: modelos.Usuario = Depends(obtener_usuario_actual)
):
    """
    Devuelve una lista de todos los usuarios registrados en el sistema
    para que el cliente pueda elegir receptores.
    """
    usuarios = db.query(modelos.Usuario).all()
    return usuarios

# (En main_api.py)

@app.post(
    "/documentos/subir",
    response_model=schemas.DocumentoInfo,
    status_code=status.HTTP_201_CREATED,
    summary="Subir un nuevo documento cifrado"
)
async def subir_documento(
    # Recibimos los datos como un formulario multi-part:
    
    # 1. El archivo ZIP cifrado
    archivo_zip: UploadFile = File(...),
    
    # 2. Los metadatos (nombre y accesos) como un string de JSON
    metadata_json: str = Form(...), 
    
    db: Session = Depends(get_db),
    usuario_actual: modelos.Usuario = Depends(obtener_usuario_actual)
):
    """
    Sube un nuevo documento.
    - **archivo_zip**: El archivo _secure.zip.
    - **metadata_json**: Un STRING de JSON con el 'nombre_original'
      y la lista de 'deks_cifradas'.
    """
    
    # 1. Leer los bytes del archivo ZIP en memoria
    zip_bytes = await archivo_zip.read()
    
    # 2. Convertir el string de metadata a un objeto Pydantic
    try:
        metadata = schemas.DocumentoCrear.model_validate_json(metadata_json)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Metadata JSON mal formateada.")
    
    # 3. Crear el objeto Documento para la BD
    nuevo_documento = modelos.Documento(
        propietario_id=usuario_actual.id,
        nombre_archivo=metadata.nombre_original,
        zip_bytes=zip_bytes #
    )
    
    db.add(nuevo_documento)
    db.commit()
    db.refresh(nuevo_documento) # Para obtener el nuevo ID
    
    # 4. Crear las entradas de DEK (quién tiene acceso)
    for dek_info in metadata.deks_cifradas:
        nueva_dek = modelos.DEK(
            documento_id=nuevo_documento.id,
            usuario_uuid=dek_info.usuario_uuid,
            dek_cifrada=dek_info.dek_cifrada #
        )
        db.add(nueva_dek)
        
    db.commit()
    
    # 5. Preparamos la respuesta (no incluimos el zip_bytes)
    respuesta = schemas.DocumentoInfo(
        id=nuevo_documento.id,
        nombre_original = nuevo_documento.nombre_archivo,
        creado_en=nuevo_documento.creado_en,
        propietario_uuid=usuario_actual.uuid
    )
    
    return respuesta


# (En main_api.py)

@app.get(
    "/documentos/recibidos",
    response_model=List[schemas.DocumentoInfo],
    summary="Listar documentos a los que tengo acceso"
)
def listar_documentos_recibidos(
    db: Session = Depends(get_db),
    usuario_actual: modelos.Usuario = Depends(obtener_usuario_actual)
):
    """
    Devuelve una lista de todos los documentos a los que el
    usuario actual (identificado por su token) tiene acceso.
    
    Busca en la tabla DEK todos los 'documento_id' asociados
    con el UUID del usuario actual.
    """
    
    # 1. Obtener los IDs de las DEKs a las que el usuario tiene acceso
    #    (Esto es una sub-consulta)
    ids_documentos_accesibles = db.query(modelos.DEK.documento_id).filter(
        modelos.DEK.usuario_uuid == usuario_actual.uuid
    )
    
    # 2. Buscar todos los Documentos que están en esa lista de IDs
    documentos = db.query(modelos.Documento).filter(
        modelos.Documento.id.in_(ids_documentos_accesibles)
    ).all()
    
    # 3. Formatear la respuesta (¡importante!)
    #    Necesitamos buscar el UUID del propietario de CADA documento.
    respuesta = []
    for doc in documentos:
        # doc.propietario es la relación que definimos en modelos.py
        propietario_uuid = doc.propietario.uuid 
        
        info = schemas.DocumentoInfo(
            id=doc.id,
            nombre_original=doc.nombre_archivo,
            creado_en=doc.creado_en,
            propietario_uuid=propietario_uuid
        )
        respuesta.append(info)

    return respuesta


# (En main_api.py)

@app.get(
    "/documentos/descargar/{documento_id}",
    summary="Descargar el ZIP cifrado de un documento"
)
def descargar_documento(
    documento_id: int,
    db: Session = Depends(get_db),
    usuario_actual: modelos.Usuario = Depends(obtener_usuario_actual)
):
    """
    Descarga los bytes crudos del archivo ZIP cifrado.
    
    Verifica dos cosas:
    1. Que el documento exista.
    2. Que el usuario actual tenga una DEK para ese documento.
    """
    
    # 1. Verificar que el usuario tiene acceso
    dek_acceso = db.query(modelos.DEK).filter(
        modelos.DEK.documento_id == documento_id,
        modelos.DEK.usuario_uuid == usuario_actual.uuid
    ).first()
    
    if not dek_acceso:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Documento no encontrado o no tienes acceso."
        )

    # 2. Si tiene acceso, obtener el documento
    documento = db.query(modelos.Documento).filter(
        modelos.Documento.id == documento_id
    ).first()
    
    if not documento:
        # Esto no debería pasar si la DEK existe, pero es una buena guarda
        raise HTTPException(status_code=404, detail="Documento no encontrado.")
        
    # 3. ¡Devolver los bytes del ZIP!
    #    Le decimos a FastAPI que el tipo de medio es "zip"
    return Response(
        content=documento.zip_bytes,
        media_type="application/zip",
        headers={
            "Content-Disposition": f"attachment; filename=secure_document_{documento_id}.zip"
        }
    )






