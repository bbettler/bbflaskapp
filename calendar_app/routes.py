# Importiere notwendige Module und Funktionen aus Flask
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
# Importiere Funktionen zur Zugriffskontrolle (Login) und den aktuellen Benutzer
from flask_login import login_required, current_user
# Importiere die Datenbankerweiterung
from extensions import db
# Importiere Modelle für Events und Benutzer
from models import Event, User
# Importiere Datums- und Zeitfunktionen
from datetime import datetime, timedelta
# Importiere das Kalender-Modul zur Ermittlung von Monatsdaten
import calendar

# Erstelle ein Blueprint für das Kalender-Modul
calendar_bp = Blueprint("calendar", __name__)

# Route für die Kalenderansicht, optional mit Jahr und Monat als Parameter
@calendar_bp.route("/")
@calendar_bp.route("/<int:year>/<int:month>")
@login_required
def calendar_view(year=None, month=None):
    """ Zeigt den Monatskalender mit eigenen Events & Einladungen an """
    
    today = datetime.today()
    # Falls Jahr oder Monat nicht angegeben sind, verwende das aktuelle Datum
    if year is None or month is None:
        year, month = today.year, today.month

    # Erstelle ein Datum für den ersten Tag des aktuellen Monats
    first_day_of_current_month = datetime(year, month, 1)
    # Berechne den Vormonat, indem ein Tag abgezogen wird
    previous_month = first_day_of_current_month - timedelta(days=1)
    # Berechne den Folgemonat, indem 31 Tage hinzugefügt werden (vereinfachte Berechnung)
    next_month = first_day_of_current_month + timedelta(days=31)
    # Erstelle Links für den Vormonat und Folgemonat
    previous_month_link = url_for("calendar.calendar_view", year=previous_month.year, month=previous_month.month)
    next_month_link = url_for("calendar.calendar_view", year=next_month.year, month=next_month.month)
    # Definiere die Überschriften für die Wochentage
    weekdays_headers = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]
    # Ermittle den ersten Wochentag und die Anzahl der Tage im Monat
    first_weekday, days_in_month = calendar.monthrange(year, month)
    # Erstelle eine Liste aller Tage des Monats als Dictionaries
    month_days = [{"day": day, "month": month, "year": year} for day in range(1, days_in_month + 1)]

    # Abrufen aller Events des Nutzers für den aktuellen Monat (eigene Events und Einladungen)
    events = Event.query.filter(
        (Event.user_id == current_user.id) |  # Eigene Events
        (Event.participants.any(id=current_user.id))  # Events, zu denen man eingeladen wurde
    ).filter(
        Event.start_time <= datetime(year, month, days_in_month),
        Event.end_time >= datetime(year, month, 1)
    ).all()

    # Bereite Events vor, die sich über mehrere Tage erstrecken
    tasks = {}
    for event in events:
        current_date = event.start_time.date()
        # Iteriere über alle Tage, an denen das Event stattfindet
        while current_date <= event.end_time.date():
            event_month = current_date.month
            event_day = current_date.day

            # Initialisiere das Dictionary für den Monat, falls nicht vorhanden
            if event_month not in tasks:
                tasks[event_month] = {}
            # Initialisiere die Liste für den Tag, falls nicht vorhanden
            if event_day not in tasks[event_month]:
                tasks[event_month][event_day] = []

            # Füge das Event zum entsprechenden Tag hinzu
            tasks[event_month][event_day].append(event)
            # Gehe zum nächsten Tag
            current_date += timedelta(days=1)

    # Rendere die Kalenderseite und übergebe alle benötigten Variablen
    return render_template("calendar/calendar.html",
                           month_name=calendar.month_name[month],
                           year=year,
                           month=month,
                           current_day=today.day if today.year == year and today.month == month else None,
                           weekdays_headers=weekdays_headers,
                           month_days=month_days,
                           tasks=tasks,
                           previous_month_link=previous_month_link,
                           next_month_link=next_month_link)

# Route zum Erstellen eines neuen Events, akzeptiert GET- und POST-Anfragen
@calendar_bp.route("/new", methods=["GET", "POST"])
@login_required
def new_event():
    # Standardwerte aus der URL abrufen (falls vorhanden)
    year = request.args.get("year", type=int, default=datetime.now().year)
    month = request.args.get("month", type=int, default=datetime.now().month)
    day = request.args.get("day", type=int, default=datetime.now().day)

    # Alle Nutzer abrufen, um sie als potenzielle Teilnehmer anzuzeigen
    users = User.query.all()

    if request.method == "POST":
        # Abrufen der Formulardaten
        title = request.form["title"]
        description = request.form["description"]
        start_time = datetime.strptime(request.form["start_time"], "%Y-%m-%dT%H:%M")
        end_time = datetime.strptime(request.form["end_time"], "%Y-%m-%dT%H:%M")
        # Abrufen der ausgewählten Teilnehmer-IDs (Multi-Select)
        selected_user_ids = request.form.getlist("participants")

        # Erstelle ein neues Event mit den eingegebenen Daten und dem aktuellen Benutzer als Ersteller
        event = Event(
            title=title,
            description=description,
            start_time=start_time,
            end_time=end_time,
            user_id=current_user.id
        )

        # Füge Teilnehmer hinzu, falls vorhanden
        for user_id in selected_user_ids:
            user = User.query.get(int(user_id))
            if user:
                event.participants.append(user)

        # Füge das Event der Datenbank hinzu und speichere die Änderungen
        db.session.add(event)
        db.session.commit()
        flash("Event erfolgreich hinzugefügt!", "success")
        return redirect(url_for("calendar.calendar_view"))

    # Standard-Datum für das Formular vorbefüllen (im Format YYYY-MM-DDTHH:MM)
    default_date = f"{year:04d}-{month:02d}-{day:02d}T12:00"

    # Rendere die Seite zum Erstellen eines neuen Events und übergebe das Standarddatum sowie die Nutzerliste
    return render_template("calendar/new_event.html", default_date=default_date, users=users)

# Route zum Bearbeiten eines bestehenden Events, akzeptiert GET- und POST-Anfragen
@calendar_bp.route("/edit/<int:event_id>", methods=["GET", "POST"])
@login_required
def edit_event(event_id):
    # Suche das Event anhand der event_id, wenn nicht gefunden, wird 404 zurückgegeben
    event = Event.query.get_or_404(event_id)

    # 🔒 Sicherstellen, dass nur der Ersteller das Event bearbeiten kann
    if event.user_id != current_user.id:
        flash("Du hast keine Berechtigung, dieses Event zu bearbeiten.", "danger")
        return redirect(url_for("calendar.calendar_view"))

    # Alle Nutzer abrufen, um die Teilnehmerauswahl zu ermöglichen
    all_users = User.query.all()

    if request.method == "POST":
        # Aktualisiere die Event-Daten anhand der eingegebenen Formulardaten
        event.title = request.form["title"]
        event.description = request.form["description"]
        event.start_time = datetime.strptime(request.form["start_time"], "%Y-%m-%dT%H:%M")
        event.end_time = datetime.strptime(request.form["end_time"], "%Y-%m-%dT%H:%M")

        # Aktualisiere die Teilnehmerliste
        selected_user_ids = request.form.getlist("participants")  # Liste der gewählten Teilnehmer
        selected_users = User.query.filter(User.id.in_(selected_user_ids)).all()

        event.participants.clear()  # Entferne alle bisherigen Teilnehmer
        event.participants.extend(selected_users)  # Füge die neuen Teilnehmer hinzu

        db.session.commit()  # Speichere die Änderungen in der Datenbank
        flash("Event erfolgreich aktualisiert!", "success")
        return redirect(url_for("calendar.calendar_view"))

    # Rendere die Bearbeitungsseite für das Event und übergebe das Event und die Liste aller Nutzer
    return render_template("calendar/edit_event.html", event=event, all_users=all_users)

# Route zum Löschen eines Events, akzeptiert nur DELETE-Anfragen
@calendar_bp.route("/delete/<int:event_id>", methods=["DELETE"])
@login_required
def delete_event(event_id):
    # Suche das Event anhand der event_id
    event = Event.query.get(event_id)
    # Überprüfe, ob das Event existiert und ob der aktuelle Benutzer der Ersteller ist
    if event and event.user_id == current_user.id:
        db.session.delete(event)  # Lösche das Event aus der Datenbank
        db.session.commit()  # Speichere die Änderungen in der Datenbank
        return jsonify({"success": True}), 200
    # Gib eine Fehlermeldung zurück, falls das Event nicht gefunden wurde oder keine Berechtigung vorliegt
    return jsonify({"error": "Nicht gefunden oder keine Berechtigung"}), 403
