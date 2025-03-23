from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager

# Erstellen einer SQLAlchemy-Instanz für die Datenbankinteraktion
db = SQLAlchemy()

# Erstellen einer Migrate-Instanz zur Verwaltung von Datenbankmigrationen
migrate = Migrate()

# Erstellen einer LoginManager-Instanz für die Benutzer-Authentifizierung
login_manager = LoginManager()
# Legt fest, dass bei nicht authentifizierten Benutzern die Route "auth.login" aufgerufen wird
login_manager.login_view = "auth.login"
