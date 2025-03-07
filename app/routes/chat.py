from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required, current_user
from app import db
from app.models.chat import Chat, Message
from app.utils.ai import generate_ai_response
from datetime import datetime
import os
from dotenv import load_dotenv
import requests
import json

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
    
    # Get current model type from config
    current_model = current_app.config.get('AI_MODEL_TYPE', 'openai')
    custom_model_id = current_app.config.get('CUSTOM_MODEL_ID', '')
    
    # Get custom model information if using a custom model
    custom_model = None
    custom_models = []
    
    if current_model == 'custom' and custom_model_id:
        from app.models.custom_model import CustomModel
        custom_model = CustomModel.query.filter_by(id=custom_model_id, user_id=current_user.id).first()
        custom_models = CustomModel.query.filter_by(user_id=current_user.id, is_active=True).all()
    else:
        from app.models.custom_model import CustomModel
        custom_models = CustomModel.query.filter_by(user_id=current_user.id, is_active=True).all()
    
    return render_template('chat.html', 
                          title='个人AI聊天', 
                          chats=chats, 
                          active_chat=active_chat, 
                          messages=messages, 
                          current_model=current_model,
                          custom_model=custom_model,
                          custom_model_id=custom_model_id,
                          custom_models=custom_models)

@chat_bp.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    """Render and handle the settings page."""
    # Get current model type from config
    current_model = current_app.config.get('AI_MODEL_TYPE', 'openai')
    custom_model_id = current_app.config.get('CUSTOM_MODEL_ID', '')
    
    # Get API keys from config
    openai_api_key = current_app.config.get('OPENAI_API_KEY', '')
    deepseek_api_key = current_app.config.get('DEEPSEEK_API_KEY', '')
    deepseek_api_url = current_app.config.get('DEEPSEEK_API_URL', 'https://api.deepseek.com/v1/chat/completions')
    deepseek_model = current_app.config.get('DEEPSEEK_MODEL', 'deepseek-chat')
    siliconflow_api_key = current_app.config.get('SILICONFLOW_API_KEY', '')
    siliconflow_api_url = current_app.config.get('SILICONFLOW_API_URL', 'https://api.siliconflow.com/v1/chat/completions')
    siliconflow_model = current_app.config.get('SILICONFLOW_MODEL', 'siliconflow-7b-chat')
    
    # Get custom models
    from app.models.custom_model import CustomModel
    custom_models = CustomModel.query.filter_by(user_id=current_user.id, is_active=True).all()
    
    if request.method == 'POST':
        # Get form data
        ai_model_type = request.form.get('ai_model_type')
        openai_api_key = request.form.get('openai_api_key')
        deepseek_api_key = request.form.get('deepseek_api_key')
        deepseek_api_url = request.form.get('deepseek_api_url')
        deepseek_model = request.form.get('deepseek_model')
        siliconflow_api_key = request.form.get('siliconflow_api_key')
        siliconflow_api_url = request.form.get('siliconflow_api_url')
        siliconflow_model = request.form.get('siliconflow_model')
        
        # Handle custom model selection
        if ai_model_type == 'custom':
            custom_model_id = request.form.get('custom_model_id')
            if not custom_model_id:
                flash('请选择一个自定义模型', 'danger')
                return redirect(url_for('chat.settings'))
        else:
            custom_model_id = ''
        
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
        env_vars['OPENAI_API_KEY'] = openai_api_key
        env_vars['DEEPSEEK_API_KEY'] = deepseek_api_key
        env_vars['DEEPSEEK_API_URL'] = deepseek_api_url
        env_vars['DEEPSEEK_MODEL'] = deepseek_model
        env_vars['SILICONFLOW_API_KEY'] = siliconflow_api_key
        env_vars['SILICONFLOW_API_URL'] = siliconflow_api_url
        env_vars['SILICONFLOW_MODEL'] = siliconflow_model
        
        # Add or remove custom model ID
        if ai_model_type == 'custom' and custom_model_id:
            env_vars['CUSTOM_MODEL_ID'] = custom_model_id
        elif 'CUSTOM_MODEL_ID' in env_vars:
            del env_vars['CUSTOM_MODEL_ID']
        
        # Write back to .env file
        with open(env_path, 'w') as f:
            for key, value in env_vars.items():
                f.write(f"{key}={value}\n")
        
        # Reload environment variables
        load_dotenv(env_path, override=True)
        
        # Update application config
        current_app.config['AI_MODEL_TYPE'] = ai_model_type
        current_app.config['OPENAI_API_KEY'] = openai_api_key
        current_app.config['DEEPSEEK_API_KEY'] = deepseek_api_key
        current_app.config['DEEPSEEK_API_URL'] = deepseek_api_url
        current_app.config['DEEPSEEK_MODEL'] = deepseek_model
        current_app.config['SILICONFLOW_API_KEY'] = siliconflow_api_key
        current_app.config['SILICONFLOW_API_URL'] = siliconflow_api_url
        current_app.config['SILICONFLOW_MODEL'] = siliconflow_model
        
        if ai_model_type == 'custom' and custom_model_id:
            current_app.config['CUSTOM_MODEL_ID'] = custom_model_id
        elif 'CUSTOM_MODEL_ID' in current_app.config:
            del current_app.config['CUSTOM_MODEL_ID']
        
        flash('设置已保存', 'success')
        return redirect(url_for('chat.settings'))
    
    return render_template('settings.html',
                          title='设置 - 豆包AI聊天',
                          current_model=current_model,
                          openai_api_key=openai_api_key,
                          deepseek_api_key=deepseek_api_key,
                          deepseek_api_url=deepseek_api_url,
                          deepseek_model=deepseek_model,
                          siliconflow_api_key=siliconflow_api_key,
                          siliconflow_api_url=siliconflow_api_url,
                          siliconflow_model=siliconflow_model,
                          custom_models=custom_models,
                          custom_model_id=custom_model_id)

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

@chat_bp.route('/test_api_key', methods=['POST'])
@login_required
def test_api_key():
    """Test an API key to see if it's valid."""
    try:
        model = request.form.get('model')
        api_key = request.form.get('api_key')
        api_url = request.form.get('api_url')
        model_name = request.form.get('model_name')
        
        if not model or not api_key:
            return jsonify({'success': False, 'error': '缺少必要参数'}), 400
        
        # Simple test message
        test_message = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello, this is a test message to verify API key."}
        ]
        
        if model == 'custom':
            # Test custom model API
            if not api_url:
                return jsonify({'success': False, 'error': '缺少API地址'}), 400
                
            if not model_name:
                return jsonify({'success': False, 'error': '缺少模型名称'}), 400
                
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            }
            
            data = {
                "model": model_name,
                "messages": test_message,
                "max_tokens": 10  # Minimal tokens for quick test
            }
            
            # Log the request details for debugging
            print(f"Testing Custom API with URL: {api_url}")
            print(f"Using model: {model_name}")
            print(f"API key (first 5 chars): {api_key[:5]}...")
            
            try:
                # Call API with timeout
                response = requests.post(api_url, headers=headers, data=json.dumps(data), timeout=10)
                
                # Log the response status and headers for debugging
                print(f"Custom API response status: {response.status_code}")
                print(f"Custom API response headers: {response.headers}")
                
                if response.status_code == 200:
                    return jsonify({'success': True, 'message': '自定义API密钥有效'})
                elif response.status_code == 401:
                    # Try to get more details from the response
                    try:
                        error_json = response.json()
                        error_detail = error_json.get('error', {}).get('message', '')
                        print(f"Custom API error details: {error_detail}")
                        return jsonify({'success': False, 'error': f'API认证失败: {error_detail}'})
                    except:
                        return jsonify({'success': False, 'error': 'API认证失败，密钥无效'})
                else:
                    # Try to get more details from the response
                    try:
                        response_text = response.text
                        print(f"Custom API response text: {response_text}")
                        return jsonify({'success': False, 'error': f'API请求失败: HTTP {response.status_code} - {response_text}'})
                    except:
                        return jsonify({'success': False, 'error': f'API请求失败: HTTP {response.status_code}'})
            except Exception as e:
                print(f"Exception testing Custom API: {str(e)}")
                return jsonify({'success': False, 'error': f'API测试异常: {str(e)}'})
        
        elif model == 'deepseek':
            # Test DeepSeek API
            if not api_url:
                api_url = 'https://api.deepseek.com/v1/chat/completions'
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            }
            
            data = {
                "model": current_app.config.get('DEEPSEEK_MODEL', 'deepseek-chat'),
                "messages": test_message,
                "max_tokens": 10  # Minimal tokens for quick test
            }
            
            # Log the request details for debugging
            print(f"Testing DeepSeek API with URL: {api_url}")
            print(f"Using model: {data['model']}")
            print(f"API key (first 5 chars): {api_key[:5]}...")
            
            try:
                # Call DeepSeek API with timeout
                response = requests.post(api_url, headers=headers, data=json.dumps(data), timeout=10)
                
                # Log the response status and headers for debugging
                print(f"DeepSeek API response status: {response.status_code}")
                print(f"DeepSeek API response headers: {response.headers}")
                
                if response.status_code == 200:
                    return jsonify({'success': True, 'message': 'DeepSeek API密钥有效'})
                elif response.status_code == 401:
                    # Try to get more details from the response
                    try:
                        error_json = response.json()
                        error_detail = error_json.get('error', {}).get('message', '')
                        print(f"DeepSeek API error details: {error_detail}")
                        return jsonify({'success': False, 'error': f'DeepSeek API认证失败: {error_detail}'})
                    except:
                        return jsonify({'success': False, 'error': 'DeepSeek API认证失败，密钥无效'})
                else:
                    # Try to get more details from the response
                    try:
                        response_text = response.text
                        print(f"DeepSeek API response text: {response_text}")
                        return jsonify({'success': False, 'error': f'DeepSeek API请求失败: HTTP {response.status_code} - {response_text}'})
                    except:
                        return jsonify({'success': False, 'error': f'DeepSeek API请求失败: HTTP {response.status_code}'})
            except Exception as e:
                print(f"Exception testing DeepSeek API: {str(e)}")
                return jsonify({'success': False, 'error': f'DeepSeek API测试异常: {str(e)}'})
            
        elif model == 'siliconflow':
            # Test SiliconFlow API
            if not api_url:
                api_url = 'https://api.siliconflow.cn/v1/chat/completions'
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            }
            
            data = {
                "model": current_app.config.get('SILICONFLOW_MODEL', 'Pro/deepseek-ai/DeepSeek-R1'),
                "messages": test_message,
                "max_tokens": 10  # Minimal tokens for quick test
            }
            
            response = requests.post(api_url, headers=headers, data=json.dumps(data), timeout=10)
            
        elif model == 'openai':
            # Test OpenAI API
            import openai
            openai.api_key = api_key
            
            try:
                # Use a simple models list call to test the API key
                client = openai.OpenAI(api_key=api_key)
                models = client.models.list()
                # If we get here, the API key is valid
                return jsonify({'success': True, 'message': 'API密钥有效'})
            except Exception as e:
                error_message = str(e)
                if "Authentication" in error_message or "auth" in error_message.lower() or "key" in error_message.lower():
                    return jsonify({'success': False, 'error': 'API认证失败，密钥无效'})
                else:
                    return jsonify({'success': False, 'error': f'OpenAI API调用失败: {error_message}'})
            
        else:
            # Unsupported model
            return jsonify({'success': False, 'error': '不支持的模型类型'}), 400
        
        # Check response for non-OpenAI models
        if response.status_code == 200:
            return jsonify({'success': True, 'message': 'API密钥有效'})
        elif response.status_code == 401:
            return jsonify({'success': False, 'error': 'API认证失败，密钥无效'})
        elif response.status_code == 403:
            return jsonify({'success': False, 'error': 'API权限不足，请检查密钥权限'})
        elif response.status_code == 404:
            return jsonify({'success': False, 'error': 'API端点不存在，请检查API地址'})
        elif response.status_code >= 500:
            return jsonify({'success': False, 'error': 'API服务器错误，请稍后重试'})
        else:
            error_message = f"API请求失败: HTTP {response.status_code}"
            try:
                error_json = response.json()
                if 'error' in error_json:
                    error_detail = error_json['error'].get('message', '')
                    error_message += f" - {error_detail}"
                    
                    # Check for common error patterns
                    if 'authentication' in error_detail.lower() or 'auth' in error_detail.lower():
                        return jsonify({'success': False, 'error': 'API认证失败，密钥无效或格式错误'})
                    elif 'rate limit' in error_detail.lower() or 'quota' in error_detail.lower():
                        return jsonify({'success': False, 'error': 'API使用超出限额，请稍后重试'})
            except:
                pass
            return jsonify({'success': False, 'error': error_message})
            
    except requests.exceptions.Timeout:
        return jsonify({'success': False, 'error': 'API请求超时，请检查API地址是否正确'})
    except requests.exceptions.ConnectionError:
        return jsonify({'success': False, 'error': 'API连接错误，请检查网络连接或API地址是否正确'})
    except Exception as e:
        return jsonify({'success': False, 'error': f'测试失败: {str(e)}'})

@chat_bp.route('/switch_model', methods=['POST'])
@login_required
def switch_model():
    """Switch the AI model type."""
    try:
        model = request.form.get('model')
        custom_model_id = request.form.get('custom_model_id')
        
        # Check if this is a custom model
        if model == 'custom' and custom_model_id:
            from app.models.custom_model import CustomModel
            custom_model = CustomModel.query.filter_by(id=custom_model_id, user_id=current_user.id).first()
            
            if not custom_model:
                return jsonify({'success': False, 'error': '找不到指定的自定义模型'}), 404
                
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
            
            # Update model type and custom model ID
            env_vars['AI_MODEL_TYPE'] = 'custom'
            env_vars['CUSTOM_MODEL_ID'] = custom_model_id
            
            # Write back to .env file
            with open(env_path, 'w') as f:
                for key, value in env_vars.items():
                    f.write(f"{key}={value}\n")
            
            # Reload environment variables
            load_dotenv(env_path, override=True)
            
            # Update application config
            current_app.config['AI_MODEL_TYPE'] = 'custom'
            current_app.config['CUSTOM_MODEL_ID'] = custom_model_id
            
            return jsonify({'success': True, 'message': f'已切换到自定义模型: {custom_model.display_name}'})
        
        # Standard models
        if not model or model not in ['openai', 'deepseek', 'siliconflow', 'custom']:
            return jsonify({'success': False, 'error': '无效的模型类型'}), 400
        
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
        
        # Update model type
        env_vars['AI_MODEL_TYPE'] = model
        
        # Remove custom model ID if switching to a standard model
        if 'CUSTOM_MODEL_ID' in env_vars:
            del env_vars['CUSTOM_MODEL_ID']
        
        # Write back to .env file
        with open(env_path, 'w') as f:
            for key, value in env_vars.items():
                f.write(f"{key}={value}\n")
        
        # Reload environment variables
        load_dotenv(env_path, override=True)
        
        # Update application config
        current_app.config['AI_MODEL_TYPE'] = model
        if 'CUSTOM_MODEL_ID' in current_app.config:
            del current_app.config['CUSTOM_MODEL_ID']
        
        return jsonify({'success': True, 'message': f'已切换到{model}模型'})
        
    except Exception as e:
        return jsonify({'success': False, 'error': f'切换模型失败: {str(e)}'}), 500 