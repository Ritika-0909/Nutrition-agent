"""
Core nutrition routes — dashboard, chat, meal planning, BMI, calorie tracker
"""
import json
import uuid
import logging
from datetime import datetime, date, timedelta
from flask import (Blueprint, render_template, request, jsonify,
                   redirect, url_for, flash, session, send_file)
from flask_login import login_required, current_user
from models import db, UserProfile, ChatMessage, NutritionLog, WaterLog, MealPlan
from agent import get_agent

nutrition_bp = Blueprint("nutrition", __name__)
logger       = logging.getLogger(__name__)


@nutrition_bp.route("/dashboard")
@login_required
def dashboard():
    agent   = get_agent()
    profile = current_user.profile
    today   = date.today()

    # Today's water
    water_today = db.session.query(
        db.func.sum(WaterLog.amount_ml)
    ).filter(WaterLog.user_id == current_user.id, WaterLog.log_date == today).scalar() or 0

    # Hydration goal
    hydration_goal = 2500
    if profile and profile.weight_kg:
        h = agent.calculate_hydration(profile.weight_kg,
                                       profile.activity_level or "moderate")
        hydration_goal = h["total_ml"]

    # Today's nutrition
    todays_logs = NutritionLog.query.filter_by(
        user_id=current_user.id, log_date=today).all()
    total_cals  = sum(l.calories or 0 for l in todays_logs)
    total_prot  = sum(l.protein_g or 0 for l in todays_logs)
    total_carbs = sum(l.carbs_g or 0 for l in todays_logs)
    total_fat   = sum(l.fat_g or 0 for l in todays_logs)

    # BMI
    bmi_data = None
    if profile and profile.weight_kg and profile.height_cm:
        bmi_data = agent.calculate_bmi(profile.weight_kg, profile.height_cm)

    # TDEE
    tdee = None
    if profile and all([profile.weight_kg, profile.height_cm, profile.age, profile.gender]):
        bmr  = agent.calculate_bmr(profile.weight_kg, profile.height_cm,
                                    profile.age, profile.gender)
        tdee = int(agent.calculate_tdee(bmr, profile.activity_level or "moderate"))

    # Weekly nutrition (last 7 days)
    week_ago = today - timedelta(days=6)
    weekly = db.session.query(
        NutritionLog.log_date,
        db.func.sum(NutritionLog.calories)
    ).filter(
        NutritionLog.user_id == current_user.id,
        NutritionLog.log_date >= week_ago
    ).group_by(NutritionLog.log_date).all()

    weekly_data = {str(r[0]): int(r[1] or 0) for r in weekly}
    chart_labels = [(week_ago + timedelta(days=i)).strftime("%a") for i in range(7)]
    chart_values = [weekly_data.get(str(week_ago + timedelta(days=i)), 0) for i in range(7)]

    # Recent chat
    recent_chats = ChatMessage.query.filter_by(
        user_id=current_user.id
    ).order_by(ChatMessage.created_at.desc()).limit(5).all()

    # Active meal plan
    active_plan = MealPlan.query.filter_by(
        user_id=current_user.id, is_active=True
    ).order_by(MealPlan.created_at.desc()).first()

    return render_template("nutrition/dashboard.html",
        profile=profile, bmi_data=bmi_data, tdee=tdee,
        water_today=water_today, hydration_goal=hydration_goal,
        total_cals=total_cals, total_prot=total_prot,
        total_carbs=total_carbs, total_fat=total_fat,
        chart_labels=json.dumps(chart_labels), chart_values=json.dumps(chart_values),
        recent_chats=recent_chats, active_plan=active_plan,
        family_count=len(current_user.family_members),
        current_hour=datetime.now().hour)


@nutrition_bp.route("/setup-profile", methods=["GET", "POST"])
@login_required
def setup_profile():
    return redirect(url_for("auth.profile"))


@nutrition_bp.route("/chat")
@login_required
def chat():
    history = ChatMessage.query.filter_by(
        user_id=current_user.id
    ).order_by(ChatMessage.created_at.asc()).limit(100).all()
    if "chat_session_id" not in session:
        session["chat_session_id"] = str(uuid.uuid4())
    return render_template("nutrition/chat.html", chat_history=history)


@nutrition_bp.route("/meal-plan")
@login_required
def meal_plan():
    plans = MealPlan.query.filter_by(user_id=current_user.id).order_by(
        MealPlan.created_at.desc()).all()
    return render_template("nutrition/meal_plan.html", plans=plans)


@nutrition_bp.route("/bmi-calculator")
@login_required
def bmi_calculator():
    profile  = current_user.profile
    bmi_data = None
    if profile and profile.weight_kg and profile.height_cm:
        bmi_data = get_agent().calculate_bmi(profile.weight_kg, profile.height_cm)
    return render_template("nutrition/bmi_calculator.html",
                           profile=profile, bmi_data=bmi_data)


@nutrition_bp.route("/calorie-tracker")
@login_required
def calorie_tracker():
    today = date.today()
    logs  = NutritionLog.query.filter_by(
        user_id=current_user.id, log_date=today
    ).order_by(NutritionLog.created_at.asc()).all()

    profile = current_user.profile
    tdee    = 2000
    if profile and all([profile.weight_kg, profile.height_cm, profile.age, profile.gender]):
        agent = get_agent()
        bmr   = agent.calculate_bmr(profile.weight_kg, profile.height_cm,
                                     profile.age, profile.gender)
        tdee  = int(agent.calculate_tdee(bmr, profile.activity_level or "moderate"))

    return render_template("nutrition/calorie_tracker.html",
                           logs=logs, today=today, tdee=tdee)


@nutrition_bp.route("/history")
@login_required
def history():
    page  = request.args.get("page", 1, type=int)
    logs  = NutritionLog.query.filter_by(user_id=current_user.id).order_by(
        NutritionLog.log_date.desc()
    ).paginate(page=page, per_page=30, error_out=False)
    return render_template("nutrition/history.html", logs=logs)


@nutrition_bp.route("/recipes")
@login_required
def recipes():
    return render_template("nutrition/recipes.html")


@nutrition_bp.route("/hydration")
@login_required
def hydration():
    agent   = get_agent()
    profile = current_user.profile
    today   = date.today()

    water_today = db.session.query(
        db.func.sum(WaterLog.amount_ml)
    ).filter(WaterLog.user_id == current_user.id, WaterLog.log_date == today).scalar() or 0

    goal = {"total_ml": 2500, "total_L": 2.5, "glasses_8oz": 10, "hourly_ml": 156}
    if profile and profile.weight_kg:
        goal = agent.calculate_hydration(profile.weight_kg,
                                          profile.activity_level or "moderate")

    # Last 7 days water data
    week_ago = today - timedelta(days=6)
    weekly = db.session.query(
        WaterLog.log_date, db.func.sum(WaterLog.amount_ml)
    ).filter(
        WaterLog.user_id == current_user.id,
        WaterLog.log_date >= week_ago
    ).group_by(WaterLog.log_date).all()
    weekly_water = {str(r[0]): int(r[1] or 0) for r in weekly}
    chart_labels = [(week_ago + timedelta(days=i)).strftime("%a") for i in range(7)]
    chart_values = [weekly_water.get(str(week_ago + timedelta(days=i)), 0) for i in range(7)]

    return render_template("nutrition/hydration.html",
        water_today=water_today, goal=goal,
        chart_labels=json.dumps(chart_labels),
        chart_values=json.dumps(chart_values))
