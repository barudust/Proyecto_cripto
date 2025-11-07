# Aquí irán funciones para validar formatos, extensiones, etc.
def validar_uuid(uuid_str: str) -> bool:
    import uuid
    try:
        uuid.UUID(uuid_str)
        return True
    except ValueError:
        return False
