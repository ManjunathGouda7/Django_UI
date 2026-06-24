# UI_Automation_Development/pages/ChatBot.py
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
import json
import os
from datetime import datetime

def chatbot_view(request):
    """Render the ChatBot page"""
    return render(request, 'grl_api/ChatBot.html')

@csrf_exempt
def send_message(request):
    """Handle chat messages"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            message = data.get('message', '')
            chat_id = data.get('chat_id', None)
            model = data.get('model', 'ministral-3-3b-instruct-2512')
            
            # Here you would integrate with your actual AI model
            # For now, return a mock response
            response = {
                'status': 'success',
                'message': f"I received your message: '{message}'. This is a mock response. Integrate with your AI model here!",
                'chat_id': chat_id or f"chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                'timestamp': datetime.now().isoformat()
            }
            
            return JsonResponse(response)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
    return JsonResponse({'error': 'Method not allowed'}, status=405)

@csrf_exempt
def get_chat_history(request):
    """Get chat history"""
    if request.method == 'GET':
        # Mock chat history
        history = {
            'chats': [
                {
                    'id': 'chat_001',
                    'title': 'Hello World',
                    'preview': 'This is a sample chat',
                    'timestamp': '2026-01-15T10:30:00',
                    'messages': [
                        {'sender': 'user', 'content': 'Hello', 'timestamp': '2026-01-15T10:30:00'},
                        {'sender': 'bot', 'content': 'Hi there! How can I help you?', 'timestamp': '2026-01-15T10:30:05'}
                    ]
                }
            ]
        }
        return JsonResponse(history)
    return JsonResponse({'error': 'Method not allowed'}, status=405)

@csrf_exempt
def get_models(request):
    """Get available AI models"""
    models = {
        'status': 'success',
        'models_status': {
            'models': [
                'ministral-3-3b-instruct-2512',
                'llama-3-2-3b-instruct',
                'gemma-2-2b-it',
                'qwen-2.5-3b-instruct'
            ],
            'current': 'ministral-3-3b-instruct-2512'
        }
    }
    return JsonResponse(models)

@csrf_exempt
def set_model(request):
    """Set the active AI model"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            model = data.get('model', '')
            return JsonResponse({
                'status': 'success',
                'message': f'Model set to {model}',
                'model': model
            })
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
    return JsonResponse({'error': 'Method not allowed'}, status=405)

@csrf_exempt
def upload_document(request):
    """Handle document uploads"""
    if request.method == 'POST':
        if request.FILES.get('file'):
            file = request.FILES['file']
            # Process file here
            return JsonResponse({
                'status': 'success',
                'message': f'File {file.name} uploaded successfully',
                'filename': file.name,
                'size': file.size
            })
        return JsonResponse({'error': 'No file provided'}, status=400)
    return JsonResponse({'error': 'Method not allowed'}, status=405)

@csrf_exempt
def get_documents(request):
    """Get list of uploaded documents"""
    documents = {
        'status': 'success',
        'documents': [
            {'name': 'sample.txt', 'size': '2.3 KB', 'date': '2026-01-15'},
            {'name': 'documentation.pdf', 'size': '1.2 MB', 'date': '2026-01-14'}
        ]
    }
    return JsonResponse(documents)

@csrf_exempt
def delete_document(request, doc_id):
    """Delete a document"""
    if request.method == 'DELETE':
        return JsonResponse({
            'status': 'success',
            'message': f'Document {doc_id} deleted'
        })
    return JsonResponse({'error': 'Method not allowed'}, status=405)

@csrf_exempt
def delete_chat(request, chat_id):
    """Delete a chat"""
    if request.method == 'DELETE':
        return JsonResponse({
            'status': 'success',
            'message': f'Chat {chat_id} deleted'
        })
    return JsonResponse({'error': 'Method not allowed'}, status=405)

@csrf_exempt
def clear_all_chats(request):
    """Clear all chat history"""
    if request.method == 'DELETE':
        return JsonResponse({
            'status': 'success',
            'message': 'All chats cleared'
        })
    return JsonResponse({'error': 'Method not allowed'}, status=405)