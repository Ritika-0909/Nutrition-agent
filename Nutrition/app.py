"""
╔══════════════════════════════════════════════════════════════════════╗
║           NutriAgent AI — Main Flask Application                     ║
║           IBM Watsonx.ai + Granite Models                            ║
╚══════════════════════════════════════════════════════════════════════╝
"""

import os
import logging
from datetime import datetime
from flask import Flask, render_template, redirect, url_for, flash, session
from flask_login import LoginManager, current_user
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()

# ── Configure logging ────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("nutriagent.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)

# ── Application factory ──────────────────────────────────────────────────────

def create_app() -> Flask:
    app = Flask(__name__)

    # Core config
    app.config["SECRET_KEY"]            = os.getenv("SECRET_KEY", "dev-secret-change-me")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", "sqlite:///nutriagent.db")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {"pool_recycle": 280, "pool_pre_ping": True}
    app.config["WTF_CSRF_ENABLED"]      = True
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    app.config["REMEMBER_COOKIE_DURATION"] = int(os.getenv("REMEMBER_COOKIE_DURATION", 2592000))

    # Mail config
    app.config["MAIL_SERVER"]   = os.getenv("MAIL_SERVER", "smtp.gmail.com")
    app.config["MAIL_PORT"]     = int(os.getenv("MAIL_PORT", 587))
    app.config["MAIL_USE_TLS"]  = os.getenv("MAIL_USE_TLS", "True") == "True"
    app.config["MAIL_USERNAME"] = os.getenv("MAIL_USERNAME")
    app.config["MAIL_PASSWORD"] = os.getenv("MAIL_PASSWORD")

    # ── Initialize extensions ────────────────────────────────────────────────
    from models import db, bcrypt
    db.init_app(app)
    bcrypt.init_app(app)
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Please log in to access NutriAgent AI."
    login_manager.login_message_category = "info"

    @login_manager.user_loader
    def load_user(user_id):
        from models import User
        return db.session.get(User, int(user_id))

    # ── Register blueprints ──────────────────────────────────────────────────
    from routes.auth      import auth_bp
    from routes.nutrition import nutrition_bp
    from routes.family    import family_bp
    from routes.api       import api_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(nutrition_bp)
    app.register_blueprint(family_bp)
    app.register_blueprint(api_bp, url_prefix="/api")

    # ── Core routes ──────────────────────────────────────────────────────────
    @app.route("/")
    def index():
        if current_user.is_authenticated:
            return redirect(url_for("nutrition.dashboard"))
        return render_template("index.html")

    @app.route("/health")
    def health():
        return {"status": "ok", "app": "NutriAgent AI", "timestamp": datetime.utcnow().isoformat()}

    # ── Context processors ───────────────────────────────────────────────────
    @app.context_processor
    def inject_globals():
        return {
            "app_name": "NutriAgent AI",
            "current_year": datetime.utcnow().year,
        }

    # ── Error handlers ───────────────────────────────────────────────────────
    @app.errorhandler(404)
    def not_found(e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def server_error(e):
        logger.error(f"Server error: {e}")
        return render_template("errors/500.html"), 500

    @app.errorhandler(403)
    def forbidden(e):
        return render_template("errors/403.html"), 403

    # ── Database initialization ──────────────────────────────────────────────
    with app.app_context():
        db.create_all()
        logger.info("Database tables created/verified.")

    return app


app = create_app()

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("FLASK_DEBUG", "True") == "True"
    logger.info(f"Starting NutriAgent AI on port {port} (debug={debug})")
    app.run(host="0.0.0.0", port=port, debug=debug)
