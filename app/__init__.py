from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect, generate_csrf
from app.config import get_config

# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()
csrf = CSRFProtect()

def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(get_config())
    
    # Initialize extensions with app
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    
    login_manager.login_view = 'auth.login'
    login_manager.login_message = '请先登录以访问此页面'
    login_manager.login_message_category = 'info'
    
    # 添加上下文处理器，自动将current_model变量添加到所有模板中
    @app.context_processor
    def inject_current_model():
        return {'current_model': app.config.get('AI_MODEL_TYPE', 'openai')}
    
    # 添加上下文处理器，提供csrf_token变量
    @app.context_processor
    def inject_csrf_token():
        return {'csrf_token': generate_csrf()}
    
    with app.app_context():
        # Import and register blueprints
        from app.routes.auth import auth_bp
        from app.routes.chat import chat_bp
        from app.errors.handlers import errors_bp
        
        app.register_blueprint(auth_bp)
        app.register_blueprint(chat_bp)
        app.register_blueprint(errors_bp)
        
        # Create database tables if they don't exist
        # Note: When using Flask-Migrate, you should use migrations instead
        # db.create_all()
        
        return app 