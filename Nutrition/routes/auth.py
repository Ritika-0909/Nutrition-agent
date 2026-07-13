"""
Authentication routes — register, login, logout, profile management
"""
import logging
from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from models import db, User, UserProfile

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")
logger  = logging.getLogger(__name__)


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("nutrition.dashboard"))
    if request.method == "POST":
        data     = request.form
        username = data.get("username", "").strip()
        email    = data.get("email", "").strip().lower()
        password = data.get("password", "")
        confirm  = data.get("confirm_password", "")
        fullname = data.get("full_name", "").strip()

        errors = []
        if not username or len(username) < 3:
            errors.append("Username must be at least 3 characters.")
        if not email or "@" not in email:
            errors.append("A valid email is required.")
        if len(password) < 8:
            errors.append("Password must be at least 8 characters.")
        if password != confirm:
            errors.append("Passwords do not match.")
        if User.query.filter_by(username=username).first():
            errors.append("Username already taken.")
        if User.query.filter_by(email=email).first():
            errors.append("Email already registered.")

        if errors:
            for e in errors:
                flash(e, "danger")
            return render_template("auth/register.html", form_data=data)

        user = User(username=username, email=email, full_name=fullname)
        user.set_password(password)
        db.session.add(user)
        db.session.flush()

        profile = UserProfile(user_id=user.id)
        db.session.add(profile)
        db.session.commit()

        logger.info(f"New user registered: {username}")
        login_user(user)
        flash(f"Welcome to NutriAgent AI, {fullname or username}! Let's set up your profile.", "success")
        return redirect(url_for("nutrition.setup_profile"))

    return render_template("auth/register.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("nutrition.dashboard"))
    if request.method == "POST":
        identifier = request.form.get("identifier", "").strip()
        password   = request.form.get("password", "")
        remember   = request.form.get("remember") == "on"

        user = (User.query.filter_by(username=identifier).first() or
                User.query.filter_by(email=identifier).first())

        if user and user.check_password(password) and user.is_active:
            user.last_login = datetime.utcnow()
            db.session.commit()
            login_user(user, remember=remember)
            logger.info(f"User logged in: {user.username}")
            next_page = request.args.get("next")
            flash(f"Welcome back, {user.full_name or user.username}! 🌿", "success")
            return redirect(next_page or url_for("nutrition.dashboard"))
        flash("Invalid credentials. Please try again.", "danger")

    return render_template("auth/login.html")


@auth_bp.route("/logout")
@login_required
def logout():
    username = current_user.username
    logout_user()
    logger.info(f"User logged out: {username}")
    flash("You've been logged out safely. Come back soon! 👋", "info")
    return redirect(url_for("auth.login"))


@auth_bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    profile = current_user.profile
    if not profile:
        profile = UserProfile(user_id=current_user.id)
        db.session.add(profile)
        db.session.commit()

    if request.method == "POST":
        data = request.form
        # Update User
        current_user.full_name   = data.get("full_name", current_user.full_name)
        current_user.language    = data.get("language", "en")
        current_user.dark_mode   = data.get("dark_mode") == "on"

        # Update Profile
        profile.age                = _safe_int(data.get("age"))
        profile.gender             = data.get("gender", "")
        profile.weight_kg          = _safe_float(data.get("weight_kg"))
        profile.height_cm          = _safe_float(data.get("height_cm"))
        profile.activity_level     = data.get("activity_level", "moderate")
        profile.fitness_goal       = data.get("fitness_goal", "maintenance")
        profile.dietary_preference = data.get("dietary_preference", "omnivore")
        profile.allergies          = data.get("allergies", "none")
        profile.medical_conditions = data.get("medical_conditions", "none")
        profile.cuisine_preference = data.get("cuisine_preference", "Indian")
        profile.cooking_skill      = data.get("cooking_skill", "intermediate")
        profile.budget             = data.get("budget", "medium")
        profile.meals_per_day      = _safe_int(data.get("meals_per_day")) or 3
        profile.sleep_hours        = _safe_float(data.get("sleep_hours")) or 7.5
        profile.stress_level       = data.get("stress_level", "moderate")
        profile.target_weight_kg   = _safe_float(data.get("target_weight_kg"))

        db.session.commit()
        flash("Profile updated successfully! 🎉", "success")
        return redirect(url_for("auth.profile"))

    return render_template("auth/profile.html", profile=profile)


@auth_bp.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    if request.method == "POST":
        action = request.form.get("action")
        if action == "change_password":
            old_pw  = request.form.get("old_password", "")
            new_pw  = request.form.get("new_password", "")
            confirm = request.form.get("confirm_password", "")
            if not current_user.check_password(old_pw):
                flash("Current password is incorrect.", "danger")
            elif len(new_pw) < 8:
                flash("New password must be at least 8 characters.", "danger")
            elif new_pw != confirm:
                flash("New passwords do not match.", "danger")
            else:
                current_user.set_password(new_pw)
                db.session.commit()
                flash("Password changed successfully! 🔒", "success")
        elif action == "delete_account":
            confirm_text = request.form.get("confirm_text", "")
            if confirm_text == "DELETE":
                username = current_user.username
                logout_user()
                user = User.query.filter_by(username=username).first()
                if user:
                    db.session.delete(user)
                    db.session.commit()
                flash("Your account has been deleted.", "info")
                return redirect(url_for("index"))
            else:
                flash("Type DELETE to confirm account deletion.", "danger")
    return render_template("auth/settings.html")


# ── Helpers ──────────────────────────────────────────────────────────────────
def _safe_int(val):
    try:
        return int(val) if val else None
    except (ValueError, TypeError):
        return None


def _safe_float(val):
    try:
        return float(val) if val else None
    except (ValueError, TypeError):
        return None
