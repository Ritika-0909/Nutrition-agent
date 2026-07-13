"""
RESTful API routes — AI chat, nutrition logs, water tracking, PDF export
"""
import json
import logging
import uuid
from datetime import datetime, date
from io import BytesIO
from flask import Blueprint, request, jsonify, session, send_file
from flask_login import login_required, current_user
from models import db, ChatMessage, NutritionLog, WaterLog, MealPlan
from agent import get_agent

api_bp = Blueprint("api", __name__)
logger = logging.getLogger(__name__)


# ── AI Chat endpoint ─────────────────────────────────────────────────────────
@api_bp.route("/chat", methods=["POST"])
@login_required
def chat_api():
    data        = request.get_json(force=True) or {}
    user_msg    = (data.get("message") or "").strip()
    task_type   = data.get("task_type", "chat")
    member_id   = data.get("member_id")

    if not user_msg:
        return jsonify({"error": "Message cannot be empty"}), 400

    # Build user profile dict
    profile     = current_user.profile
    user_profile = {}
    if profile:
        user_profile = {
            "name":               current_user.full_name or current_user.username,
            "age":                profile.age,
            "gender":             profile.gender,
            "weight_kg":          profile.weight_kg,
            "height_cm":          profile.height_cm,
            "activity_level":     profile.activity_level,
            "fitness_goal":       profile.fitness_goal,
            "dietary_preference": profile.dietary_preference,
            "allergies":          profile.allergies,
            "medical_conditions": profile.medical_conditions,
            "cuisine_preference": profile.cuisine_preference,
        }

    # If asking for family member context
    if member_id:
        from models import FamilyMember
        member = FamilyMember.query.filter_by(
            id=member_id, user_id=current_user.id).first()
        if member:
            user_profile.update({
                "name":               member.name,
                "age":                member.age,
                "gender":             member.gender,
                "weight_kg":          member.weight_kg,
                "height_cm":          member.height_cm,
                "dietary_preference": member.dietary_preference,
                "allergies":          member.allergies,
                "medical_conditions": member.medical_conditions,
                "fitness_goal":       member.fitness_goal,
            })

    # Fetch recent chat history
    session_id   = session.get("chat_session_id", str(uuid.uuid4()))
    session["chat_session_id"] = session_id
    history_rows = ChatMessage.query.filter_by(
        user_id=current_user.id
    ).order_by(ChatMessage.created_at.asc()).limit(20).all()
    chat_history = [{"role": r.role, "content": r.content} for r in history_rows]

    # Generate AI response
    agent    = get_agent()
    response = agent.generate_response(user_msg, user_profile, chat_history, task_type)

    # Save messages
    user_record = ChatMessage(
        user_id=current_user.id, session_id=session_id,
        role="user", content=user_msg, task_type=task_type, member_id=member_id)
    ai_record   = ChatMessage(
        user_id=current_user.id, session_id=session_id,
        role="assistant", content=response, task_type=task_type, member_id=member_id)
    db.session.add_all([user_record, ai_record])
    db.session.commit()

    agent = get_agent()
    return jsonify({
        "response":    response,
        "task_type":   task_type,
        "timestamp":   datetime.utcnow().isoformat(),
        "ai_status":   agent.init_status,        # "ok" | "project_not_found" | "auth_error" | ...
    })


# ── AI Connection test ───────────────────────────────────────────────────────
@api_bp.route("/test-connection", methods=["GET"])
@login_required
def test_connection():
    """Returns the current AI engine status — useful for the settings/dashboard page."""
    agent = get_agent()
    status = agent.init_status
    ok     = status == "ok"
    return jsonify({
        "ok":         ok,
        "status":     status,
        "model_id":   agent.model_id,
        "project_id": agent.project_id[:8] + "…" if agent.project_id else "not set",
        "error":      agent.init_error[:300] if agent.init_error else None,
        "hint": {
            "project_not_found": "Create/open a Watsonx.ai project at dataplatform.cloud.ibm.com and copy its Project ID into .env",
            "auth_error":        "Regenerate your IBM API key at cloud.ibm.com/iam/apikeys and update IBM_API_KEY in .env",
            "no_credentials":    "Copy .env.example to .env and fill in IBM_API_KEY and IBM_PROJECT_ID",
            "error":             "Check the app log (nutriagent.log) for the full error message",
            "ok":                "IBM Watsonx AI is connected and ready ✅",
        }.get(status, "Unknown status"),
    })


# ── Nutrition Log endpoints ──────────────────────────────────────────────────
@api_bp.route("/nutrition/log", methods=["POST"])
@login_required
def add_nutrition_log():
    data = request.get_json(force=True) or {}
    log  = NutritionLog(
        user_id   = current_user.id,
        log_date  = date.today(),
        meal_type = data.get("meal_type", "snack"),
        food_name = data.get("food_name", "Unknown"),
        calories  = float(data.get("calories", 0)),
        protein_g = float(data.get("protein_g", 0)),
        carbs_g   = float(data.get("carbs_g", 0)),
        fat_g     = float(data.get("fat_g", 0)),
        fiber_g   = float(data.get("fiber_g", 0)),
        notes     = data.get("notes", ""),
    )
    db.session.add(log)
    db.session.commit()
    return jsonify({"success": True, "id": log.id, "message": "Food logged!"})


@api_bp.route("/nutrition/log/<int:log_id>", methods=["DELETE"])
@login_required
def delete_nutrition_log(log_id):
    log = NutritionLog.query.filter_by(id=log_id, user_id=current_user.id).first_or_404()
    db.session.delete(log)
    db.session.commit()
    return jsonify({"success": True})


@api_bp.route("/nutrition/today", methods=["GET"])
@login_required
def get_today_nutrition():
    today = date.today()
    logs  = NutritionLog.query.filter_by(user_id=current_user.id, log_date=today).all()
    return jsonify({
        "logs":   [l.to_dict() for l in logs],
        "totals": {
            "calories":  sum(l.calories or 0 for l in logs),
            "protein_g": sum(l.protein_g or 0 for l in logs),
            "carbs_g":   sum(l.carbs_g or 0 for l in logs),
            "fat_g":     sum(l.fat_g or 0 for l in logs),
            "fiber_g":   sum(l.fiber_g or 0 for l in logs),
        }
    })


# ── Water tracking endpoints ─────────────────────────────────────────────────
@api_bp.route("/water/log", methods=["POST"])
@login_required
def log_water():
    data      = request.get_json(force=True) or {}
    amount_ml = int(data.get("amount_ml", 250))
    today     = date.today()
    entry     = WaterLog(user_id=current_user.id, log_date=today, amount_ml=amount_ml)
    db.session.add(entry)
    db.session.commit()

    total = db.session.query(
        db.func.sum(WaterLog.amount_ml)
    ).filter(WaterLog.user_id == current_user.id, WaterLog.log_date == today).scalar() or 0

    return jsonify({"success": True, "total_ml": total, "message": f"+{amount_ml}ml logged!"})


@api_bp.route("/water/today", methods=["GET"])
@login_required
def get_today_water():
    today = date.today()
    total = db.session.query(
        db.func.sum(WaterLog.amount_ml)
    ).filter(WaterLog.user_id == current_user.id, WaterLog.log_date == today).scalar() or 0
    return jsonify({"total_ml": total})


# ── Meal Plan endpoints ──────────────────────────────────────────────────────
@api_bp.route("/meal-plan/generate", methods=["POST"])
@login_required
def generate_meal_plan():
    data        = request.get_json(force=True) or {}
    duration    = data.get("duration", "7 days")
    preferences = data.get("preferences", "")
    member_id   = data.get("member_id")

    profile  = current_user.profile
    pdata    = {}
    if profile:
        pdata = {
            "name":               current_user.full_name or current_user.username,
            "age":                profile.age,
            "gender":             profile.gender,
            "weight_kg":          profile.weight_kg,
            "height_cm":          profile.height_cm,
            "activity_level":     profile.activity_level,
            "fitness_goal":       profile.fitness_goal,
            "dietary_preference": profile.dietary_preference,
            "allergies":          profile.allergies,
            "medical_conditions": profile.medical_conditions,
        }

    prompt = (
        f"Generate a detailed {duration} Indian-inspired meal plan for:\n"
        f"Profile: {json.dumps(pdata, indent=2)}\n"
        f"Additional preferences: {preferences or 'None'}\n"
        f"Include daily breakfast, lunch, dinner, and 2 snacks with calories for each meal."
    )

    agent    = get_agent()
    plan_txt = agent.generate_response(prompt, pdata, [], "meal_plan")

    meal_plan = MealPlan(
        user_id   = current_user.id,
        member_id = member_id,
        plan_name = f"{duration.title()} Plan — {datetime.utcnow().strftime('%b %d, %Y')}",
        plan_data = plan_txt,
        duration  = duration,
        is_active = True,
    )
    # Deactivate older plans
    MealPlan.query.filter_by(user_id=current_user.id, is_active=True).update({"is_active": False})
    db.session.add(meal_plan)
    db.session.commit()

    return jsonify({"success": True, "plan": plan_txt, "plan_id": meal_plan.id})


@api_bp.route("/meal-plan/<int:plan_id>", methods=["DELETE"])
@login_required
def delete_meal_plan(plan_id):
    plan = MealPlan.query.filter_by(id=plan_id, user_id=current_user.id).first_or_404()
    db.session.delete(plan)
    db.session.commit()
    return jsonify({"success": True})


# ── BMI & Nutrition calculations ─────────────────────────────────────────────
@api_bp.route("/calculate/bmi", methods=["POST"])
@login_required
def calc_bmi():
    data = request.get_json(force=True) or {}
    try:
        weight = float(data["weight_kg"])
        height = float(data["height_cm"])
        result = get_agent().calculate_bmi(weight, height)
        return jsonify(result)
    except (KeyError, ValueError, TypeError) as e:
        return jsonify({"error": str(e)}), 400


@api_bp.route("/calculate/tdee", methods=["POST"])
@login_required
def calc_tdee():
    data = request.get_json(force=True) or {}
    try:
        agent    = get_agent()
        bmr      = agent.calculate_bmr(
            float(data["weight_kg"]), float(data["height_cm"]),
            int(data["age"]), data["gender"])
        tdee     = agent.calculate_tdee(bmr, data.get("activity_level", "moderate"))
        return jsonify({"bmr": round(bmr), "tdee": round(tdee)})
    except (KeyError, ValueError, TypeError) as e:
        return jsonify({"error": str(e)}), 400


@api_bp.route("/calculate/hydration", methods=["POST"])
@login_required
def calc_hydration():
    data = request.get_json(force=True) or {}
    try:
        result = get_agent().calculate_hydration(
            float(data["weight_kg"]),
            data.get("activity_level", "moderate"),
            data.get("climate", "temperate"))
        return jsonify(result)
    except (KeyError, ValueError, TypeError) as e:
        return jsonify({"error": str(e)}), 400


# ── PDF Report endpoint ──────────────────────────────────────────────────────
@api_bp.route("/report/pdf", methods=["GET"])
@login_required
def download_pdf_report():
    try:
        from utils.pdf_generator import generate_nutrition_report
        pdf_buffer = generate_nutrition_report(current_user)
        return send_file(
            pdf_buffer,
            mimetype="application/pdf",
            as_attachment=True,
            download_name=f"nutrition_report_{current_user.username}_{date.today()}.pdf",
        )
    except Exception as e:
        logger.error(f"PDF generation error: {e}")
        return jsonify({"error": "PDF generation failed. Please try again."}), 500


# ── User Preferences ────────────────────────────────────────────────────────
@api_bp.route("/preferences", methods=["POST"])
@login_required
def update_preferences():
    data = request.get_json(force=True) or {}
    if "dark_mode" in data:
        current_user.dark_mode = bool(data["dark_mode"])
        db.session.commit()
    return jsonify({"success": True})


# ── Clear chat history ───────────────────────────────────────────────────────
@api_bp.route("/chat/clear", methods=["POST"])
@login_required
def clear_chat():
    ChatMessage.query.filter_by(user_id=current_user.id).delete()
    db.session.commit()
    if "chat_session_id" in session:
        del session["chat_session_id"]
    return jsonify({"success": True, "message": "Chat history cleared."})


# ── AI-powered calorie analysis ──────────────────────────────────────────────
@api_bp.route("/analyze/food", methods=["POST"])
@login_required
def analyze_food():
    data      = request.get_json(force=True) or {}
    food_text = (data.get("food") or "").strip()
    if not food_text:
        return jsonify({"error": "Food description required"}), 400

    profile = current_user.profile
    pdata   = {}
    if profile:
        pdata = {
            "dietary_preference": profile.dietary_preference,
            "allergies":          profile.allergies,
            "medical_conditions": profile.medical_conditions,
        }

    prompt = (
        f"Provide a detailed nutritional analysis for: {food_text}\n"
        "Include: total calories, protein (g), carbohydrates (g), fat (g), "
        "fiber (g), sugar (g), sodium (mg), key vitamins and minerals. "
        "Also give a health rating (1-10) and explain pros/cons."
    )
    agent    = get_agent()
    analysis = agent.generate_response(prompt, pdata, [], "calorie_analysis")
    return jsonify({"analysis": analysis, "food": food_text})


# ── AI Recipe suggestion ─────────────────────────────────────────────────────
@api_bp.route("/recipe/suggest", methods=["POST"])
@login_required
def suggest_recipe():
    data        = request.get_json(force=True) or {}
    ingredients = data.get("ingredients", "")
    preferences = data.get("preferences", "")
    meal_type   = data.get("meal_type", "any")

    profile  = current_user.profile
    pdata    = {}
    if profile:
        pdata = {
            "dietary_preference": profile.dietary_preference,
            "allergies":          profile.allergies,
            "cuisine_preference": profile.cuisine_preference,
        }

    prompt = (
        f"Suggest a healthy, delicious {meal_type} recipe.\n"
        f"Available ingredients: {ingredients or 'flexible'}\n"
        f"Preferences: {preferences or 'healthy Indian-inspired'}\n"
        f"User profile: {pdata}\n"
        "Provide full recipe with ingredients, steps, cooking time, and nutrition info."
    )
    agent  = get_agent()
    recipe = agent.generate_response(prompt, pdata, [], "recipe")
    return jsonify({"recipe": recipe})
