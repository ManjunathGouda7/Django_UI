from django.urls import path
from .views_IssuesAndTasksTracking import (
    # Main views
    issues_tasks_dashboard,
    get_issues_tasks_data,
    
    # Issue endpoints
    get_issues,
    create_issue,
    get_issue_details,
    update_issue,
    delete_issue,
    assign_issue,
    update_issue_status,
    update_issue_priority,
    
    # Task endpoints
    get_tasks,
    create_task,
    get_task_details,
    update_task,
    delete_task,
    complete_task,
    assign_task,
    update_task_priority,
    
    # Comment endpoints
    get_issue_comments,
    add_issue_comment,
    get_task_comments,
    add_task_comment,
    
    # Analytics endpoints
    get_issues_analytics,
    get_tasks_analytics,
    get_dashboard_stats,
    
    # Bulk operations
    bulk_update_issues,
    bulk_update_tasks,
    
    # Export endpoints
    export_issues,
    export_tasks,
    
    # Search endpoints
    search_issues,
    search_tasks,
    
    # Notification endpoints
    get_notifications,
    mark_notifications_read,
)

app_name = 'issues_tasks'

urlpatterns = [
    # ============================================
    # MAIN VIEWS
    # ============================================
    path('', issues_tasks_dashboard, name='dashboard'),
    path('data/', get_issues_tasks_data, name='data'),
    
    # ============================================
    # ISSUE ENDPOINTS
    # ============================================
    path('api/issues/', get_issues, name='get_issues'),
    path('api/issues/create/', create_issue, name='create_issue'),
    path('api/issues/<int:issue_id>/', get_issue_details, name='get_issue_details'),
    path('api/issues/<int:issue_id>/update/', update_issue, name='update_issue'),
    path('api/issues/<int:issue_id>/delete/', delete_issue, name='delete_issue'),
    path('api/issues/<int:issue_id>/assign/', assign_issue, name='assign_issue'),
    path('api/issues/<int:issue_id>/status/', update_issue_status, name='update_issue_status'),
    path('api/issues/<int:issue_id>/priority/', update_issue_priority, name='update_issue_priority'),
    
    # ============================================
    # TASK ENDPOINTS
    # ============================================
    path('api/tasks/', get_tasks, name='get_tasks'),
    path('api/tasks/create/', create_task, name='create_task'),
    path('api/tasks/<int:task_id>/', get_task_details, name='get_task_details'),
    path('api/tasks/<int:task_id>/update/', update_task, name='update_task'),
    path('api/tasks/<int:task_id>/delete/', delete_task, name='delete_task'),
    path('api/tasks/<int:task_id>/complete/', complete_task, name='complete_task'),
    path('api/tasks/<int:task_id>/assign/', assign_task, name='assign_task'),
    path('api/tasks/<int:task_id>/priority/', update_task_priority, name='update_task_priority'),
    
    # ============================================
    # COMMENT ENDPOINTS
    # ============================================
    path('api/issues/<int:issue_id>/comments/', get_issue_comments, name='get_issue_comments'),
    path('api/issues/<int:issue_id>/comments/add/', add_issue_comment, name='add_issue_comment'),
    path('api/tasks/<int:task_id>/comments/', get_task_comments, name='get_task_comments'),
    path('api/tasks/<int:task_id>/comments/add/', add_task_comment, name='add_task_comment'),
    
    # ============================================
    # ANALYTICS ENDPOINTS
    # ============================================
    path('api/issues/analytics/', get_issues_analytics, name='get_issues_analytics'),
    path('api/tasks/analytics/', get_tasks_analytics, name='get_tasks_analytics'),
    path('api/dashboard/stats/', get_dashboard_stats, name='get_dashboard_stats'),
    
    # ============================================
    # BULK OPERATIONS
    # ============================================
    path('api/issues/bulk-update/', bulk_update_issues, name='bulk_update_issues'),
    path('api/tasks/bulk-update/', bulk_update_tasks, name='bulk_update_tasks'),
    
    # ============================================
    # EXPORT ENDPOINTS
    # ============================================
    path('api/issues/export/', export_issues, name='export_issues'),
    path('api/tasks/export/', export_tasks, name='export_tasks'),
    
    # ============================================
    # SEARCH ENDPOINTS
    # ============================================
    path('api/issues/search/', search_issues, name='search_issues'),
    path('api/tasks/search/', search_tasks, name='search_tasks'),
    
    # ============================================
    # NOTIFICATION ENDPOINTS
    # ============================================
    path('api/notifications/', get_notifications, name='get_notifications'),
    path('api/notifications/mark-read/', mark_notifications_read, name='mark_notifications_read'),
]