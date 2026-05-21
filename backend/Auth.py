"""
backend/Auth.py
Gestion de la logique d'authentification 
"""

from typing import Tuple

from db.users import get_user_by_username, verify_password, create_user, username_exists
from db.joueurs import create_joueur
from db.permissions import get_user_permissions
from sessionUser import SessionUser

from backend.notifications import notifier


class Auth:
    """Gestion de l'authentification des utilisateurs."""
    @staticmethod
    def login(username: str, password: str) -> Tuple[bool, str]:
        """
        Vérifie les identifiants de l'utilisateur.
        Retourne un tuple (success: bool, error: str).
        """
        if not username or not password:
            return False, "Tous les champs sont obligatoires."

        try:
            user = get_user_by_username(username)

            if user and verify_password(password, user[2]):
                perms = get_user_permissions(user[0])
                SessionUser.login(user, perms)
                return True, ""
            else:
                return False, "Identifiants incorrects."

        except Exception as e:
            print(f"[AUTH] Login error: {e}")
            return False, "Erreur de connexion à la base de données."

    @staticmethod
    def register(username: str, password: str, password_confirm: str) -> Tuple[bool, str]:
        """
        Enregistre un nouvel utilisateur.
        Retourne un tuple (success: bool, error: str).
        """
        if not username or not password or not password_confirm:
            return False, "Tous les champs sont obligatoires."
        if password != password_confirm:
            return False, "Les mots de passe ne correspondent pas."

        try:
            if username_exists(username):
                return False, "Ce nom d'utilisateur est déjà pris."
            else:
                create_user(username, password)  # Cette fonction doit être définie dans db.users
                success = notifier("Inscription", f"Le user \"{username}\" vient d'être créé", "min", ["UserCreate"])
                if not success:
                    print("[WARNING] Erreur lors de l'envois de la notification")
                return True, ""
            
        except Exception as e:
            print(f"[AUTH] Registration error: {e}")
            return False, "Erreur de connexion à la base de données."
        
    @staticmethod
    def addNewPlayer(nom: str, prenom: str) -> Tuple[bool, str]:
        """
        Enregistre un nouveau joueur.
        Retourne un tuple (success: bool, error: str).
        """
        if not nom or not prenom:
            return False, "Tous les champs sont obligatoires."

        try:
            create_joueur(nom, prenom)  # Cette fonction doit être définie dans db.joueurs
            success = notifier("Nouveau joueur", f"Le joueur \"{prenom} {nom}\" vient d'être créé", "min", ["PlayerCreate"])
            if not success:
                print("[WARNING] Erreur lors de l'envois de la notification")
            return True, ""
            
        except Exception as e:
            print(f"[AUTH] Player creation error: {e}")
            return False, "Erreur de connexion à la base de données."