"""
PDF Report generator for NutriAgent AI
Generates professional nutrition reports using ReportLab
"""
import io
import logging
from datetime import date, timedelta
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                 TableStyle, HRFlowable, KeepTogether)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

logger = logging.getLogger(__name__)

# ── Brand Colors ──────────────────────────────────────────────────────────────
PRIMARY   = colors.HexColor("#3b82d4")
SECONDARY = colors.HexColor("#7c5cd8")
SUCCESS   = colors.HexColor("#22c55e")
WARNING   = colors.HexColor("#f59e0b")
DANGER    = colors.HexColor("#ef4444")
LIGHT_BG  = colors.HexColor("#f7f8fa")
DARK_TEXT = colors.HexColor("#1f2328")
MUTED     = colors.HexColor("#57606a")
BORDER    = colors.HexColor("#e5e7eb")


def generate_nutrition_report(user) -> io.BytesIO:
    """Generate a comprehensive PDF nutrition report for the user."""
    from models import db, NutritionLog, WaterLog, MealPlan
    buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        leftMargin=18*mm, rightMargin=18*mm,
        topMargin=20*mm, bottomMargin=20*mm,
    )

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle("Title2",   parent=styles["Heading1"], fontSize=22, textColor=PRIMARY,   spaceAfter=4,  alignment=TA_CENTER))
    styles.add(ParagraphStyle("Subtitle", parent=styles["Normal"],   fontSize=11, textColor=MUTED,     spaceAfter=16, alignment=TA_CENTER))
    styles.add(ParagraphStyle("H2",       parent=styles["Heading2"], fontSize=14, textColor=PRIMARY,   spaceBefore=14, spaceAfter=6))
    styles.add(ParagraphStyle("H3",       parent=styles["Heading3"], fontSize=12, textColor=DARK_TEXT, spaceBefore=10, spaceAfter=4))
    styles.add(ParagraphStyle("Body",     parent=styles["Normal"],   fontSize=10, textColor=DARK_TEXT, leading=16))
    styles.add(ParagraphStyle("Muted",    parent=styles["Normal"],   fontSize=9,  textColor=MUTED,     leading=14))
    styles.add(ParagraphStyle("Footer",   parent=styles["Normal"],   fontSize=8,  textColor=MUTED,     alignment=TA_CENTER))

    today     = date.today()
    week_ago  = today - timedelta(days=6)
    profile   = user.profile
    story     = []

    # ── Cover ───────────────────────────────────────────────────────────────
    story.append(Spacer(1, 10*mm))
    story.append(Paragraph("NutriAgent AI", styles["Title2"]))
    story.append(Paragraph("Personalized Nutrition Report", styles["Subtitle"]))
    story.append(HRFlowable(width="100%", thickness=2, color=PRIMARY, spaceAfter=4*mm))
    story.append(Paragraph(f"Report for: <b>{user.full_name or user.username}</b>", styles["Body"]))
    story.append(Paragraph(f"Date: {today.strftime('%B %d, %Y')}", styles["Body"]))
    story.append(Paragraph(f"Period: {week_ago.strftime('%b %d')} – {today.strftime('%b %d, %Y')}", styles["Body"]))
    story.append(Spacer(1, 8*mm))

    # ── Profile Summary ──────────────────────────────────────────────────────
    story.append(Paragraph("Profile Summary", styles["H2"]))
    if profile:
        from agent import get_agent
        agent = get_agent()
        bmi_str  = "N/A"
        tdee_str = "N/A"
        if profile.weight_kg and profile.height_cm:
            bmi = agent.calculate_bmi(profile.weight_kg, profile.height_cm)
            bmi_str = f"{bmi['bmi']} ({bmi['category']})"
        if all([profile.weight_kg, profile.height_cm, profile.age, profile.gender]):
            bmr  = agent.calculate_bmr(profile.weight_kg, profile.height_cm, profile.age, profile.gender)
            tdee = agent.calculate_tdee(bmr, profile.activity_level or "moderate")
            tdee_str = f"{int(tdee)} kcal/day"

        profile_data = [
            ["Field", "Value"],
            ["Age",              f"{profile.age or 'N/A'} years"],
            ["Gender",           profile.gender or "N/A"],
            ["Weight",           f"{profile.weight_kg or 'N/A'} kg"],
            ["Height",           f"{profile.height_cm or 'N/A'} cm"],
            ["BMI",              bmi_str],
            ["Activity Level",   (profile.activity_level or "moderate").replace("_", " ").title()],
            ["Fitness Goal",     (profile.fitness_goal or "maintenance").replace("_", " ").title()],
            ["Dietary Pref.",    (profile.dietary_preference or "omnivore").title()],
            ["Daily Calorie Goal", tdee_str],
            ["Allergies",        profile.allergies or "None"],
            ["Medical Conditions", profile.medical_conditions or "None"],
        ]
        t = Table(profile_data, colWidths=[60*mm, 110*mm])
        t.setStyle(TableStyle([
            ("BACKGROUND",  (0, 0), (-1, 0),  PRIMARY),
            ("TEXTCOLOR",   (0, 0), (-1, 0),  colors.white),
            ("FONTNAME",    (0, 0), (-1, 0),  "Helvetica-Bold"),
            ("FONTSIZE",    (0, 0), (-1, 0),  10),
            ("BACKGROUND",  (0, 1), (-1, -1), LIGHT_BG),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT_BG]),
            ("FONTNAME",    (0, 1), (0, -1),  "Helvetica-Bold"),
            ("FONTSIZE",    (0, 1), (-1, -1), 9),
            ("GRID",        (0, 0), (-1, -1), 0.5, BORDER),
            ("ROUNDEDCORNERS", [4]),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("TOPPADDING",    (0, 0), (-1, -1), 5),
            ("LEFTPADDING",   (0, 0), (-1, -1), 8),
        ]))
        story.append(t)
    else:
        story.append(Paragraph("Profile not set up.", styles["Body"]))

    story.append(Spacer(1, 6*mm))

    # ── 7-Day Nutrition Summary ──────────────────────────────────────────────
    story.append(Paragraph("7-Day Nutrition Summary", styles["H2"]))
    logs = NutritionLog.query.filter(
        NutritionLog.user_id == user.id,
        NutritionLog.log_date >= week_ago
    ).all()

    if logs:
        from collections import defaultdict
        daily = defaultdict(lambda: {"calories": 0, "protein_g": 0, "carbs_g": 0, "fat_g": 0, "fiber_g": 0})
        for l in logs:
            d = str(l.log_date)
            daily[d]["calories"]  += l.calories or 0
            daily[d]["protein_g"] += l.protein_g or 0
            daily[d]["carbs_g"]   += l.carbs_g or 0
            daily[d]["fat_g"]     += l.fat_g or 0
            daily[d]["fiber_g"]   += l.fiber_g or 0

        table_data = [["Date", "Calories", "Protein", "Carbs", "Fat", "Fiber"]]
        totals     = {"calories": 0, "protein_g": 0, "carbs_g": 0, "fat_g": 0, "fiber_g": 0}
        for i in range(7):
            d = str(week_ago + timedelta(days=i))
            r = daily.get(d, {})
            table_data.append([
                (week_ago + timedelta(days=i)).strftime("%b %d, %a"),
                f"{int(r.get('calories',0))} kcal",
                f"{r.get('protein_g',0):.1f}g",
                f"{r.get('carbs_g',0):.1f}g",
                f"{r.get('fat_g',0):.1f}g",
                f"{r.get('fiber_g',0):.1f}g",
            ])
            for k in totals: totals[k] += r.get(k, 0)
        table_data.append([
            "TOTAL (7d)",
            f"{int(totals['calories'])} kcal",
            f"{totals['protein_g']:.1f}g",
            f"{totals['carbs_g']:.1f}g",
            f"{totals['fat_g']:.1f}g",
            f"{totals['fiber_g']:.1f}g",
        ])
        nt = Table(table_data, colWidths=[38*mm, 30*mm, 25*mm, 25*mm, 25*mm, 25*mm])
        nt.setStyle(TableStyle([
            ("BACKGROUND",  (0, 0), (-1, 0),  PRIMARY),
            ("TEXTCOLOR",   (0, 0), (-1, 0),  colors.white),
            ("FONTNAME",    (0, 0), (-1, 0),  "Helvetica-Bold"),
            ("BACKGROUND",  (0, -1), (-1, -1), colors.HexColor("#e0f2fe")),
            ("FONTNAME",    (0, -1), (-1, -1), "Helvetica-Bold"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -2), [colors.white, LIGHT_BG]),
            ("FONTSIZE",    (0, 0), (-1, -1), 9),
            ("GRID",        (0, 0), (-1, -1), 0.5, BORDER),
            ("ALIGN",       (1, 0), (-1, -1), "CENTER"),
            ("BOTTOMPADDING", (0,0), (-1,-1), 5),
            ("TOPPADDING",    (0,0), (-1,-1), 5),
        ]))
        story.append(nt)
    else:
        story.append(Paragraph("No nutrition data logged this week.", styles["Muted"]))

    story.append(Spacer(1, 6*mm))

    # ── Hydration Summary ────────────────────────────────────────────────────
    story.append(Paragraph("Hydration Summary (Last 7 Days)", styles["H2"]))
    water_logs = WaterLog.query.filter(
        WaterLog.user_id == user.id,
        WaterLog.log_date >= week_ago
    ).all()
    if water_logs:
        total_water = sum(w.amount_ml for w in water_logs)
        avg_water   = total_water / 7
        story.append(Paragraph(f"Total water: <b>{total_water:,} ml</b>  |  "
                                f"Daily average: <b>{int(avg_water)} ml</b>", styles["Body"]))
    else:
        story.append(Paragraph("No hydration data logged.", styles["Muted"]))

    story.append(Spacer(1, 6*mm))

    # ── Active Meal Plan ─────────────────────────────────────────────────────
    active_plan = MealPlan.query.filter_by(user_id=user.id, is_active=True).first()
    if active_plan:
        story.append(Paragraph("Active Meal Plan", styles["H2"]))
        story.append(Paragraph(f"<b>{active_plan.plan_name}</b>", styles["H3"]))
        plan_text = active_plan.plan_data[:1500] + ("..." if len(active_plan.plan_data) > 1500 else "")
        story.append(Paragraph(plan_text.replace('\n', '<br/>'), styles["Body"]))

    story.append(Spacer(1, 8*mm))

    # ── Family Members ───────────────────────────────────────────────────────
    if user.family_members:
        story.append(Paragraph("Family Profiles", styles["H2"]))
        fm_data = [["Name", "Relation", "Age", "Dietary Pref.", "Goal", "Conditions"]]
        for m in user.family_members:
            fm_data.append([
                m.name, m.relation or "N/A",
                str(m.age or "N/A"),
                (m.dietary_preference or "omnivore").title(),
                (m.fitness_goal or "maintenance").replace("_", " ").title(),
                (m.medical_conditions or "None")[:30],
            ])
        fmt = Table(fm_data, colWidths=[28*mm, 25*mm, 15*mm, 28*mm, 28*mm, 44*mm])
        fmt.setStyle(TableStyle([
            ("BACKGROUND",  (0, 0), (-1, 0), SECONDARY),
            ("TEXTCOLOR",   (0, 0), (-1, 0), colors.white),
            ("FONTNAME",    (0, 0), (-1, 0), "Helvetica-Bold"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT_BG]),
            ("FONTSIZE",    (0, 0), (-1, -1), 8),
            ("GRID",        (0, 0), (-1, -1), 0.5, BORDER),
            ("BOTTOMPADDING", (0,0), (-1,-1), 4), ("TOPPADDING", (0,0), (-1,-1), 4),
        ]))
        story.append(fmt)
        story.append(Spacer(1, 6*mm))

    # ── Disclaimer ───────────────────────────────────────────────────────────
    story.append(HRFlowable(width="100%", thickness=1, color=BORDER, spaceBefore=4*mm))
    story.append(Paragraph(
        "⚠ Disclaimer: This report is generated by AI and is for informational purposes only. "
        "Please consult a qualified nutritionist or healthcare professional before making "
        "significant dietary changes, especially if you have medical conditions.",
        styles["Muted"]
    ))
    story.append(Spacer(1, 3*mm))
    story.append(Paragraph(
        f"Generated by NutriAgent AI | Powered by IBM Watsonx Granite | {today.strftime('%B %d, %Y')}",
        styles["Footer"]
    ))

    doc.build(story)
    buffer.seek(0)
    return buffer
