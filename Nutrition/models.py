"""
Database models for NutriAgent AI
"""
from datetime import datetime, date
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from flask_bcrypt import Bcrypt

db = SQLAlchemy()
bcrypt = Bcrypt()


class User(UserMixin, db.Model):
    __tablename__ = "users"
    id                  = db.Column(db.Integer, primary_key=True)
    username            = db.Column(db.String(80), unique=True, nullable=False)
    email               = db.Column(db.String(120), unique=True, nullable=False)
    password_hash       = db.Column(db.String(256), nullable=False)
    full_name           = db.Column(db.String(120))
    avatar_color        = db.Column(db.String(20), default="#3b82d4")
    language            = db.Column(db.String(10), default="en")
    dark_mode           = db.Column(db.Boolean, default=False)
    created_at          = db.Column(db.DateTime, default=datetime.utcnow)
    last_login          = db.Column(db.DateTime)
    is_active           = db.Column(db.Boolean, default=True)

    # Relationships
    profile             = db.relationship("UserProfile", back_populates="user",
                                           uselist=False, cascade="all, delete-orphan")
    family_members      = db.relationship("FamilyMember", back_populates="user",
                                           cascade="all, delete-orphan")
    chat_messages       = db.relationship("ChatMessage", back_populates="user",
                                           cascade="all, delete-orphan")
    nutrition_logs      = db.relationship("NutritionLog", back_populates="user",
                                           cascade="all, delete-orphan")
    water_logs          = db.relationship("WaterLog", back_populates="user",
                                           cascade="all, delete-orphan")
    meal_plans          = db.relationship("MealPlan", back_populates="user",
                                           cascade="all, delete-orphan")

    def set_password(self, password: str):
        self.password_hash = bcrypt.generate_password_hash(password).decode("utf-8")

    def check_password(self, password: str) -> bool:
        return bcrypt.check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            "id": self.id, "username": self.username, "email": self.email,
            "full_name": self.full_name, "language": self.language,
            "dark_mode": self.dark_mode,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class UserProfile(db.Model):
    __tablename__ = "user_profiles"
    id                  = db.Column(db.Integer, primary_key=True)
    user_id             = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    age                 = db.Column(db.Integer)
    gender              = db.Column(db.String(20))
    weight_kg           = db.Column(db.Float)
    height_cm           = db.Column(db.Float)
    activity_level      = db.Column(db.String(30), default="moderate")
    fitness_goal        = db.Column(db.String(50), default="maintenance")
    dietary_preference  = db.Column(db.String(50), default="omnivore")
    allergies           = db.Column(db.Text, default="none")
    medical_conditions  = db.Column(db.Text, default="none")
    cuisine_preference  = db.Column(db.String(100), default="Indian")
    cooking_skill       = db.Column(db.String(20), default="intermediate")
    budget              = db.Column(db.String(20), default="medium")
    meals_per_day       = db.Column(db.Integer, default=3)
    sleep_hours         = db.Column(db.Float, default=7.5)
    stress_level        = db.Column(db.String(20), default="moderate")
    target_weight_kg    = db.Column(db.Float)
    target_calories     = db.Column(db.Integer)
    updated_at          = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = db.relationship("User", back_populates="profile")

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class FamilyMember(db.Model):
    __tablename__ = "family_members"
    id                  = db.Column(db.Integer, primary_key=True)
    user_id             = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    name                = db.Column(db.String(100), nullable=False)
    relation            = db.Column(db.String(50))
    age                 = db.Column(db.Integer)
    gender              = db.Column(db.String(20))
    weight_kg           = db.Column(db.Float)
    height_cm           = db.Column(db.Float)
    dietary_preference  = db.Column(db.String(50), default="omnivore")
    allergies           = db.Column(db.Text)
    medical_conditions  = db.Column(db.Text)
    fitness_goal        = db.Column(db.String(50), default="maintenance")
    avatar_color        = db.Column(db.String(20), default="#7c5cd8")
    notes               = db.Column(db.Text)
    created_at          = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", back_populates="family_members")

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class ChatMessage(db.Model):
    __tablename__ = "chat_messages"
    id              = db.Column(db.Integer, primary_key=True)
    user_id         = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    session_id      = db.Column(db.String(64))
    role            = db.Column(db.String(10), nullable=False)  # 'user' or 'assistant'
    content         = db.Column(db.Text, nullable=False)
    task_type       = db.Column(db.String(30), default="chat")
    member_id       = db.Column(db.Integer, db.ForeignKey("family_members.id"), nullable=True)
    created_at      = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", back_populates="chat_messages")

    def to_dict(self):
        return {
            "id": self.id, "role": self.role, "content": self.content,
            "task_type": self.task_type, "member_id": self.member_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class NutritionLog(db.Model):
    __tablename__ = "nutrition_logs"
    id          = db.Column(db.Integer, primary_key=True)
    user_id     = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    log_date    = db.Column(db.Date, default=date.today)
    meal_type   = db.Column(db.String(30))  # breakfast/lunch/dinner/snack
    food_name   = db.Column(db.String(200))
    calories    = db.Column(db.Float, default=0)
    protein_g   = db.Column(db.Float, default=0)
    carbs_g     = db.Column(db.Float, default=0)
    fat_g       = db.Column(db.Float, default=0)
    fiber_g     = db.Column(db.Float, default=0)
    notes       = db.Column(db.Text)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", back_populates="nutrition_logs")

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns
                if not isinstance(getattr(self, c.name), (datetime, date))} | {
            "log_date": self.log_date.isoformat() if self.log_date else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class WaterLog(db.Model):
    __tablename__ = "water_logs"
    id          = db.Column(db.Integer, primary_key=True)
    user_id     = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    log_date    = db.Column(db.Date, default=date.today)
    amount_ml   = db.Column(db.Integer, default=0)
    logged_at   = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", back_populates="water_logs")


class MealPlan(db.Model):
    __tablename__ = "meal_plans"
    id          = db.Column(db.Integer, primary_key=True)
    user_id     = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    member_id   = db.Column(db.Integer, db.ForeignKey("family_members.id"), nullable=True)
    plan_name   = db.Column(db.String(200))
    plan_data   = db.Column(db.Text)   # JSON string
    duration    = db.Column(db.String(20), default="7 days")
    is_active   = db.Column(db.Boolean, default=True)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", back_populates="meal_plans")

    def to_dict(self):
        return {
            "id": self.id, "plan_name": self.plan_name,
            "plan_data": self.plan_data, "duration": self.duration,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
