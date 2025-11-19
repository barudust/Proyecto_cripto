from fastapi.security import OAuth2PasswordRequestForm
import uuid 
from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File, Form, Response
from sqlalchemy.orm import Session
import modelos, schemas, seguridad
from database import SessionLocal, motor 
from seguridad import obtener_usuario_actual
from typing import List
import json

CODIGO_USUARIO = "Abogado2025"
CODIGO_ADMIN = "SocioFundadorVIP"

modelos.Base.metadata.create_all(bind=motor)

app = FastAPI(
    title="API Cripto",
    description="Backend para gestionar usuarios y documentos cifrados."
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
def leer_raiz():
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
    es_admin_nuevo = False
    
    if usuario.codigo_invitacion == CODIGO_ADMIN:
        es_admin_nuevo = True
    elif usuario.codigo_invitacion == CODIGO_USUARIO:
        es_admin_nuevo = False
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Código de invitación inválido."
        )
 
    db_usuario = db.query(modelos.Usuario).filter(
        modelos.Usuario.nombre == usuario.nombre
    ).first()
    
    if db_usuario:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El nombre de usuario ya está registrado."
        )

    print(f"--- REGISTRANDO USUARIO: {usuario.nombre} (Admin: {es_admin_nuevo}) ---") 
    hash_contrasena = seguridad.obtener_hash_contrasena(usuario.contrasena)
    nuevo_uuid = str(uuid.uuid4())

    nuevo_usuario_db = modelos.Usuario(
        nombre=usuario.nombre,
        hash_contrasena=hash_contrasena,
        uuid=nuevo_uuid,
        es_admin=es_admin_nuevo
    )

    db.add(nuevo_usuario_db)
    db.commit()
    db.refresh(nuevo_usuario_db)

    return nuevo_usuario_db

@app.post(
    "/token", 
    response_model=schemas.Token,
    summary="Iniciar sesión y obtener un Token de Acceso"
)
def login_para_token_acceso(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    usuario = db.query(modelos.Usuario).filter(
        modelos.Usuario.nombre == form_data.username
    ).first()

    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nombre de usuario o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    if not seguridad.verificar_contrasena(
        form_data.password, usuario.hash_contrasena
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nombre de usuario o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = seguridad.crear_token_acceso(
        data={"sub": usuario.uuid}
    )

    return {"access_token": token, "token_type": "bearer"}

@app.put(
    "/usuarios/mi-clave-publica",
    response_model=schemas.UsuarioVer,
    summary="Subir/Reemplazar la clave pública (Borra archivos propios y accesos)"
)
def subir_clave_publica(
    datos_clave: schemas.ClavePublicaUpdate,
    db: Session = Depends(get_db),
    usuario_de_token: modelos.Usuario = Depends(obtener_usuario_actual)
):
    usuario_actual = db.merge(usuario_de_token)
    
    print(f"--- REGENERANDO CLAVES PARA: {usuario_actual.nombre} ---")

    # 1. ELIMINAR MIS DOCUMENTOS (Porque mi firma ya no será válida y no podré descifrarlos)
    # Al borrar el documento, la configuración 'cascade' borrará las DEKs de todos los demás.
    num_docs = db.query(modelos.Documento).filter(
        modelos.Documento.propietario_id == usuario_actual.id
    ).delete()
    print(f" -> Eliminados {num_docs} documentos propios.")

    # 2. ELIMINAR MIS ACCESOS A ARCHIVOS DE OTROS (Porque cambié mi llave privada y no podré abrir las DEKs viejas)
    num_deks = db.query(modelos.DEK).filter(
        modelos.DEK.usuario_uuid == usuario_actual.uuid
    ).delete()
    print(f" -> Eliminados {num_deks} accesos a documentos de terceros.")
    
    # 3. Actualizar la clave pública
    usuario_actual.clave_publica = datos_clave.clave_publica
    
    db.commit()
    db.refresh(usuario_actual)
    
    return usuario_actual


@app.get(
    "/usuarios",
    response_model=List[schemas.UsuarioVer],
    summary="Obtener una lista de todos los usuarios"
)
def obtener_usuarios(
    db: Session = Depends(get_db),
    usuario_actual: modelos.Usuario = Depends(obtener_usuario_actual)
):
    usuarios = db.query(modelos.Usuario).all()
    return usuarios

@app.post(
    "/documentos/subir",
    response_model=schemas.DocumentoInfo,
    status_code=status.HTTP_201_CREATED,
    summary="Subir un nuevo documento cifrado"
)
async def subir_documento(
    archivo_zip: UploadFile = File(...),
    metadata_json: str = Form(...), 
    db: Session = Depends(get_db),
    usuario_actual: modelos.Usuario = Depends(obtener_usuario_actual)
):
    zip_bytes = await archivo_zip.read()
    
    try:
        metadata = schemas.DocumentoCrear.model_validate_json(metadata_json)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Metadata JSON mal formateada.")
    
    nuevo_documento = modelos.Documento(
        propietario_id=usuario_actual.id,
        nombre_archivo=metadata.nombre_original,
        zip_bytes=zip_bytes
    )
    
    db.add(nuevo_documento)
    db.commit()
    db.refresh(nuevo_documento) 
    
    for dek_info in metadata.deks_cifradas:
        nueva_dek = modelos.DEK(
            documento_id=nuevo_documento.id,
            usuario_uuid=dek_info.usuario_uuid,
            dek_cifrada=dek_info.dek_cifrada
        )
        db.add(nueva_dek)
        
    db.commit()
    
    respuesta = schemas.DocumentoInfo(
        id=nuevo_documento.id,
        nombre_original = nuevo_documento.nombre_archivo,
        creado_en=nuevo_documento.creado_en,
        propietario_uuid=usuario_actual.uuid
    )
    
    return respuesta

@app.get(
    "/documentos/recibidos",
    response_model=List[schemas.DocumentoInfo],
    summary="Listar documentos a los que tengo acceso"
)
def listar_documentos_recibidos(
    db: Session = Depends(get_db),
    usuario_actual: modelos.Usuario = Depends(obtener_usuario_actual)
):
    documentos = (
        db.query(modelos.Documento)
        .join(modelos.DEK, modelos.Documento.id == modelos.DEK.documento_id)
        .filter(modelos.DEK.usuario_uuid == usuario_actual.uuid)
        .all()
    )

    respuesta = []
    for doc in documentos:
        propietario_uuid = doc.propietario.uuid 
        
        info = schemas.DocumentoInfo(
            id=doc.id,
            nombre_original=doc.nombre_archivo,
            creado_en=doc.creado_en,
            propietario_uuid=propietario_uuid
        )
        respuesta.append(info)

    return respuesta

@app.get(
    "/documentos/descargar/{documento_id}",
    summary="Descargar el ZIP cifrado de un documento"
)
def descargar_documento(
    documento_id: int,
    db: Session = Depends(get_db),
    usuario_actual: modelos.Usuario = Depends(obtener_usuario_actual)
):
    dek_acceso = db.query(modelos.DEK).filter(
        modelos.DEK.documento_id == documento_id,
        modelos.DEK.usuario_uuid == usuario_actual.uuid
    ).first()
    
    if not dek_acceso:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Documento no encontrado o no tienes acceso."
        )

    documento = db.query(modelos.Documento).filter(
        modelos.Documento.id == documento_id
    ).first()
    
    if not documento:
        raise HTTPException(status_code=404, detail="Documento no encontrado.")

    return Response(
        content=documento.zip_bytes,
        media_type="application/zip",
        headers={
            "Content-Disposition": f"attachment; filename=secure_document_{documento_id}.zip"
        }
    )

@app.delete("/admin/usuarios/{usuario_uuid}", status_code=204)
def eliminar_usuario(
    usuario_uuid: str,
    db: Session = Depends(get_db),
    admin_actual: modelos.Usuario = Depends(obtener_usuario_actual)
):
    if not admin_actual.es_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="No eres administrador."
        )
        
    victima = db.query(modelos.Usuario).filter(modelos.Usuario.uuid == usuario_uuid).first()
    if not victima:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")
        
    db.query(modelos.DEK).filter(modelos.DEK.usuario_uuid == usuario_uuid).delete()
    
    db.delete(victima)
    db.commit()
    return