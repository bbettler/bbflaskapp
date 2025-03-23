from flask import Blueprint, jsonify, render_template, request
from extensions import db

# Erstellen eines Blueprints für Fehlerseiten
errors_bp = Blueprint("errors", __name__)

@errors_bp.app_errorhandler(404)
def not_found_error(error):
    """
    Diese Methode wird aufgerufen, wenn eine 404-Fehlermeldung (Seite nicht gefunden) auftritt.
    Falls die Anfrage JSON bevorzugt und nicht HTML, wird ein JSON-Fehler zurückgegeben.
    Andernfalls wird eine benutzerdefinierte HTML-Fehlerseite (404.html) gerendert.
    """
    if request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html:
        return jsonify({'error': 'Not found'}), 404
    else:
        return render_template('errors/404.html'), 404

@errors_bp.app_errorhandler(500)
def internal_error(error):
    """
    Diese Methode wird aufgerufen, wenn ein interner Serverfehler (500) auftritt.
    Es wird zuerst ein Rollback auf der aktuellen Datenbank-Sitzung durchgeführt,
    um offene Transaktionen zurückzusetzen.
    Falls die Anfrage JSON bevorzugt und nicht HTML, wird ein JSON-Fehler zurückgegeben.
    Andernfalls wird eine benutzerdefinierte HTML-Fehlerseite (500.html) gerendert.
    """
    db.session.rollback()  # Setzt alle offenen Transaktionen zurück
    if request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html:
        return jsonify({'error': 'Internal Server Error'}), 500
    else:
        return render_template('errors/500.html'), 500
