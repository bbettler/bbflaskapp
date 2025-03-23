from datetime import datetime, timedelta  # Importiert Datums- und Zeitfunktionen
from extensions import db, login_manager  # Importiert die Datenbankinstanz und den Login-Manager
import base64  # Zum Kodieren von Binärdaten (für Token)
from flask_login import UserMixin  # Mixin, das Standard-Implementierungen für Flask-Login bereitstellt
import os  # Zum Arbeiten mit Betriebssystemfunktionen (z.B. Zufallsdaten)
from werkzeug.security import check_password_hash, generate_password_hash  # Funktionen zum Erzeugen und Prüfen von Passwort-Hashes

# Definition einer Hilfstabelle für die Viele-zu-Viele-Beziehung zwischen Events und Teilnehmern (User)
event_participants = db.Table(
    "event_participants",
    db.Column("event_id", db.Integer, db.ForeignKey("events.id"), primary_key=True),
    db.Column("user_id", db.Integer, db.ForeignKey("users.id"), primary_key=True)  # 🔥 Fix für PostgreSQL (sorgt für korrekte Schlüsseldefinition)
)

class User(UserMixin, db.Model):
    __tablename__ = "users"  # Expliziter Tabellenname für PostgreSQL

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(128), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    company = db.Column(db.String(32))
    job = db.Column(db.String(32))
    phone = db.Column(db.String(32))
    token = db.Column(db.String(32), index=True, unique=True)
    token_expiration = db.Column(db.DateTime)

    def set_password(self, password):
        """
        Setzt das Passwort des Benutzers, indem es in einen sicheren Hash umgewandelt wird.
        """
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """
        Überprüft, ob das übergebene Passwort mit dem gespeicherten Hash übereinstimmt.
        """
        return check_password_hash(self.password_hash, password)

    def get_token(self, expires_in=3600):
        """
        Liefert einen Zugangstoken für den Benutzer, der für die WebAPI genutzt wird.
        Falls bereits ein gültiger Token vorhanden ist (und nicht bald abläuft), wird dieser zurückgegeben.
        Ansonsten wird ein neuer Token generiert, gespeichert und zurückgegeben.
        """
        now = datetime.utcnow()
        if self.token and self.token_expiration > now + timedelta(seconds=60):
            return self.token
        # Generiert einen neuen Token, indem 24 zufällige Bytes base64-kodiert werden
        self.token = base64.b64encode(os.urandom(24)).decode('utf-8')
        self.token_expiration = now + timedelta(seconds=expires_in)
        db.session.add(self)
        return self.token

    def revoke_token(self):
        """
        Widerruft den existierenden Token, indem das Ablaufdatum in die Vergangenheit gesetzt wird.
        """
        self.token_expiration = datetime.utcnow() - timedelta(seconds=1)

    def check_token(token):
        """
        Prüft die Gültigkeit eines übergebenen Tokens.
        Sucht einen Benutzer, dessen Token mit dem übergebenen übereinstimmt und dessen Ablaufzeit in der Zukunft liegt.
        Gibt den Benutzer zurück, wenn alles gültig ist, andernfalls None.
        """
        user = User.query.filter_by(token=token).first()
        if user is None or user.token_expiration < datetime.utcnow():
            return None
        return user

    def __repr__(self):
        # Repräsentation des Benutzerobjekts (hilfreich für Debugging)
        return f'<User {self.username}>'

    def to_dict(self):
        # Konvertiert das Benutzerobjekt in ein Dictionary (z.B. für JSON-Antworten)
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'company': self.company,
            'job': self.job,
            'phone': self.phone
        }

# Flask-Login: Funktion zum Laden eines Benutzers anhand der ID
@login_manager.user_loader
def load_user(user_id):
    """
    Lädt den Benutzer für Flask-Login anhand der Benutzer-ID.
    """
    return User.query.get(int(user_id))

class Event(db.Model):
    __tablename__ = "events"  # Expliziter Tabellenname für die Events

    id = db.Column(db.Integer, primary_key=True)
    
    title = db.Column(db.String(100), nullable=False)  # Titel des Events (Pflichtfeld)
    description = db.Column(db.Text, nullable=True)      # Beschreibung des Events (optional)
    start_time = db.Column(db.DateTime, nullable=False)    # Startzeit des Events
    end_time = db.Column(db.DateTime, nullable=False)      # Endzeit des Events
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)  # Fremdschlüssel zu dem Benutzer, der das Event erstellt hat
    creator = db.relationship("User", backref="created_events")
    # Beziehung zu den Teilnehmern: Viele-zu-Viele-Beziehung über die Hilfstabelle 'event_participants'
    participants = db.relationship(
        "User",
        secondary=event_participants,
        backref=db.backref("attending_events", lazy="dynamic")
    )

    def to_dict(self):
        """Konvertiert das Event-Objekt in ein Dictionary für die API."""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "start_time": self.start_time.strftime("%Y-%m-%d %H:%M:%S"),
            "end_time": self.end_time.strftime("%Y-%m-%d %H:%M:%S"),
            "user_id": self.user_id,
            # Erzeugt eine Liste der Benutzernamen aller Teilnehmer des Events
            "participants": [user.username for user in self.participants]
        }

    def __repr__(self):
        # Repräsentation des Eventobjekts (hilfreich für Debugging)
        return f"<Event {self.title}>"
