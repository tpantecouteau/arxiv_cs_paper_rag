import traceback
from functools import wraps

from airflow.exceptions import (
    AirflowFailException,  # pyright: ignore[reportMissingImports]
)
from PyPDF2 import PdfReader


def critical_task(func):
    """
    Décorateur qui capture les exceptions dans les tâches critiques
    et lève AirflowFailException pour forcer l'état 'failed'.
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            print(f"🚀 Starting critical task: {func.__name__}")
            result = func(*args, **kwargs)
            print(f"✅ Task succeeded: {func.__name__}")
            return result
        except Exception as e:
            tb = traceback.format_exc()
            print(f"❌ Critical error in {func.__name__}: {e}\n{tb}")
            raise AirflowFailException(f"Task '{func.__name__}' failed: {e}")

    return wrapper


def safe_task(func):
    """Log l’erreur mais n’interrompt pas le DAG complet."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
            print(f"✅ Safe task OK: {func.__name__}")
            return result
        except Exception as e:
            print(f"⚠️ Warning in {func.__name__}: {e}")
            return None

    return wrapper


def is_valid_pdf(file_path):
    """
    Vérifie si un fichier PDF est lisible et non corrompu.
    Retourne True si valide, False sinon.
    """
    try:
        reader = PdfReader(file_path)
        _ = len(reader.pages)  # force la lecture des pages
        return True
    except Exception as e:
        print(f"⚠️ PDF invalide ({file_path}): {e}")
        return False
