from flask import Flask, render_template
from config import Config
from extensions import db, migrate, login_manager
from models import User
from api import api_bp
from errors import errors_bp

# Flask-App initialisieren
app = Flask(__name__)

# Konfiguration aus `config.py` laden
app.config.from_object(Config)

# Flask-Erweiterungen mit der App verknüpfen
db.init_app(app)              # Initialisiert die Datenbankerweiterung
migrate.init_app(app, db)       # Initialisiert die Migrations-Erweiterung (für Datenbankänderungen)
login_manager.init_app(app)     # Initialisiert Flask-Login für Benutzer-Authentifizierung

with app.app_context():
    # Erzeugt alle Datenbanktabellen, falls diese noch nicht existieren
    db.create_all()
    
# Flask-Login Benutzerladefunktion: Diese Funktion wird aufgerufen, um den Benutzer anhand der user_id aus der Datenbank zu laden
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Blueprints importieren (die modularen Teile der Anwendung)
from auth.routes import auth_bp
from calendar_app.routes import calendar_bp

# Blueprints registrieren
app.register_blueprint(auth_bp, url_prefix="/auth")            # Routen für Authentifizierung unter /auth
app.register_blueprint(calendar_bp, url_prefix="/calendar")      # Routen für den Kalender unter /calendar
app.register_blueprint(api_bp)                                   # API-Routen werden ohne URL-Präfix registriert
app.register_blueprint(errors_bp)                                # Fehlerbehandlungsrouten registrieren

# Standardroute: Startseite
@app.route("/")
def index():
    return render_template("index.html")
    
# Flask-App starten (nur wenn dieses Skript direkt ausgeführt wird)
if __name__ == "__main__":
    app.run(debug=True)
