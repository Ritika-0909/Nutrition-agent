"""
╔══════════════════════════════════════════════════════════════════════╗
║          NutriAgent AI — Agent Instructions & Core Logic             ║
║  Edit the AGENT_INSTRUCTIONS dict below to fully customize behavior  ║
╚══════════════════════════════════════════════════════════════════════╝
"""

import os
import logging
from ibm_watsonx_ai import Credentials
from ibm_watsonx_ai.foundation_models import ModelInference
from ibm_watsonx_ai.metanames import GenTextParamsMetaNames as GenParams

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════
#  AGENT INSTRUCTIONS — Customize everything about the agent here
# ═══════════════════════════════════════════════════════════════════════════
AGENT_INSTRUCTIONS = {

    # ── Identity & Persona ──────────────────────────────────────────────────
    "name": "NutriAgent",
    "persona": (
        "You are NutriAgent, a compassionate, knowledgeable, and friendly AI-powered "
        "nutrition expert and wellness coach. You speak with warmth, clarity, and "
        "encouragement — like a trusted health friend, not a clinical robot."
    ),

    # ── Tone & Communication Style ──────────────────────────────────────────
    "tone": "warm, encouraging, professional, empathetic",
    "response_style": (
        "Use clear headings, bullet points, and emojis sparingly for readability. "
        "Always be concise but complete. Start with empathy, then provide actionable advice. "
        "End with a motivating note or a simple next step. Avoid medical jargon. "
        "If a user seems overwhelmed, simplify and offer one step at a time."
    ),

    # ── Diet Specialization ─────────────────────────────────────────────────
    "diet_expertise": [
        "Indian regional cuisines (North Indian, South Indian, Gujarati, Bengali, Maharashtrian)",
        "Vegetarian and vegan nutrition",
        "Diabetic-friendly diets",
        "Heart-healthy and DASH diets",
        "Weight-loss (calorie deficit) plans",
        "Muscle-gain (high-protein) plans",
        "PCOS/hormonal balance diets",
        "Gluten-free and allergen-aware nutrition",
        "Child and adolescent nutrition",
        "Senior and elderly dietary needs",
        "Prenatal and postpartum nutrition",
        "Intermittent fasting and time-restricted eating",
        "Mediterranean diet",
        "Keto and low-carb approaches",
    ],

    # ── Indian Food Preferences ─────────────────────────────────────────────
    "indian_food_focus": {
        "enabled": True,
        "prefer_local_ingredients": True,
        "common_superfoods": [
            "Turmeric (haldi)", "Amla (Indian gooseberry)", "Moringa (drumstick leaves)",
            "Ghee (in moderation)", "Coconut oil", "Sesame seeds (til)", "Flaxseeds (alsi)",
            "Fenugreek (methi)", "Bitter gourd (karela)", "Drumstick (sahjan)",
            "Millet (bajra, jowar, ragi)", "Lentils (dal — moong, masoor, chana)",
            "Paneer (low-fat)", "Curd/Yogurt (dahi)", "Jaggery (gur) over sugar",
        ],
        "typical_meals": {
            "breakfast": ["Poha", "Upma", "Idli-Sambar", "Paratha with curd", "Sprouted moong chaat",
                          "Ragi porridge", "Oats khichdi"],
            "lunch": ["Dal-chawal", "Rajma-chawal", "Roti-sabzi", "Chole bhature (occasional)",
                      "Sambar rice", "Khichdi", "Pulao with raita"],
            "dinner": ["Light khichdi", "Roti with dal tadka", "Vegetable soup with multigrain roti",
                       "Dalia", "Moong dal chilla"],
            "snacks": ["Makhana", "Roasted chana", "Fruits", "Buttermilk", "Sprout chaat",
                       "Murmura bhel (healthy)", "Handful of dry fruits"],
        },
        "regional_consideration": True,
        "seasonal_ingredients": True,
    },

    # ── Safety Rules (Critical — Do NOT weaken these) ───────────────────────
    "safety_rules": [
        "NEVER diagnose medical conditions. Always recommend consulting a qualified doctor or dietitian.",
        "NEVER prescribe medications, supplements beyond general dietary advice, or specific doses.",
        "ALWAYS flag if user mentions symptoms that may need urgent medical attention.",
        "NEVER recommend extreme calorie restriction (below 1200 kcal/day for women, 1500 kcal/day for men).",
        "NEVER encourage disordered eating behaviors (purging, extreme fasting, etc.).",
        "ALWAYS acknowledge allergies and medical conditions provided by the user.",
        "For children under 2, ALWAYS advise consulting a pediatrician before dietary changes.",
        "NEVER share personally identifiable information beyond what the user provides for their session.",
        "If asked about topics outside nutrition/wellness, politely redirect to your expertise.",
    ],

    # ── Response Templates & Formats ────────────────────────────────────────
    "response_formats": {
        "meal_plan": (
            "Present as: Day-by-Day table with Breakfast | Lunch | Dinner | Snacks columns. "
            "Include approximate calories per meal. Add a weekly summary with total macros."
        ),
        "calorie_analysis": (
            "Show: Total calories, Protein (g), Carbs (g), Fat (g), Fiber (g). "
            "Compare to daily recommended intake. Flag deficiencies or excesses."
        ),
        "grocery_list": (
            "Group by category: Vegetables, Fruits, Grains & Cereals, Protein Sources, "
            "Dairy, Spices & Condiments, Healthy Fats. Include quantities for 1 week."
        ),
        "hydration_goal": (
            "Calculate using weight (kg) × 30–35 ml. Adjust for activity level, climate, "
            "health conditions. Break into hourly/reminder schedule."
        ),
        "recipe": (
            "Include: Ingredients list, Step-by-step instructions (numbered), "
            "Prep time, Cook time, Servings, Nutrition per serving (calories, protein, carbs, fat)."
        ),
    },

    # ── Multilingual Support ─────────────────────────────────────────────────
    "supported_languages": {
        "en": "English",
        "hi": "Hindi",
        "ta": "Tamil",
        "te": "Telugu",
        "bn": "Bengali",
        "mr": "Marathi",
        "gu": "Gujarati",
        "kn": "Kannada",
        "ml": "Malayalam",
        "pa": "Punjabi",
    },
    "language_instruction": (
        "Detect the user's language from their message. "
        "If they write in Hindi, respond in Hindi. "
        "If they write in Tamil, respond in Tamil. "
        "Always match the user's language unless explicitly asked to use another language."
    ),

    # ── Personalization Factors ──────────────────────────────────────────────
    "personalization_factors": [
        "age", "gender", "weight_kg", "height_cm", "activity_level",
        "fitness_goal", "dietary_preference", "allergies", "medical_conditions",
        "cuisine_preference", "cooking_skill", "budget", "family_size",
        "meal_frequency", "sleep_hours", "stress_level",
    ],

    # ── Fitness Goals Mapping ────────────────────────────────────────────────
    "fitness_goals": {
        "weight_loss": {
            "calorie_adjustment": "-500 kcal from TDEE",
            "macro_split": "40% carbs, 30% protein, 30% fat",
            "focus": "High fiber, lean protein, low-GI foods, portion control",
        },
        "muscle_gain": {
            "calorie_adjustment": "+300 to +500 kcal from TDEE",
            "macro_split": "40% carbs, 35% protein, 25% fat",
            "focus": "High protein (1.6–2.2g/kg body weight), complex carbs, healthy fats",
        },
        "maintenance": {
            "calorie_adjustment": "TDEE (no surplus/deficit)",
            "macro_split": "50% carbs, 25% protein, 25% fat",
            "focus": "Balanced, whole-food diet, micronutrient coverage",
        },
        "diabetes_management": {
            "calorie_adjustment": "Calculated based on weight goal",
            "macro_split": "45% low-GI carbs, 25% protein, 30% fat",
            "focus": "Glycemic control, portion sizes, fiber, avoid refined sugars",
        },
        "heart_health": {
            "calorie_adjustment": "Calculated based on weight goal",
            "macro_split": "55% carbs, 20% protein, 25% healthy fats",
            "focus": "Omega-3, fiber, potassium, sodium restriction, antioxidants",
        },
    },

    # ── System Prompt Template ───────────────────────────────────────────────
    "system_prompt_template": (
        "{persona}\n\n"
        "EXPERTISE: {diet_expertise_list}\n\n"
        "TONE: {tone}\n\n"
        "STYLE: {response_style}\n\n"
        "SAFETY: Always follow these rules:\n{safety_rules_list}\n\n"
        "LANGUAGE: {language_instruction}\n\n"
        "When the user provides profile data (age, weight, goals, etc.), "
        "use it to personalize every response. Always be specific and actionable.\n"
        "Current user profile: {user_profile}\n"
        "Conversation history context: {chat_history}\n"
    ),
}
# ═══════════════════════════════════════════════════════════════════════════
#  END OF AGENT_INSTRUCTIONS
# ═══════════════════════════════════════════════════════════════════════════


class NutriAgentAI:
    """Core AI engine wrapping IBM Watsonx Granite model."""

    # Possible init_status values: "ok" | "no_credentials" | "project_not_found" | "auth_error" | "error"
    init_status  : str = "no_credentials"
    init_error   : str = ""

    def __init__(self):
        self.api_key     = os.getenv("IBM_API_KEY", "").strip()
        self.project_id  = os.getenv("IBM_PROJECT_ID", "").strip()
        self.watsonx_url = os.getenv("IBM_WATSONX_URL", "https://us-south.ml.cloud.ibm.com").strip()
        self.model_id    = os.getenv("GRANITE_MODEL_ID", "ibm/granite-13b-instruct-v2").strip()
        # Model is created lazily on first use — avoids blocking startup on network calls
        self._model      = None
        self._params     = None
        self._creds      = None
        self.init_status  = "no_credentials" if not (self.api_key and self.project_id) else "pending"
        self.init_error   = ""
        if not self.api_key or not self.project_id:
            msg = ("IBM_API_KEY" if not self.api_key else "IBM_PROJECT_ID") + " is missing in .env"
            logger.warning(msg)
            self.init_error = msg
        else:
            # Pre-build params so they're ready at first call
            self._params = {
                GenParams.MAX_NEW_TOKENS:     int(os.getenv("MAX_NEW_TOKENS", 1200)),
                GenParams.TEMPERATURE:        float(os.getenv("TEMPERATURE", 0.7)),
                GenParams.TOP_P:              float(os.getenv("TOP_P", 0.9)),
                GenParams.TOP_K:              int(os.getenv("TOP_K", 50)),
                GenParams.REPETITION_PENALTY: float(os.getenv("REPETITION_PENALTY", 1.1)),
                GenParams.STOP_SEQUENCES:     ["Human:", "User:"],
            }
            logger.info(f"NutriAgent AI ready (lazy init) — model: {self.model_id}")

    @property
    def model(self):
        """Lazily create the ModelInference object on first access."""
        if self._model is not None:
            return self._model
        if self.init_status in ("no_credentials", "project_not_found", "auth_error"):
            return None
        if not self.api_key or not self.project_id:
            return None
        try:
            self._creds = Credentials(url=self.watsonx_url, api_key=self.api_key)
            self._model = ModelInference(
                model_id=self.model_id,
                credentials=self._creds,
                project_id=self.project_id,
                params=self._params,
            )
            self.init_status = "ok"
            logger.info(f"NutriAgent AI connected: {self.model_id}")
            return self._model
        except Exception as e:
            err_str = str(e)
            logger.error(f"Watsonx model init error: {err_str}")
            self.init_error = err_str
            if "404" in err_str or "not_found" in err_str or "Not Found" in err_str:
                self.init_status = "project_not_found"
            elif "401" in err_str or "403" in err_str or "Unauthorized" in err_str:
                self.init_status = "auth_error"
            else:
                self.init_status = "error"
            return None

    def _build_system_prompt(self, user_profile: dict, chat_history: list) -> str:
        instr = AGENT_INSTRUCTIONS
        safety_list = "\n".join(f"  - {r}" for r in instr["safety_rules"])
        expertise_list = ", ".join(instr["diet_expertise"][:6]) + ", and more."
        history_text = ""
        for msg in chat_history[-4:]:  # last 4 exchanges for context
            role = "User" if msg.get("role") == "user" else "NutriAgent"
            history_text += f"{role}: {msg.get('content', '')}\n"
        profile_text = (
            f"Name: {user_profile.get('name', 'User')}, "
            f"Age: {user_profile.get('age', 'N/A')}, "
            f"Weight: {user_profile.get('weight_kg', 'N/A')} kg, "
            f"Height: {user_profile.get('height_cm', 'N/A')} cm, "
            f"Goal: {user_profile.get('fitness_goal', 'maintenance')}, "
            f"Diet: {user_profile.get('dietary_preference', 'omnivore')}, "
            f"Allergies: {user_profile.get('allergies', 'none')}, "
            f"Conditions: {user_profile.get('medical_conditions', 'none')}, "
            f"Activity: {user_profile.get('activity_level', 'moderate')}"
        )
        return instr["system_prompt_template"].format(
            persona=instr["persona"],
            diet_expertise_list=expertise_list,
            tone=instr["tone"],
            response_style=instr["response_style"],
            safety_rules_list=safety_list,
            language_instruction=instr["language_instruction"],
            user_profile=profile_text,
            chat_history=history_text or "No prior conversation.",
        )

    def generate_response(self, user_message: str, user_profile: dict = None,
                          chat_history: list = None, task_type: str = "chat") -> str:
        if user_profile is None:
            user_profile = {}
        if chat_history is None:
            chat_history = []

        system_prompt = self._build_system_prompt(user_profile, chat_history)

        # Task-specific format hints
        format_hints = AGENT_INSTRUCTIONS["response_formats"]
        task_hint = ""
        if task_type in format_hints:
            task_hint = f"\nFORMAT INSTRUCTIONS: {format_hints[task_type]}\n"

        full_prompt = (
            f"{system_prompt}\n"
            f"{task_hint}\n"
            f"Human: {user_message}\n"
            f"NutriAgent:"
        )

        if self.model is None:
            return self._fallback_response(task_type)

        try:
            result = self.model.generate_text(prompt=full_prompt)
            response = result.strip() if isinstance(result, str) else str(result).strip()
            if not response:
                return self._fallback_response(task_type)
            # Successful generation — mark OK and reset any prior error
            self.init_status = "ok"
            self.init_error  = ""
            return response
        except Exception as e:
            err_str = str(e)
            logger.error(f"AI generation error: {err_str}")
            self._classify_error(err_str)
            return self._fallback_response(task_type)

    def _classify_error(self, err_str: str):
        """Classify an IBM error string into init_status and store it."""
        self.init_error = err_str
        if "not_found" in err_str or "Not Found" in err_str or '"code":404' in err_str or "404" in err_str:
            self.init_status = "project_not_found"
        elif "Inactive" in err_str or "invalid_instance_status" in err_str:
            self.init_status = "wml_inactive"
        elif "401" in err_str or "403" in err_str or "Unauthorized" in err_str or "forbidden" in err_str.lower():
            self.init_status = "auth_error"
        elif "not supported" in err_str or "Supported models" in err_str:
            self.init_status = "model_not_supported"
        else:
            self.init_status = "error"

    def _fallback_response(self, task_type: str = "chat") -> str:
        """Return a specific, actionable message based on what actually went wrong."""
        status = self.init_status

        if status == "project_not_found":
            reason = (
                "⚠️ **IBM Watsonx Project Not Found**\n\n"
                "Your Project ID returned 404. Steps to fix:\n\n"
                "1. Run `python check_project.py` — it lists all valid Project IDs\n"
                "2. Copy the correct ID\n"
                "3. Open `.env` and set `IBM_PROJECT_ID=<the correct id>`\n"
                "4. Restart with `python app.py`"
            )
        elif status == "wml_inactive":
            reason = (
                "⚠️ **Watson Machine Learning Instance is Inactive**\n\n"
                "Your WML service instance is suspended. Steps to fix:\n\n"
                "1. Go to [cloud.ibm.com/resources](https://cloud.ibm.com/resources)\n"
                "2. Find your **Watson Machine Learning** instance\n"
                "3. Click on it → if it shows 'Inactive', click **Resume** or **Upgrade**\n"
                "4. Wait ~2 minutes for it to become active\n"
                "5. Come back and send a message again"
            )
        elif status == "model_not_supported":
            reason = (
                "⚠️ **Model Not Available on This Project**\n\n"
                "The configured model is not supported by your WML instance. Steps:\n\n"
                "1. Run `python check_project.py` to find a working project\n"
                "2. Open `.env` and try `GRANITE_MODEL_ID=ibm/granite-3-1-8b-base`\n"
                "3. Restart with `python app.py`"
            )
        elif status == "auth_error":
            reason = (
                "⚠️ **IBM API Key Invalid or Expired**\n\n"
                "Authentication failed (401/403). Steps:\n\n"
                "1. Go to [cloud.ibm.com/iam/apikeys](https://cloud.ibm.com/iam/apikeys)\n"
                "2. Create a new API key\n"
                "3. Set `IBM_API_KEY=<new key>` in your `.env` file\n"
                "4. Restart with `python app.py`"
            )
        elif status == "no_credentials":
            reason = (
                "⚠️ **IBM Credentials Not Configured**\n\n"
                "The `.env` file is missing. Steps:\n\n"
                "1. Run: `copy .env.example .env` in your terminal\n"
                "2. Open `.env` and fill in `IBM_API_KEY` and `IBM_PROJECT_ID`\n"
                "3. Restart with `python app.py`"
            )
        else:
            reason = (
                "⚠️ **AI Engine Unavailable**\n\n"
                f"Error: `{self.init_error[:200] if self.init_error else 'Unknown error'}`\n\n"
                "Check the `nutriagent.log` file for details, then restart with `python app.py`."
            )

        task_prefixes = {
            "meal_plan":        "**Meal Plan generation requires IBM Watsonx AI.**\n\n",
            "calorie_analysis":  "**Calorie Analysis requires IBM Watsonx AI.**\n\n",
            "grocery_list":      "**Grocery List generation requires IBM Watsonx AI.**\n\n",
            "recipe":            "**Recipe suggestions require IBM Watsonx AI.**\n\n",
            "hydration_goal":    "**Hydration advice requires IBM Watsonx AI.**\n\n",
        }
        prefix = task_prefixes.get(task_type, "")
        return prefix + reason

    def calculate_bmr(self, weight_kg: float, height_cm: float,
                      age: int, gender: str) -> float:
        """Mifflin-St Jeor BMR formula."""
        if gender.lower() in ("male", "m"):
            return 10 * weight_kg + 6.25 * height_cm - 5 * age + 5
        else:
            return 10 * weight_kg + 6.25 * height_cm - 5 * age - 161

    def calculate_tdee(self, bmr: float, activity_level: str) -> float:
        multipliers = {
            "sedentary": 1.2, "light": 1.375,
            "moderate": 1.55, "active": 1.725, "very_active": 1.9,
        }
        return bmr * multipliers.get(activity_level, 1.55)

    def calculate_bmi(self, weight_kg: float, height_cm: float) -> dict:
        height_m = height_cm / 100
        bmi = weight_kg / (height_m ** 2)
        if bmi < 18.5:
            category, color = "Underweight", "#3b82f6"
        elif bmi < 25.0:
            category, color = "Normal weight", "#22c55e"
        elif bmi < 30.0:
            category, color = "Overweight", "#f59e0b"
        else:
            category, color = "Obese", "#ef4444"
        return {"bmi": round(bmi, 1), "category": category, "color": color}

    def calculate_hydration(self, weight_kg: float, activity_level: str,
                            climate: str = "temperate") -> dict:
        base_ml = weight_kg * 33
        activity_bonus = {"sedentary": 0, "light": 200, "moderate": 400,
                          "active": 600, "very_active": 800}.get(activity_level, 0)
        climate_bonus = {"hot": 500, "tropical": 600, "temperate": 0, "cold": -100}.get(climate, 0)
        total_ml = base_ml + activity_bonus + climate_bonus
        return {
            "total_ml":   round(total_ml),
            "total_L":    round(total_ml / 1000, 1),
            "glasses_8oz": round(total_ml / 240),
            "hourly_ml":  round(total_ml / 16),  # 16 waking hours
        }


# Module-level singleton
_agent_instance = None

def get_agent() -> NutriAgentAI:
    global _agent_instance
    if _agent_instance is None:
        _agent_instance = NutriAgentAI()
    return _agent_instance
