from flask import Blueprint, jsonify, request
from flask_httpauth import HTTPBasicAuth, HTTPTokenAuth
from extensions import db
from models import User, Event
import datetime

# Erstellen eines Blueprints für die API-Routen
api_bp = Blueprint("api", __name__)

# Initialisieren der Basic-Auth und Token-Auth Instanzen
basic_auth = HTTPBasicAuth()
token_auth = HTTPTokenAuth()

# Basic Auth zur Verifikation von Benutzername/Passwort
@basic_auth.verify_password
def verify_password(username_or_email, password):
    """
    Verifiziert Benutzername oder E-Mail und Passwort.
    Sucht den Benutzer anhand des eingegebenen Benutzernamens oder der E-Mail und überprüft das Passwort.
    """
    user = User.query.filter(
        (User.username == username_or_email) | (User.email == username_or_email)
    ).first()
    if user and user.check_password(password):
        return user
    return None

@basic_auth.error_handler
def basic_auth_error(status):
    # Gibt eine JSON-Fehlermeldung zurück, falls die Basic Auth fehlschlägt
    return jsonify({"error": "Invalid credentials"}), status

# Token Auth zur Verifikation von API-Tokens
@token_auth.verify_token
def verify_token(token):
    # Überprüft das Token und gibt den zugehörigen Benutzer zurück, falls das Token gültig ist
    return User.check_token(token) if token else None

@token_auth.error_handler
def token_auth_error(status):
    # Gibt eine JSON-Fehlermeldung zurück, falls die Token Auth fehlschlägt
    return jsonify({"error": "Invalid token"}), status

# Endpoint: Token erstellen
@api_bp.route("/api/tokens", methods=["POST"])
@basic_auth.login_required
def get_token():
    # Erstellt ein API-Token für den authentifizierten Benutzer
    token = basic_auth.current_user().get_token()
    db.session.commit()
    return jsonify({"token": token})

# Endpoint: Token zurückziehen
@api_bp.route("/api/tokens", methods=["DELETE"])
@token_auth.login_required
def revoke_token():
    # Widerruft das API-Token des authentifizierten Benutzers
    token_auth.current_user().revoke_token()
    db.session.commit()
    return "", 204

# Benutzer-Daten abrufen
@api_bp.route("/api/users", methods=["GET"])
@token_auth.login_required
def get_user():
    # Gibt die Benutzerdaten des authentifizierten Benutzers als JSON zurück
    return jsonify(token_auth.current_user().to_dict())

# Neuen Benutzer registrieren
@api_bp.route("/api/users", methods=["POST"])
def create_new_user():
    # Liest JSON-Daten aus der Anfrage, um einen neuen Benutzer zu registrieren
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid data"}), 400

    username = data.get("username")
    email = data.get("email")
    password = data.get("password")
    company = data.get("company")
    job = data.get("job")

    # Überprüft, ob der Benutzername oder die E-Mail bereits existieren
    if User.query.filter_by(username=username).first() or User.query.filter_by(email=email).first():
        return jsonify({"error": "Username or Email already exists"}), 400

    # Erstellt einen neuen Benutzer und speichert ihn in der Datenbank
    user = User(username=username, email=email, company=company, job=job)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return jsonify(user.to_dict()), 201

# Benutzer-Daten aktualisieren
@api_bp.route("/api/users", methods=["PUT"])
@token_auth.login_required
def update_user():
    # Liest JSON-Daten aus der Anfrage, um die Daten des authentifizierten Benutzers zu aktualisieren
    data = request.get_json()
    user = token_auth.current_user()

    # Aktualisiert alle übergebenen Felder, sofern sie existieren
    for key, value in data.items():
        if hasattr(user, key):
            setattr(user, key, value)

    db.session.commit()
    return jsonify(user.to_dict())

# Endpoint zum Löschen des Benutzers
@api_bp.route("/api/users", methods=["DELETE"])
@token_auth.login_required
def delete_user():
    # Löscht den aktuell authentifizierten Benutzer aus der Datenbank
    user = token_auth.current_user()
    
    db.session.delete(user)
    db.session.commit()
    
    return jsonify({"message": "User deleted successfully"}), 200

# Alle Events des Users abrufen
@api_bp.route("/api/events", methods=["GET"])
@token_auth.login_required
def get_events():
    # Ruft alle Events des authentifizierten Benutzers ab und gibt sie als JSON-Liste zurück
    events = Event.query.filter_by(user_id=token_auth.current_user().id).all()
    return jsonify([event.to_dict() for event in events])

# Einzelnes Event abrufen
@api_bp.route("/api/events/<int:event_id>", methods=["GET"])
@token_auth.login_required
def get_event(event_id):
    # Ruft ein einzelnes Event anhand der event_id ab, falls es dem authentifizierten Benutzer gehört
    event = Event.query.filter_by(id=event_id, user_id=token_auth.current_user().id).first()
    if not event:
        return jsonify({"error": "Event not found"}), 404
    return jsonify(event.to_dict())

# Neues Event erstellen
@api_bp.route("/api/events", methods=["POST"])
@token_auth.login_required
def create_event():
    # Liest JSON-Daten aus der Anfrage, um ein neues Event zu erstellen
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid data"}), 400

    title = data.get("title")
    description = data.get("description", "")
    start_time = data.get("start_time")
    end_time = data.get("end_time")

    # Versucht, die übergebenen Zeitangaben in datetime-Objekte umzuwandeln
    try:
        start_time = datetime.datetime.strptime(start_time, "%Y-%m-%dT%H:%M:%S")
        end_time = datetime.datetime.strptime(end_time, "%Y-%m-%dT%H:%M:%S")
    except ValueError:
        return jsonify({"error": "Invalid date format"}), 400

    # Erstellt ein neues Event und speichert es in der Datenbank
    event = Event(
        title=title,
        description=description,
        start_time=start_time,
        end_time=end_time,
        user_id=token_auth.current_user().id
    )
    db.session.add(event)
    db.session.commit()
    return jsonify(event.to_dict()), 201

# Event bearbeiten
@api_bp.route("/api/events/<int:event_id>", methods=["PUT"])
@token_auth.login_required
def update_event(event_id):
    # Sucht ein Event anhand der event_id, das dem authentifizierten Benutzer gehört
    event = Event.query.filter_by(id=event_id, user_id=token_auth.current_user().id).first()
    if not event:
        return jsonify({"error": "Event not found"}), 404

    # Liest JSON-Daten aus der Anfrage, um das Event zu aktualisieren
    data = request.get_json()
    if "title" in data:
        event.title = data["title"]
    if "description" in data:
        event.description = data["description"]
    if "start_time" in data:
        event.start_time = datetime.datetime.strptime(data["start_time"], "%Y-%m-%dT%H:%M:%S")
    if "end_time" in data:
        event.end_time = datetime.datetime.strptime(data["end_time"], "%Y-%m-%dT%H:%M:%S")

    db.session.commit()
    return jsonify(event.to_dict())

# Event löschen
@api_bp.route("/api/events/<int:event_id>", methods=["DELETE"])
@token_auth.login_required
def delete_event(event_id):
    # Sucht ein Event anhand der event_id, das dem authentifizierten Benutzer gehört
    event = Event.query.filter_by(id=event_id, user_id=token_auth.current_user().id).first()
    if not event:
        return jsonify({"error": "Event not found"}), 404

    db.session.delete(event)
    db.session.commit()
    return "", 204
