"""
Additional preferences API endpoint — add to routes/api.py or standalone
"""
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from models import db

# This is already included in routes/api.py blueprint
# Adding as a standalone reference for the preferences endpoint


def register_preferences_route(api_bp):
    @api_bp.route("/preferences", methods=["POST"])
    @login_required
    def update_preferences():
        data = request.get_json(force=True) or {}
        if "dark_mode" in data:
            current_user.dark_mode = bool(data["dark_mode"])
            db.session.commit()
        return jsonify({"success": True})
