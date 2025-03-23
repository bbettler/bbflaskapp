# Importiere notwendige Module und Klassen zur Erstellung und Validierung von Formularen
from flask_wtf import FlaskForm  # FlaskForm dient als Basis für alle Formular-Klassen in Flask
from wtforms import StringField, PasswordField, SubmitField, EmailField, BooleanField  # Import der Formularfelder
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError, Length, Regexp, Optional  # Import der Validierungsregeln
from flask_login import current_user  # Import zur Abfrage des aktuell eingeloggten Benutzers
from models import User  # Import des User-Modells zur Abfrage der Benutzerdaten aus der Datenbank
from extensions import db  # Import der Datenbankerweiterung für den Datenbankzugriff

# Definiere eine Registrierungsformular-Klasse, die von FlaskForm erbt
class RegistrationForm(FlaskForm):
    # Feld für den Benutzernamen mit einer "Pflichtfeld"-Validierung
    username = StringField('Benutzername', validators=[DataRequired()])
    # Feld für die E-Mail-Adresse mit Pflicht- und E-Mail-Format-Validierung
    email = EmailField('Email', validators=[DataRequired(), Email()])
    # Passwortfeld mit Pflicht- und Längenvalidierung
    password = PasswordField(
        "Passwort",
        validators=[
            DataRequired(),  # Stellt sicher, dass das Feld nicht leer ist
            Length(min=8, max=128, message="Das Passwort muss mindestens 8 Zeichen lang sein.")
        ]
    )
    # Passwort-Bestätigungsfeld mit Pflicht- und Übereinstimmungsvalidierung
    password2 = PasswordField(
        "Passwort wiederholen",
        validators=[
            DataRequired(),  # Stellt sicher, dass das Feld nicht leer ist
            EqualTo("password", message="Passwörter müssen übereinstimmen.")
        ]
    )
    # Feld für die Mobilnummer mit Pflicht- und Regexp-Validierung, die ein bestimmtes Format verlangt
    phone = StringField(
        "Mobilnummer",
        validators=[
            DataRequired(),  # Stellt sicher, dass das Feld nicht leer ist
            Regexp(r"^\+?\d{7,15}$", message="Die Telefonnummer darf nur Zahlen enthalten und zwischen 7-15 Zeichen lang sein.")
        ]
    )
    # Feld für den Firmennamen mit Pflichtfeld-Validierung
    company = StringField('Firma', validators=[DataRequired()])
    # Feld für den Beruf mit Pflichtfeld-Validierung
    job = StringField('Beruf', validators=[DataRequired()])
    # Submit-Button für das Registrierungsformular
    submit = SubmitField('Register')

    # Benutzerdefinierte Validierungsmethode für den Benutzernamen
    def validate_username(self, username):
        # Prüft, ob der eingegebene Benutzername bereits in der Datenbank existiert
        user = db.session.execute(db.select(User).filter_by(username=username.data)).scalar()
        if user is not None:
            raise ValidationError('Please use a different username.')

    # Benutzerdefinierte Validierungsmethode für die E-Mail-Adresse
    def validate_email(self, email):
        # Prüft, ob die eingegebene E-Mail-Adresse bereits in der Datenbank existiert
        user = db.session.execute(db.select(User).filter_by(email=email.data)).scalar()
        if user is not None:
            raise ValidationError('Please use a different email address.')

# Definiere eine Formular-Klasse zur Bearbeitung von Benutzerdaten
class EditUserForm(FlaskForm):
    # Feld für den Benutzernamen mit Pflicht- und Längenvalidierung
    username = StringField(
        "Benutzername",
        validators=[DataRequired(), Length(min=3, max=64, message="Der Benutzername muss zwischen 3 und 64 Zeichen lang sein.")]
    )
    # Feld für die E-Mail-Adresse mit Pflicht- und E-Mail-Format-Validierung
    email = EmailField(
        "Email",
        validators=[DataRequired(), Email(message="Bitte gib eine gültige E-Mail-Adresse ein.")]
    )
    # Feld für die Mobilnummer, das optional ist und mit einem Regex validiert wird
    phone = StringField(
        "Mobilnummer",
        validators=[
            Optional(),  # Telefonnummer ist optional
            Regexp(r"^\+?\d{7,15}$", message="Die Telefonnummer muss zwischen 7 und 15 Ziffern enthalten.")
        ]
    )
    # Feld für den Firmennamen mit Pflichtfeld-Validierung
    company = StringField("Firma", validators=[DataRequired()])
    # Feld für den Beruf mit Pflichtfeld-Validierung
    job = StringField("Beruf", validators=[DataRequired()])
    # Optionales Passwortfeld zur Änderung des Passworts, mit Längenvalidierung
    password = PasswordField(
        "Neues Passwort (optional)",
        validators=[Optional(), Length(min=8, max=128, message="Das Passwort muss mindestens 8 Zeichen lang sein.")]
    )
    # Passwort-Bestätigungsfeld, das überprüft, ob das neue Passwort korrekt wiederholt wurde
    password2 = PasswordField(
        "Passwort wiederholen",
        validators=[EqualTo("password", message="Passwörter müssen übereinstimmen.")]
    )
    # Submit-Button zum Speichern der Änderungen
    submit = SubmitField("Speichern")

    # Benutzerdefinierte Validierung für den Benutzernamen
    def validate_username(self, username):
        # Wenn der eingegebene Benutzername sich vom aktuellen Benutzernamen unterscheidet, wird überprüft, ob er bereits vergeben ist
        if username.data != current_user.username:
            user = User.query.filter_by(username=username.data).first()
            if user:
                raise ValidationError("Dieser Benutzername ist bereits vergeben. Bitte wähle einen anderen.")

    # Benutzerdefinierte Validierung für die E-Mail-Adresse
    def validate_email(self, email):
        # Wenn die eingegebene E-Mail sich von der aktuellen E-Mail unterscheidet, wird überprüft, ob sie bereits verwendet wird
        if email.data != current_user.email:
            user = User.query.filter_by(email=email.data).first()
            if user:
                raise ValidationError("Diese E-Mail-Adresse wird bereits verwendet. Bitte verwende eine andere.")

# Definiere eine Formular-Klasse für die Login-Seite
class LoginForm(FlaskForm):
    """
    Dieses Formular wird für die Login-Seite verwendet.
    Es muss die Felder 'username_or_email' und 'password' enthalten.
    """
    # Feld für die Eingabe von Benutzername oder E-Mail, mit Pflicht- und Längenvalidierung
    username_or_email = StringField(
        "Benutzername oder Email",
        validators=[
            DataRequired(message="Bitte gib deinen Benutzernamen oder deine E-Mail-Adresse ein."),
            Length(min=3, max=100)
        ]
    )
    
    # Passwortfeld mit Pflicht- und Längenvalidierung
    password = PasswordField(
        "Passwort",
        validators=[
            DataRequired(message="Bitte gib dein Passwort ein."),
            Length(min=6, max=128, message="Das Passwort muss zwischen 6 und 128 Zeichen lang sein.")
        ]
    )
    
    # Kontrollkästchen für "Passwort merken" mit Standardwert True
    remember_me = BooleanField("Passwort merken", default=True)
    # Submit-Button für das Login-Formular
    submit = SubmitField("Login")
