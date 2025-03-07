import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Base configuration class."""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-key-for-development-only')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # AI Model Configuration
    AI_MODEL_TYPE = os.environ.get('AI_MODEL_TYPE', 'openai')  # 'openai', 'deepseek', or 'siliconflow'
    
    # OpenAI Configuration
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
    
    # DeepSeek Configuration
    DEEPSEEK_API_KEY = os.environ.get('DEEPSEEK_API_KEY')
    DEEPSEEK_API_URL = os.environ.get('DEEPSEEK_API_URL', 'https://api.deepseek.com/v1/chat/completions')
    DEEPSEEK_MODEL = os.environ.get('DEEPSEEK_MODEL', 'deepseek-chat')
    
    # 硅谷流动 Configuration
    SILICONFLOW_API_KEY = os.environ.get('SILICONFLOW_API_KEY')
    SILICONFLOW_API_URL = os.environ.get('SILICONFLOW_API_URL', 'https://api.siliconflow.com/v1/chat/completions')
    SILICONFLOW_MODEL = os.environ.get('SILICONFLOW_MODEL', 'siliconflow-7b-chat')
    
class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    
class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    
class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    
# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

def get_config():
    """Return the appropriate configuration object based on the environment."""
    config_name = os.environ.get('FLASK_ENV', 'default')
    return config.get(config_name, config['default']) 