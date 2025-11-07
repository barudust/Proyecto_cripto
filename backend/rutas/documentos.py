from fastapi import APIRouter, UploadFile, Form

router = APIRouter(prefix="/documentos", tags=["Documentos"])

@router.post("/subir")
async def subir_documento(
    archivo: UploadFile,
    propietario_uuid: str = Form(...),
):
    # Aquí se guardará el ZIP cifrado en la base de datos o servidor
    return {"mensaje": f"Archivo {archivo.filename} recibido correctamente"}
