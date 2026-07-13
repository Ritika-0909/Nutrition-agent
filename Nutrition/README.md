# 🥗 NutriAgent AI

> **AI-Powered Nutrition Agent** built with Python Flask & IBM Watsonx.ai Granite Models

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.0.3-green.svg)](https://flask.palletsprojects.com)
[![IBM Watsonx](https://img.shields.io/badge/IBM-Watsonx.ai-0062FF.svg)](https://ibm.com/watsonx)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 🚀 Overview

NutriAgent AI is a comprehensive, production-ready nutrition web application that combines the power of **IBM Watsonx.ai Granite models** with a modern, responsive Flask frontend. It delivers personalized nutrition plans, calorie tracking, family diet management, BMI calculations, hydration goals, AI-powered recipe suggestions, and much more — all optimized for Indian cuisine and dietary habits.

---

## ✨ Features

### 🤖 AI-Powered Intelligence
- **Conversational Nutrition Chat** — Ask anything about food, diets, and wellness
- **Personalized Meal Plans** — 3-day, 7-day, 14-day, and 30-day AI-generated Indian meal plans
- **Food Calorie Analysis** — Detailed macro/micronutrient breakdown for any meal
- **AI Recipe Suggestions** — Healthy Indian recipes based on available ingredients
- **Grocery List Generation** — Weekly shopping lists tailored to meal plans
- **Hydration Goals** — Personalized water intake with reminders

### 📊 Health Tracking
- **Calorie & Macro Tracker** — Log meals with protein, carbs, fat, fiber
- **BMI Calculator** — Visual gauge with BMR and TDEE computation
- **Water Intake Tracker** — Daily hydration with 7-day history charts
- **Nutrition History** — Paginated log of all tracked meals
- **Progress Analytics** — Interactive Chart.js visualizations
- **PDF Reports** — Downloadable professional nutrition reports

### 👨‍👩‍👧‍👦 Family Nutrition Management
- **Multi-Profile Support** — Add unlimited family members
- **Individual Profiles** — Unique goals, allergies, and preferences per member
- **Family-Specific AI Chat** — Ask NutriAgent about any family member's nutrition
- **Relation Tracking** — Spouse, children, parents, grandparents

### 🔐 Security & Auth
- **Secure Authentication** — Bcrypt password hashing, Flask-Login sessions
- **Profile Management** — Full health profile with medical conditions, allergies
- **Session Security** — CSRF protection, secure cookies, HTTPOnly flags
- **Account Settings** — Password change, account deletion

### 🎨 Modern UI/UX
- **Dark Mode** — Persistent dark/light theme toggle
- **Responsive Design** — Mobile-first with Bootstrap 5.3
- **Smooth Animations** — CSS fade-in/up animations
- **Interactive Charts** — Chart.js bar, donut, and line charts
- **Quick Action Buttons** — One-click water logging, food tracking
- **Multilingual UI** — English, Hindi, Tamil, Telugu, Bengali, Marathi, Gujarati

---

## 🏗️ Project Structure

```
NutriAgent/
├── app.py                    # Flask application factory & core config
├── agent.py                  # ⭐ AGENT_INSTRUCTIONS + IBM Watsonx AI engine
├── models.py                 # SQLAlchemy database models
├── requirements.txt          # Python dependencies
├── .env.example              # Environment variables template
├── .env                      # Your local config (DO NOT COMMIT)
│
├── routes/
│   ├── __init__.py
│   ├── auth.py               # Register, login, logout, profile, settings
│   ├── nutrition.py          # Dashboard, chat, meal plans, BMI, tracker, hydration
│   ├── family.py             # Family member CRUD
│   └── api.py                # RESTful API (chat, logs, water, PDF, recipes)
│
├── utils/
│   ├── __init__.py
│   ├── pdf_generator.py      # ReportLab PDF report generation
│   └── preferences.py        # User preferences helper
│
├── templates/
│   ├── base.html             # Base layout (nav, flash, footer)
│   ├── index.html            # Landing page
│   ├── auth/                 # login, register, profile, settings
│   ├── nutrition/            # dashboard, chat, meal_plan, bmi_calculator,
│   │                         # calorie_tracker, history, hydration, recipes
│   ├── family/               # list, add_member
│   └── errors/               # 403, 404, 500
│
└── static/
    ├── css/app.css           # Complete UI with dark mode, animations
    └── js/app.js             # Dark mode, toasts, charts, interactions
```

---

## ⚙️ Customizing the Agent (AGENT_INSTRUCTIONS)

The heart of NutriAgent's AI behavior is defined in **[`agent.py`](agent.py)** inside the `AGENT_INSTRUCTIONS` dictionary. You can fully customize:

```python
# agent.py — Edit these sections:

AGENT_INSTRUCTIONS = {
    "name": "NutriAgent",
    "persona": "...",               # Agent's personality
    "tone": "warm, encouraging",    # Communication style
    "response_style": "...",        # How responses are formatted
    "diet_expertise": [...],        # List of diet specializations
    "indian_food_focus": {          # Indian cuisine preferences
        "enabled": True,
        "common_superfoods": [...], # Preferred ingredients
        "typical_meals": {...},     # Meal database
    },
    "safety_rules": [...],          # CRITICAL safety guidelines
    "response_formats": {...},      # Format templates per task type
    "supported_languages": {...},   # Multilingual mapping
    "fitness_goals": {...},         # Goal-specific macro splits
}
```

---

## 🛠️ Quick Start

### 1. Clone & Setup

```bash
git clone https://github.com/yourusername/nutriagent-ai.git
cd nutriagent-ai
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your IBM API credentials
```

```env
IBM_API_KEY=your-ibm-cloud-api-key
IBM_PROJECT_ID=your-watsonx-project-id
IBM_WATSONX_URL=https://us-south.ml.cloud.ibm.com
SECRET_KEY=your-super-secret-key
```

### 3. Get IBM Watsonx Credentials

1. Go to [cloud.ibm.com](https://cloud.ibm.com) → Create a free account
2. Create a **Watsonx.ai** service instance
3. Create a **Project** in Watson Studio
4. Generate an **API Key** from IAM → Service credentials
5. Copy your **Project ID** from the Watsonx.ai project settings

### 4. Run

```bash
python app.py
```

Open **http://localhost:5000** in your browser.

---

## 🌐 Deployment

### Deploy to Render (Free Tier)

1. Push your code to GitHub
2. Go to [render.com](https://render.com) → New Web Service
3. Connect your GitHub repository
4. Configure:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app --bind 0.0.0.0:$PORT`
   - **Environment:** Add all variables from `.env.example`
5. Click **Deploy**

### Deploy to IBM Code Engine / Cloud Foundry

```bash
# Install IBM Cloud CLI
ibmcloud login --sso
ibmcloud target --cf
ibmcloud cf push nutriagent-ai -b python_buildpack --no-start
ibmcloud cf set-env nutriagent-ai IBM_API_KEY your-key
ibmcloud cf set-env nutriagent-ai IBM_PROJECT_ID your-id
ibmcloud cf set-env nutriagent-ai SECRET_KEY your-secret
ibmcloud cf start nutriagent-ai
```

### Docker

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:5000", "--workers", "2"]
```

```bash
docker build -t nutriagent-ai .
docker run -p 5000:5000 --env-file .env nutriagent-ai
```

---

## 🔌 API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/chat` | AI nutrition chat |
| POST | `/api/nutrition/log` | Log a meal |
| DELETE | `/api/nutrition/log/<id>` | Delete log entry |
| GET | `/api/nutrition/today` | Today's nutrition totals |
| POST | `/api/water/log` | Log water intake |
| GET | `/api/water/today` | Today's water total |
| POST | `/api/meal-plan/generate` | Generate AI meal plan |
| DELETE | `/api/meal-plan/<id>` | Delete meal plan |
| POST | `/api/calculate/bmi` | Calculate BMI |
| POST | `/api/calculate/tdee` | Calculate TDEE |
| POST | `/api/calculate/hydration` | Calculate hydration goal |
| GET | `/api/report/pdf` | Download PDF report |
| POST | `/api/analyze/food` | AI food analysis |
| POST | `/api/recipe/suggest` | AI recipe suggestion |
| POST | `/api/chat/clear` | Clear chat history |

---

## 🛡️ Security Best Practices

- ✅ Bcrypt password hashing (12 rounds)
- ✅ CSRF protection via Flask-WTF
- ✅ HTTPOnly & SameSite cookies
- ✅ SQL injection prevention (SQLAlchemy ORM)
- ✅ User-scoped data access (all queries filtered by `user_id`)
- ✅ Environment variables for all secrets
- ✅ Input validation on all forms
- ✅ Rate-limiting configuration

---

## 📋 Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.11, Flask 3.0, SQLAlchemy 2.0 |
| AI Engine | IBM Watsonx.ai, Granite-13b-instruct |
| Database | SQLite (dev) / MySQL (prod) |
| Auth | Flask-Login, Flask-Bcrypt |
| PDF | ReportLab |
| Frontend | Bootstrap 5.3, Chart.js 4, Inter/Poppins |
| Deployment | Gunicorn, Render, IBM Cloud |

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit your changes: `git commit -m 'Add amazing feature'`
4. Push: `git push origin feature/amazing-feature`
5. Open a Pull Request

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

---

## 🙏 Acknowledgements

- [IBM Watsonx.ai](https://ibm.com/watsonx) for Granite foundation models
- [Flask](https://flask.palletsprojects.com) for the web framework
- [Bootstrap](https://getbootstrap.com) for the UI components
- [ReportLab](https://reportlab.com) for PDF generation
- [Chart.js](https://chartjs.org) for interactive charts

---

<div align="center">
  Made with ❤️ using IBM Watsonx.ai Granite
</div>
