from fastapi import APIRouter

router = APIRouter(prefix="/firmas", tags=["Firmas"])

@router.post("/verificar")
def verificar_firma():
    # Aquí se implementará la verificación de firma
    return {"mensaje": "Verificación en construcción"}
