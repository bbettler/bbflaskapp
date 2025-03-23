import os

class Config:
    # Setzt den geheimen Schlüssel für die Anwendung.
    # Er wird entweder aus der Umgebungsvariable "SECRET_KEY" geladen oder als Fallback auf einen Standardwert gesetzt.
    SECRET_KEY = os.environ.get("SECRET_KEY") or "mein_geheimer_schlüssel"

    # Liest die Datenbank-URL aus der Umgebungsvariable "DATABASE_URL".
    # Falls die Variable nicht existiert, wird ein Standardwert (eine PostgreSQL-URL) verwendet.
    DATABASE_URL = os.environ.get("DATABASE_URL", "")

    # Falls Heroku eine falsche URL liefert (mit "postgres://"), wird diese in das korrekte Format "postgresql://"
    # umgewandelt. Dies ist notwendig, da SQLAlchemy das "postgresql://" Schema erwartet.
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

    # Konfiguration der SQLAlchemy-Datenbankverbindung mit der ermittelten DATABASE_URL.
    SQLALCHEMY_DATABASE_URI = DATABASE_URL

    # Deaktiviert die SQLAlchemy-Track-Modifications Funktion, um unnötigen Speicherverbrauch zu vermeiden.
    SQLALCHEMY_TRACK_MODIFICATIONS = False
