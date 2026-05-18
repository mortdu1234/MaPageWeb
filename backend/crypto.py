"""
crypto.py
Chiffrement hybride RSA-OAEP + AES-256-GCM.

Principe :
  - Upload   : génère une clé AES aléatoire → chiffre le fichier (AES-GCM)
                → chiffre la clé AES avec la clé publique RSA (OAEP)
  - Download : déchiffre la clé AES avec la clé privée RSA
                → déchiffre le fichier en mémoire

Format du fichier .enc sur disque :
  [ 4 bytes  : longueur de la clé AES chiffrée (big-endian uint32) ]
  [ N bytes  : clé AES chiffrée par RSA-OAEP                       ]
  [ 12 bytes : IV AES-GCM                                           ]
  [ M bytes  : ciphertext + tag GCM (16 bytes en fin)               ]
"""

import io
import os
import struct

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from config import Config


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
    """
    Chiffre `plaintext` et écrit le résultat dans `dest_path`.
    1. Génère une clé AES-256 aléatoire
    2. Chiffre le contenu avec AES-256-GCM
    3. Chiffre la clé AES avec la clé publique RSA (OAEP/SHA-256)
    """
    # 1. Clé AES éphémère + IV
    aes_key = os.urandom(32)
    iv      = os.urandom(12)

    # 2. Chiffrement du contenu
    ciphertext_and_tag = AESGCM(aes_key).encrypt(iv, plaintext, associated_data=None)

    # 3. Chiffrement de la clé AES avec RSA
    encrypted_aes_key = _load_public_key().encrypt(aes_key, _rsa_padding()) # type: ignore

    # Écriture : [4b longueur clé][clé chiffrée][12b IV][ciphertext+tag]
    with open(dest_path, "wb") as f:
        f.write(struct.pack(">I", len(encrypted_aes_key)))
        f.write(encrypted_aes_key)
        f.write(iv)
        f.write(ciphertext_and_tag)


def decrypt_file(src_path: str) -> io.BytesIO:
    """
    Déchiffre le fichier `src_path` en mémoire et retourne un BytesIO
    prêt à être envoyé par Flask (send_file).
    Lève une exception si le fichier est altéré (tag GCM invalide).
    """
    with open(src_path, "rb") as f:
        # Longueur de la clé AES chiffrée
        key_len = struct.unpack(">I", f.read(4))[0]

        # Clé AES chiffrée → déchiffrement RSA
        encrypted_aes_key = f.read(key_len)
        aes_key = _load_private_key().decrypt(encrypted_aes_key, _rsa_padding()) # type: ignore

        # IV + ciphertext
        iv                 = f.read(12)
        ciphertext_and_tag = f.read()

    plaintext = AESGCM(aes_key).decrypt(iv, ciphertext_and_tag, associated_data=None)

    buf = io.BytesIO(plaintext)
    buf.seek(0)
    return buf