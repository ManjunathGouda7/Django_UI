# grl_api/api/chatbot_urls.py
from django.urls import path
from .views_chatbot import (  
    send_message,
    get_chat_history,
    get_models,
    set_model,
    upload_document,
    get_documents,
    delete_document,
    delete_chat,
    clear_all_chats
)

urlpatterns = [
    # Chat endpoints
    path('send-message/', send_message, name='chatbot_send_message'),
    path('get-history/', get_chat_history, name='chatbot_get_history'),
    path('get-models/', get_models, name='chatbot_get_models'),
    path('set-model/', set_model, name='chatbot_set_model'),
    
    # Document endpoints
    path('upload-document/', upload_document, name='chatbot_upload_document'),
    path('get-documents/', get_documents, name='chatbot_get_documents'),
    path('delete-document/<str:doc_id>/', delete_document, name='chatbot_delete_document'),
    
    # Chat management
    path('delete-chat/<str:chat_id>/', delete_chat, name='chatbot_delete_chat'),
    path('clear-all-chats/', clear_all_chats, name='chatbot_clear_all_chats'),
]