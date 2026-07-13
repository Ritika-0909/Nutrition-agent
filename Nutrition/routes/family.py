"""
Family management routes
"""
import logging
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models import db, FamilyMember

family_bp = Blueprint("family", __name__, url_prefix="/family")
logger    = logging.getLogger(__name__)


@family_bp.route("/")
@login_required
def family_list():
    members = FamilyMember.query.filter_by(user_id=current_user.id).all()
    return render_template("family/list.html", members=members)


@family_bp.route("/add", methods=["GET", "POST"])
@login_required
def add_member():
    if request.method == "POST":
        data = request.form
        member = FamilyMember(
            user_id            = current_user.id,
            name               = data.get("name", "").strip(),
            relation           = data.get("relation", ""),
            age                = _safe_int(data.get("age")),
            gender             = data.get("gender", ""),
            weight_kg          = _safe_float(data.get("weight_kg")),
            height_cm          = _safe_float(data.get("height_cm")),
            dietary_preference = data.get("dietary_preference", "omnivore"),
            allergies          = data.get("allergies", ""),
            medical_conditions = data.get("medical_conditions", ""),
            fitness_goal       = data.get("fitness_goal", "maintenance"),
            notes              = data.get("notes", ""),
        )
        db.session.add(member)
        db.session.commit()
        flash(f"Family member '{member.name}' added! 👨‍👩‍👧", "success")
        return redirect(url_for("family.family_list"))
    return render_template("family/add_member.html")


@family_bp.route("/<int:member_id>/edit", methods=["GET", "POST"])
@login_required
def edit_member(member_id):
    member = FamilyMember.query.filter_by(
        id=member_id, user_id=current_user.id).first_or_404()
    if request.method == "POST":
        data = request.form
        member.name               = data.get("name", member.name)
        member.relation           = data.get("relation", member.relation)
        member.age                = _safe_int(data.get("age")) or member.age
        member.gender             = data.get("gender", member.gender)
        member.weight_kg          = _safe_float(data.get("weight_kg")) or member.weight_kg
        member.height_cm          = _safe_float(data.get("height_cm")) or member.height_cm
        member.dietary_preference = data.get("dietary_preference", member.dietary_preference)
        member.allergies          = data.get("allergies", member.allergies)
        member.medical_conditions = data.get("medical_conditions", member.medical_conditions)
        member.fitness_goal       = data.get("fitness_goal", member.fitness_goal)
        member.notes              = data.get("notes", member.notes)
        db.session.commit()
        flash(f"Profile for '{member.name}' updated!", "success")
        return redirect(url_for("family.family_list"))
    return render_template("family/add_member.html", member=member)


@family_bp.route("/<int:member_id>/delete", methods=["POST"])
@login_required
def delete_member(member_id):
    member = FamilyMember.query.filter_by(
        id=member_id, user_id=current_user.id).first_or_404()
    name = member.name
    db.session.delete(member)
    db.session.commit()
    flash(f"'{name}' removed from family.", "info")
    return redirect(url_for("family.family_list"))


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
