from flask import Blueprint, render_template, redirect, url_for, flash, request, session, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from extensions import db
from models import User, Event
from auth.forms import RegistrationForm, EditUserForm, LoginForm

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        # Suche nach einem Benutzer entweder per Benutzername ODER E-Mail
        user = User.query.filter(
            (User.username == form.username_or_email.data) | 
            (User.email == form.username_or_email.data)
        ).first()

        if user and user.check_password(form.password.data):  # Passwortprüfung
            login_user(user, remember=form.remember_me.data)
            session["login_success"] = True
            return redirect(url_for("calendar.calendar_view"))  # Zielseite nach Login
        else:
            flash("Ungültiger Benutzername oder Passwort.", "danger")

    return render_template("login.html", form=form)


@auth_bp.route("/show-flash-message")
def show_flash_message():
    return render_template("show_flash.html")

@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    form = RegistrationForm()  # ✅ Formular-Instanz erstellen
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
            company=form.company.data,
            job=form.job.data,
            phone=form.phone.data,
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash("Registrierung erfolgreich! Bitte melde dich an.", "success")
        return redirect(url_for("auth.login"))

    return render_template("register.html", form=form)  # ✅ form übergeben

@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Erfolgreich ausgeloggt!", "info")
    return redirect(url_for("auth.login"))

@auth_bp.route("/edit-profile", methods=["GET", "POST"])
@login_required
def edit_profile():
    form = EditUserForm()

    if request.method == "POST" and form.validate_on_submit():
        # Überprüfung, ob sich der Benutzername oder die E-Mail geändert hat
        if form.username.data != current_user.username:
            existing_user = User.query.filter_by(username=form.username.data).first()
            if existing_user:
                flash("Dieser Benutzername ist bereits vergeben.", "danger")
                return redirect(url_for("auth.edit_profile"))

        if form.email.data != current_user.email:
            existing_email = User.query.filter_by(email=form.email.data).first()
            if existing_email:
                flash("Diese E-Mail-Adresse wird bereits verwendet.", "danger")
                return redirect(url_for("auth.edit_profile"))

        # Aktualisiere alle Felder
        current_user.username = form.username.data
        current_user.email = form.email.data
        current_user.company = form.company.data
        current_user.job = form.job.data
        current_user.phone = form.phone.data

        # Falls ein neues Passwort eingegeben wurde, speichern
        if form.password.data:
            current_user.set_password(form.password.data)

        # Änderungen in der Datenbank speichern
        db.session.commit()
        flash("Profil erfolgreich aktualisiert!", "success")
        return redirect(url_for("calendar.calendar_view"))

    # Setzt die aktuellen Werte ins Formular (damit die Felder befüllt sind)
    form.username.data = current_user.username
    form.email.data = current_user.email
    form.company.data = current_user.company
    form.job.data = current_user.job
    form.phone.data = current_user.phone

    return render_template("edit_profile.html", form=form)

# Route zum Löschen des eigenen Kontos
@auth_bp.route("/delete_account", methods=["POST"])
@login_required
def delete_account():
    user = User.query.get(current_user.id)
    
    if user:
        Event.query.filter_by(user_id=user.id).delete()
        db.session.delete(user)
        db.session.commit()
        logout_user()  # Nutzer ausloggen
        flash("Dein Konto wurde erfolgreich gelöscht.", "success")
        return redirect(url_for("auth.login"))
    
    flash("Fehler beim Löschen des Kontos!", "danger")
    return redirect(url_for("auth.edit_profile"))

