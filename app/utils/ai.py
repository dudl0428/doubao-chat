import os
import openai
import requests
import json
import logging
from app.models.chat import Message
from flask import current_app

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def generate_ai_response(chat_id, user_message):
    """
    Generate an AI response using either OpenAI API, DeepSeek API, 硅谷流动 API, or custom models.
    
    Args:
        chat_id (int): The ID of the chat.
        user_message (str): The user's message.
        
    Returns:
        str: The AI's response.
    """
    try:
        # Get chat history (last 10 messages for context)
        messages = Message.query.filter_by(chat_id=chat_id).order_by(Message.created_at.desc()).limit(10).all()
        messages.reverse()  # Oldest first
        
        # Format messages for API
        conversation = []
        for msg in messages:
            conversation.append({
                "role": msg.role,
                "content": msg.content
            })
        
        # Add the current user message if it's not already in the history
        if not messages or messages[-1].role != 'user' or messages[-1].content != user_message:
            conversation.append({
                "role": "user",
                "content": user_message
            })
        
        # Add system message at the beginning
        conversation.insert(0, {
            "role": "system",
            "content": "你是豆包AI助手，一个有用、无害、诚实的AI助手。请用中文回答用户的问题。"
        })
        
        # Check which model to use
        model_type = current_app.config.get('AI_MODEL_TYPE', 'openai')
        logger.info(f"Using model type: {model_type}")
        
        # Try the selected model first
        response = None
        if model_type.lower() == 'deepseek':
            response = generate_deepseek_response(conversation)
        elif model_type.lower() == 'siliconflow':
            response = generate_siliconflow_response(conversation)
        elif model_type.lower() == 'custom':
            response = generate_custom_response(conversation)
        else:
            response = generate_openai_response(conversation)
        
        # Check if the response indicates an error
        if "API请求超时" in response or "API连接错误" in response or "API调用失败" in response:
            logger.warning(f"Primary model ({model_type}) failed, trying fallback to OpenAI")
            # If the selected model failed, try OpenAI as a fallback
            if model_type.lower() != 'openai':
                fallback_response = generate_openai_response(conversation)
                if not ("API请求超时" in fallback_response or "API连接错误" in fallback_response or "API调用失败" in fallback_response):
                    return fallback_response + "\n\n(注: 由于原模型响应超时，此回答由OpenAI模型提供)"
        
        return response
        
    except Exception as e:
        # Log the error
        logger.error(f"Error generating AI response: {str(e)}")
        return f"抱歉，生成回复时出现错误: {str(e)}"

def generate_custom_response(conversation):
    """Generate response using a custom model API."""
    # Get custom model ID from config
    custom_model_id = current_app.config.get('CUSTOM_MODEL_ID')
    if not custom_model_id:
        logger.warning("Custom model ID not configured")
        return "自定义模型未配置，请在设置页面选择一个自定义模型。"
    
    try:
        # Import here to avoid circular imports
        from app.models.custom_model import CustomModel
        from flask_login import current_user
        
        # Get the custom model from the database
        custom_model = CustomModel.query.filter_by(id=custom_model_id, user_id=current_user.id).first()
        if not custom_model:
            logger.warning(f"Custom model with ID {custom_model_id} not found")
            return "找不到指定的自定义模型，请在设置页面重新选择模型。"
        
        # Check if the model is active
        if not custom_model.is_active:
            logger.warning(f"Custom model with ID {custom_model_id} is not active")
            return "自定义模型已被禁用，请在设置页面启用或选择其他模型。"
        
        # Optimize conversation history - limit to last 5 messages to reduce payload size
        if len(conversation) > 6:  # +1 for system message
            # Keep system message and last 5 exchanges
            system_message = conversation[0]
            conversation = [system_message] + conversation[-5:]
            logger.info("Trimmed conversation history to last 5 messages")
        
        # Override system prompt if specified
        if custom_model.system_prompt:
            conversation[0]["content"] = custom_model.system_prompt
        
        # Prepare the request
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {custom_model.api_key}"
        }
        
        data = {
            "model": custom_model.model_name,
            "messages": conversation,
            "temperature": custom_model.temperature,
            "max_tokens": custom_model.max_tokens,
            "timeout": 15  # Add explicit timeout parameter if supported by the API
        }
        
        logger.info(f"Sending request to custom API: {custom_model.api_url}")
        logger.info(f"Using model: {custom_model.model_name}")
        
        # Call custom API with timeout
        response = requests.post(custom_model.api_url, headers=headers, data=json.dumps(data), timeout=15)
        
        # Check if the request was successful
        if response.status_code == 200:
            response_json = response.json()
            return response_json['choices'][0]['message']['content']
        else:
            error_message = f"自定义模型 API请求失败: HTTP {response.status_code}"
            try:
                error_json = response.json()
                if 'error' in error_json:
                    error_detail = error_json['error'].get('message', '')
                    error_message += f" - {error_detail}"
                    logger.error(f"API Error details: {error_json}")
            except:
                pass
            logger.error(error_message)
            return error_message
    except requests.exceptions.Timeout:
        logger.error("Custom API request timed out")
        return "自定义模型 API请求超时，请稍后重试或考虑使用其他模型。"
    except requests.exceptions.ConnectionError:
        logger.error("Custom API connection error")
        return "自定义模型 API连接错误，请检查网络连接或API地址是否正确。"
    except Exception as e:
        logger.error(f"Custom API call failed: {str(e)}")
        return f"自定义模型 API调用失败: {str(e)}"

def generate_openai_response(conversation):
    """Generate response using OpenAI API."""
    # Get OpenAI API key from config
    api_key = current_app.config.get('OPENAI_API_KEY')
    if not api_key:
        logger.warning("OpenAI API key not configured")
        return "OpenAI API密钥未配置，请在设置页面配置API密钥。"
    
    try:
        # Optimize conversation history - limit to last 5 messages to reduce payload size
        if len(conversation) > 6:  # +1 for system message
            # Keep system message and last 5 exchanges
            system_message = conversation[0]
            conversation = [system_message] + conversation[-5:]
            logger.info("Trimmed conversation history to last 5 messages")
        
        # Initialize the OpenAI client
        client = openai.OpenAI(api_key=api_key)
        
        # Call OpenAI API
        logger.info("Sending request to OpenAI API")
        logger.info("Using model: gpt-3.5-turbo")
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=conversation,
            max_tokens=800,  # Reduced from 1000 to improve response time
            temperature=0.7,
            timeout=15  # Add timeout parameter
        )
        
        # Extract and return the response text
        return response.choices[0].message.content
    except Exception as e:
        error_message = str(e)
        logger.error(f"OpenAI API call failed: {error_message}")
        
        if "timeout" in error_message.lower():
            return "OpenAI API请求超时，请稍后重试或考虑使用其他模型。"
        elif "connect" in error_message.lower() or "connection" in error_message.lower():
            return "OpenAI API连接错误，请检查网络连接。"
        else:
            return f"OpenAI API调用失败: {error_message}"

def generate_deepseek_response(conversation):
    """Generate response using DeepSeek API."""
    # Get DeepSeek API key from config
    api_key = current_app.config.get('DEEPSEEK_API_KEY')
    if not api_key:
        logger.warning("DeepSeek API key not configured")
        return "DeepSeek API密钥未配置，请在设置页面配置API密钥。"
    
    # DeepSeek API endpoint
    api_url = current_app.config.get('DEEPSEEK_API_URL', 'https://api.deepseek.com/v1/chat/completions')
    
    try:
        # Optimize conversation history - limit to last 5 messages to reduce payload size
        if len(conversation) > 6:  # +1 for system message
            # Keep system message and last 5 exchanges
            system_message = conversation[0]
            conversation = [system_message] + conversation[-5:]
            logger.info("Trimmed conversation history to last 5 messages")
        
        # Prepare the request
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        
        data = {
            "model": current_app.config.get('DEEPSEEK_MODEL', 'deepseek-chat'),
            "messages": conversation,
            "temperature": 0.7,
            "max_tokens": 800,  # Reduced from 1000 to improve response time
            "timeout": 15  # Add explicit timeout parameter if supported by the API
        }
        
        logger.info(f"Sending request to DeepSeek API: {api_url}")
        logger.info(f"Using model: {data['model']}")
        
        # Call DeepSeek API with reduced timeout
        response = requests.post(api_url, headers=headers, data=json.dumps(data), timeout=15)
        
        # Check if the request was successful
        if response.status_code == 200:
            response_json = response.json()
            return response_json['choices'][0]['message']['content']
        else:
            error_message = f"DeepSeek API请求失败: HTTP {response.status_code}"
            try:
                error_json = response.json()
                if 'error' in error_json:
                    error_message += f" - {error_json['error']['message']}"
                    logger.error(f"API Error details: {error_json}")
            except:
                pass
            logger.error(error_message)
            return error_message
    except requests.exceptions.Timeout:
        logger.error("DeepSeek API request timed out")
        return "DeepSeek API请求超时，请稍后重试或考虑使用其他模型。"
    except requests.exceptions.ConnectionError:
        logger.error("DeepSeek API connection error")
        return "DeepSeek API连接错误，请检查网络连接或API地址是否正确。"
    except Exception as e:
        logger.error(f"DeepSeek API call failed: {str(e)}")
        return f"DeepSeek API调用失败: {str(e)}"

def generate_siliconflow_response(conversation):
    """Generate response using 硅谷流动 API."""
    # Get 硅谷流动 API key from config
    api_key = current_app.config.get('SILICONFLOW_API_KEY')
    if not api_key:
        logger.warning("硅谷流动 API key not configured")
        return "硅谷流动 API密钥未配置，请在设置页面配置API密钥。"
    
    # 硅谷流动 API endpoint
    api_url = current_app.config.get('SILICONFLOW_API_URL', 'https://api.siliconflow.com/v1/chat/completions')
    
    try:
        # Optimize conversation history - limit to last 5 messages to reduce payload size
        if len(conversation) > 6:  # +1 for system message
            # Keep system message and last 5 exchanges
            system_message = conversation[0]
            conversation = [system_message] + conversation[-5:]
            logger.info("Trimmed conversation history to last 5 messages")
        
        # Prepare the request
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        
        data = {
            "model": current_app.config.get('SILICONFLOW_MODEL', 'siliconflow-7b-chat'),
            "messages": conversation,
            "temperature": 0.7,
            "max_tokens": 800,  # Reduced from 1000 to improve response time
            "timeout": 15  # Add explicit timeout parameter if supported by the API
        }
        
        logger.info(f"Sending request to 硅谷流动 API: {api_url}")
        logger.info(f"Using model: {data['model']}")
        
        # Call 硅谷流动 API with reduced timeout
        response = requests.post(api_url, headers=headers, data=json.dumps(data), timeout=15)
        
        # Check if the request was successful
        if response.status_code == 200:
            response_json = response.json()
            return response_json['choices'][0]['message']['content']
        else:
            error_message = f"硅谷流动 API请求失败: HTTP {response.status_code}"
            try:
                error_json = response.json()
                if 'error' in error_json:
                    error_message += f" - {error_json['error']['message']}"
                    logger.error(f"API Error details: {error_json}")
            except:
                pass
            logger.error(error_message)
            return error_message
    except requests.exceptions.Timeout:
        logger.error("硅谷流动 API request timed out")
        return "硅谷流动 API请求超时，请稍后重试或考虑使用其他模型。"
    except requests.exceptions.ConnectionError:
        logger.error("硅谷流动 API connection error")
        return "硅谷流动 API连接错误，请检查网络连接或API地址是否正确。"
    except Exception as e:
        logger.error(f"硅谷流动 API call failed: {str(e)}")
        return f"硅谷流动 API调用失败: {str(e)}" 