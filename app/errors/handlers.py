from flask import Blueprint, render_template, current_app

errors_bp = Blueprint('errors', __name__)

@errors_bp.app_errorhandler(404)
def not_found_error(error):
    """Handle 404 errors."""
    return render_template('errors/404.html'), 404

@errors_bp.app_errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    return render_template('errors/500.html'), 500 