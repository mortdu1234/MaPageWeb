"""Service de cryptographie du package app."""

import io
import os
import struct

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.config import Config


def _load_public_key():
    with open(Config.RSA_PUBLIC_KEY_PATH, "rb") as f:
        return serialization.load_pem_public_key(f.read())


def _load_private_key():
    with open(Config.RSA_PRIVATE_KEY_PATH, "rb") as f:
        return serialization.load_pem_private_key(f.read(), password=None)


def _rsa_padding():
    return padding.OAEP(
        mgf=padding.MGF1(algorithm=hashes.SHA256()),
        algorithm=hashes.SHA256(),
        label=None,
    )


def encrypt_file(plaintext: bytes, dest_path: str) -> None:
    aes_key = os.urandom(32)
    iv = os.urandom(12)
    ciphertext_and_tag = AESGCM(aes_key).encrypt(iv, plaintext, associated_data=None)
    encrypted_aes_key = _load_public_key().encrypt(aes_key, _rsa_padding())  # type: ignore

    with open(dest_path, "wb") as f:
        f.write(struct.pack(">I", len(encrypted_aes_key)))
        f.write(encrypted_aes_key)
        f.write(iv)
        f.write(ciphertext_and_tag)


def decrypt_file(src_path: str) -> io.BytesIO:
    with open(src_path, "rb") as f:
        key_len = struct.unpack(">I", f.read(4))[0]
        encrypted_aes_key = f.read(key_len)
        aes_key = _load_private_key().decrypt(encrypted_aes_key, _rsa_padding())  # type: ignore
        iv = f.read(12)
        ciphertext_and_tag = f.read()

    plaintext = AESGCM(aes_key).decrypt(iv, ciphertext_and_tag, associated_data=None)
    buf = io.BytesIO(plaintext)
    buf.seek(0)
    return buf
