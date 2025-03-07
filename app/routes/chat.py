from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required, current_user
from app import db
from app.models.chat import Chat, Message
from app.utils.ai import generate_ai_response
from datetime import datetime
import os
from dotenv import load_dotenv

# Create blueprint with url_prefix
chat_bp = Blueprint('chat', __name__, url_prefix='/chat')

@chat_bp.route('/test')
def test():
    """Test route to check if routing is working."""
    return "路由系统正常工作！"

@chat_bp.route('/')
@login_required
def index():
    """Render the main chat page."""
    # Get all chats for the current user
    chats = Chat.query.filter_by(user_id=current_user.id).order_by(Chat.updated_at.desc()).all()
    
    # Get the active chat or create a new one if none exists
    active_chat_id = request.args.get('chat_id')
    active_chat = None
    
    if active_chat_id:
        active_chat = Chat.query.filter_by(id=active_chat_id, user_id=current_user.id).first()
    
    if not active_chat and chats:
        active_chat = chats[0]
    
    if not active_chat:
        # Create a new chat
        active_chat = Chat(user_id=current_user.id)
        db.session.add(active_chat)
        db.session.commit()
        chats = [active_chat]
    
    # Get messages for the active chat
    messages = Message.query.filter_by(chat_id=active_chat.id).order_by(Message.created_at).all()
    
    return render_template('chat.html', 
                          title='豆包AI聊天', 
                          chats=chats, 
                          active_chat=active_chat, 
                          messages=messages)

@chat_bp.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    """Render and handle the settings page."""
    # Load current settings from config
    current_model = current_app.config.get('AI_MODEL_TYPE', 'openai')
    openai_api_key = current_app.config.get('OPENAI_API_KEY', '')
    deepseek_api_key = current_app.config.get('DEEPSEEK_API_KEY', '')
    deepseek_api_url = current_app.config.get('DEEPSEEK_API_URL', 'https://api.deepseek.com/v1/chat/completions')
    deepseek_model = current_app.config.get('DEEPSEEK_MODEL', 'deepseek-chat')
    siliconflow_api_key = current_app.config.get('SILICONFLOW_API_KEY', '')
    siliconflow_api_url = current_app.config.get('SILICONFLOW_API_URL', 'https://api.siliconflow.com/v1/chat/completions')
    siliconflow_model = current_app.config.get('SILICONFLOW_MODEL', 'siliconflow-7b-chat')
    
    if request.method == 'POST':
        # Get form data
        ai_model_type = request.form.get('ai_model_type', 'openai')
        openai_api_key_new = request.form.get('openai_api_key', '')
        deepseek_api_key_new = request.form.get('deepseek_api_key', '')
        deepseek_api_url_new = request.form.get('deepseek_api_url', 'https://api.deepseek.com/v1/chat/completions')
        deepseek_model_new = request.form.get('deepseek_model', 'deepseek-chat')
        siliconflow_api_key_new = request.form.get('siliconflow_api_key', '')
        siliconflow_api_url_new = request.form.get('siliconflow_api_url', 'https://api.siliconflow.com/v1/chat/completions')
        siliconflow_model_new = request.form.get('siliconflow_model', 'siliconflow-7b-chat')
        
        # Update .env file
        env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), '.env')
        
        # Read existing .env file
        env_vars = {}
        if os.path.exists(env_path):
            with open(env_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        env_vars[key] = value
        
        # Update values
        env_vars['AI_MODEL_TYPE'] = ai_model_type
        if openai_api_key_new:
            env_vars['OPENAI_API_KEY'] = openai_api_key_new
        if deepseek_api_key_new:
            env_vars['DEEPSEEK_API_KEY'] = deepseek_api_key_new
        env_vars['DEEPSEEK_API_URL'] = deepseek_api_url_new
        env_vars['DEEPSEEK_MODEL'] = deepseek_model_new
        if siliconflow_api_key_new:
            env_vars['SILICONFLOW_API_KEY'] = siliconflow_api_key_new
        env_vars['SILICONFLOW_API_URL'] = siliconflow_api_url_new
        env_vars['SILICONFLOW_MODEL'] = siliconflow_model_new
        
        # Write back to .env file
        with open(env_path, 'w') as f:
            for key, value in env_vars.items():
                f.write(f"{key}={value}\n")
        
        # Reload environment variables
        load_dotenv(env_path, override=True)
        
        # Update application config
        current_app.config['AI_MODEL_TYPE'] = ai_model_type
        if openai_api_key_new:
            current_app.config['OPENAI_API_KEY'] = openai_api_key_new
        if deepseek_api_key_new:
            current_app.config['DEEPSEEK_API_KEY'] = deepseek_api_key_new
        current_app.config['DEEPSEEK_API_URL'] = deepseek_api_url_new
        current_app.config['DEEPSEEK_MODEL'] = deepseek_model_new
        if siliconflow_api_key_new:
            current_app.config['SILICONFLOW_API_KEY'] = siliconflow_api_key_new
        current_app.config['SILICONFLOW_API_URL'] = siliconflow_api_url_new
        current_app.config['SILICONFLOW_MODEL'] = siliconflow_model_new
        
        # Update local variables for template
        current_model = ai_model_type
        if openai_api_key_new:
            openai_api_key = openai_api_key_new
        if deepseek_api_key_new:
            deepseek_api_key = deepseek_api_key_new
        deepseek_api_url = deepseek_api_url_new
        deepseek_model = deepseek_model_new
        if siliconflow_api_key_new:
            siliconflow_api_key = siliconflow_api_key_new
        siliconflow_api_url = siliconflow_api_url_new
        siliconflow_model = siliconflow_model_new
        
        flash('设置已保存', 'success')
    
    return render_template('settings.html',
                          title='设置 - 豆包AI聊天',
                          current_model=current_model,
                          openai_api_key=openai_api_key,
                          deepseek_api_key=deepseek_api_key,
                          deepseek_api_url=deepseek_api_url,
                          deepseek_model=deepseek_model,
                          siliconflow_api_key=siliconflow_api_key,
                          siliconflow_api_url=siliconflow_api_url,
                          siliconflow_model=siliconflow_model)

@chat_bp.route('/new', methods=['POST'])
@login_required
def new_chat():
    """Create a new chat."""
    chat = Chat(user_id=current_user.id)
    db.session.add(chat)
    db.session.commit()
    
    return redirect(url_for('chat.index', chat_id=chat.id))

@chat_bp.route('/<int:chat_id>/rename', methods=['POST'])
@login_required
def rename_chat(chat_id):
    """Rename a chat."""
    chat = Chat.query.filter_by(id=chat_id, user_id=current_user.id).first_or_404()
    
    title = request.form.get('title')
    if title:
        chat.title = title
        db.session.commit()
        return jsonify({'success': True})
    
    return jsonify({'success': False, 'error': '标题不能为空'}), 400

@chat_bp.route('/<int:chat_id>/delete', methods=['POST'])
@login_required
def delete_chat(chat_id):
    """Delete a chat."""
    chat = Chat.query.filter_by(id=chat_id, user_id=current_user.id).first_or_404()
    
    db.session.delete(chat)
    db.session.commit()
    
    return redirect(url_for('chat.index'))

@chat_bp.route('/<int:chat_id>/message', methods=['POST'])
@login_required
def send_message(chat_id):
    """Send a message to the chat."""
    try:
        chat = Chat.query.filter_by(id=chat_id, user_id=current_user.id).first_or_404()
        
        content = request.form.get('content')
        if not content:
            return jsonify({'success': False, 'error': '消息不能为空'}), 400
        
        # Create user message
        user_message = Message(chat_id=chat.id, role='user', content=content)
        db.session.add(user_message)
        
        # Update chat timestamp
        chat.updated_at = datetime.utcnow()
        
        # If this is the first message, update the chat title
        if chat.title == '新对话' and Message.query.filter_by(chat_id=chat.id).count() == 0:
            # Use the first 20 characters of the message as the title
            chat.title = content[:20] + ('...' if len(content) > 20 else '')
        
        db.session.commit()
        
        # Generate AI response
        ai_response = generate_ai_response(chat.id, content)
        
        # Check if the AI response indicates an error
        if "API密钥未配置" in ai_response:
            return jsonify({
                'success': False, 
                'error': ai_response,
                'error_type': 'api_key_missing'
            }), 400
            
        if "API调用失败" in ai_response or "API请求失败" in ai_response:
            return jsonify({
                'success': False, 
                'error': ai_response,
                'error_type': 'api_call_failed'
            }), 400
            
        if "API请求超时" in ai_response:
            return jsonify({
                'success': False, 
                'error': ai_response,
                'error_type': 'api_timeout'
            }), 408
            
        if "API连接错误" in ai_response:
            return jsonify({
                'success': False, 
                'error': ai_response,
                'error_type': 'api_connection_error'
            }), 503
        
        # Create AI message
        ai_message = Message(chat_id=chat.id, role='assistant', content=ai_response)
        db.session.add(ai_message)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'user_message': {
                'id': user_message.id,
                'content': user_message.content,
                'created_at': user_message.created_at.isoformat()
            },
            'ai_message': {
                'id': ai_message.id,
                'content': ai_message.content,
                'created_at': ai_message.created_at.isoformat()
            }
        })
    except Exception as e:
        # Log the error
        print(f"Error in send_message: {str(e)}")
        return jsonify({'success': False, 'error': f'发送消息时出现错误: {str(e)}'}), 500 