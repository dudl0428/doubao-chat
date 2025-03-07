from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.urls import url_parse
from app import db
from app.models.user import User
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError

# Create blueprint
auth_bp = Blueprint('auth', __name__)

# Routes
@auth_bp.route('/')
def index():
    """Render the home page."""
    return render_template('index.html')

# Forms
class LoginForm(FlaskForm):
    """Login form."""
    username = StringField('用户名', validators=[DataRequired(message='请输入用户名')])
    password = PasswordField('密码', validators=[DataRequired(message='请输入密码')])
    remember_me = BooleanField('记住我')
    submit = SubmitField('登录')

class RegistrationForm(FlaskForm):
    """Registration form."""
    username = StringField('用户名', validators=[DataRequired(message='请输入用户名'), Length(min=3, max=64, message='用户名长度必须在3到64个字符之间')])
    email = StringField('邮箱', validators=[DataRequired(message='请输入邮箱'), Email(message='请输入有效的邮箱地址')])
    password = PasswordField('密码', validators=[DataRequired(message='请输入密码'), Length(min=8, message='密码长度至少为8个字符')])
    password2 = PasswordField('确认密码', validators=[DataRequired(message='请确认密码'), EqualTo('password', message='两次输入的密码不匹配')])
    submit = SubmitField('注册')
    
    def validate_username(self, username):
        """Validate that the username is not already in use."""
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('该用户名已被使用，请选择其他用户名')
    
    def validate_email(self, email):
        """Validate that the email is not already in use."""
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('该邮箱已被注册，请使用其他邮箱')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login."""
    if current_user.is_authenticated:
        return redirect(url_for('chat.index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.verify_password(form.password.data):
            flash('用户名或密码错误', 'danger')
            return redirect(url_for('auth.login'))
        
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('chat.index')
        return redirect(next_page)
    
    return render_template('login.html', title='登录', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    """Handle user logout."""
    logout_user()
    flash('您已成功登出', 'success')
    return redirect(url_for('auth.login'))

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Handle user registration."""
    if current_user.is_authenticated:
        return redirect(url_for('chat.index'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.password = form.password.data
        db.session.add(user)
        db.session.commit()
        flash('注册成功！请登录', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('register.html', title='注册', form=form) 