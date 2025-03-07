from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required, current_user
from app import db
from app.models.custom_model import CustomModel
import requests
import json

# Create blueprint with url_prefix
custom_model_bp = Blueprint('custom_model', __name__, url_prefix='/custom_model')

@custom_model_bp.route('/')
@login_required
def index():
    """List all custom models for the current user."""
    models = CustomModel.query.filter_by(user_id=current_user.id).all()
    return render_template('custom_model/index.html', custom_models=models)

@custom_model_bp.route('/new', methods=['GET', 'POST'])
@login_required
def new():
    """Create a new custom model."""
    if request.method == 'POST':
        name = request.form.get('name')
        display_name = request.form.get('display_name')
        api_url = request.form.get('api_url')
        api_key = request.form.get('api_key')
        model_name = request.form.get('model_name')
        temperature = float(request.form.get('temperature', 0.7))
        max_tokens = int(request.form.get('max_tokens', 2000))
        system_prompt = request.form.get('system_prompt')
        
        # Validate required fields
        if not name or not display_name or not api_url or not api_key or not model_name:
            flash('所有必填字段都必须填写', 'danger')
            return redirect(url_for('custom_model.new'))
        
        # Check if name already exists for this user
        existing_model = CustomModel.query.filter_by(user_id=current_user.id, name=name).first()
        if existing_model:
            flash('已存在同名的自定义模型', 'danger')
            return redirect(url_for('custom_model.new'))
        
        # Create new custom model
        custom_model = CustomModel(
            user_id=current_user.id,
            name=name,
            display_name=display_name,
            api_url=api_url,
            api_key=api_key,
            model_name=model_name,
            temperature=temperature,
            max_tokens=max_tokens,
            system_prompt=system_prompt
        )
        
        db.session.add(custom_model)
        db.session.commit()
        
        flash('自定义模型创建成功', 'success')
        return redirect(url_for('custom_model.index'))
    
    return render_template('custom_model/new.html')

@custom_model_bp.route('/<int:model_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(model_id):
    """Edit a custom model."""
    model = CustomModel.query.filter_by(id=model_id, user_id=current_user.id).first_or_404()
    
    if request.method == 'POST':
        model.display_name = request.form.get('display_name')
        model.api_url = request.form.get('api_url')
        model.api_key = request.form.get('api_key')
        model.model_name = request.form.get('model_name')
        model.temperature = float(request.form.get('temperature', 0.7))
        model.max_tokens = int(request.form.get('max_tokens', 2000))
        model.system_prompt = request.form.get('system_prompt')
        model.is_active = 'is_active' in request.form
        
        db.session.commit()
        
        flash('自定义模型更新成功', 'success')
        return redirect(url_for('custom_model.index'))
    
    return render_template('custom_model/edit.html', custom_model=model)

@custom_model_bp.route('/<int:model_id>/delete', methods=['POST'])
@login_required
def delete(model_id):
    """Delete a custom model."""
    model = CustomModel.query.filter_by(id=model_id, user_id=current_user.id).first_or_404()
    
    db.session.delete(model)
    db.session.commit()
    
    flash('自定义模型删除成功', 'success')
    return redirect(url_for('custom_model.index'))

@custom_model_bp.route('/<int:model_id>/test', methods=['POST'])
@login_required
def test(model_id):
    """Test a custom model API connection."""
    model = CustomModel.query.filter_by(id=model_id, user_id=current_user.id).first_or_404()
    
    # Simple test message
    test_message = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello, this is a test message to verify API key."}
    ]
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {model.api_key}"
    }
    
    data = {
        "model": model.model_name,
        "messages": test_message,
        "max_tokens": 10,  # Minimal tokens for quick test
        "temperature": model.temperature
    }
    
    try:
        # Call API with timeout
        response = requests.post(model.api_url, headers=headers, data=json.dumps(data), timeout=10)
        
        if response.status_code == 200:
            return jsonify({'success': True, 'message': 'API连接成功'})
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
            except:
                pass
            return jsonify({'success': False, 'error': error_message})
            
    except requests.exceptions.Timeout:
        return jsonify({'success': False, 'error': 'API请求超时，请检查API地址是否正确'})
    except requests.exceptions.ConnectionError:
        return jsonify({'success': False, 'error': 'API连接错误，请检查网络连接或API地址是否正确'})
    except Exception as e:
        return jsonify({'success': False, 'error': f'测试失败: {str(e)}'}) 