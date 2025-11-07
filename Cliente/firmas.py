# firmas.py
# Funciones para firmar/verificar (verificar se usa en descifrar)
import os
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding

def verify_signature_bytes(plaintext: bytes, signature: bytes, public_key_pem: bytes) -> bool:
    try:
        pub = serialization.load_pem_public_key(public_key_pem)
        pub.verify(
            signature,
            plaintext,
            padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
            hashes.SHA256()
        )
        return True
    except Exception:
        return False
