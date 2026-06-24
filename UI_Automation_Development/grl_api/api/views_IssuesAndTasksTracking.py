import json
import logging
import csv
import io
from datetime import datetime, timedelta
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from rest_framework.response import Response

from grl_api.models import Issue, Task, Comment

logger = logging.getLogger(__name__)

# ============================================
# DATABASE SEEDING
# ============================================
def seed_initial_data_if_empty():
    """Seed initial data if database tables are empty"""
    try:
        if Issue.objects.count() == 0:
            # Seed default issues
            i1 = Issue.objects.create(
                title='Fix login page redirect issue',
                description='Users are not being redirected properly after successful login.',
                status='open',
                priority='high',
                assigned_to='John Doe',
                created_by='Jane Smith',
                due_date=(datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d"),
                tags=['login', 'bug', 'high-priority']
            )
            i2 = Issue.objects.create(
                title='Update API documentation',
                description='The API documentation needs to be updated with the new endpoints.',
                status='in_progress',
                priority='medium',
                assigned_to='Alice Johnson',
                created_by='Bob Wilson',
                due_date=(datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d"),
                tags=['documentation', 'api']
            )
            i3 = Issue.objects.create(
                title='Database connection timeout',
                description='Database connections are timing out under heavy load.',
                status='closed', # change status slightly to have variance
                priority='high', # standard priority
                assigned_to='Sarah Lee',
                created_by='Mike Johnson',
                due_date=(datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d"),
                tags=['database', 'performance']
            )
            
            # Seed default comments
            Comment.objects.create(author='John Doe', content='Looking into the redirects.', item_type='issue', item_id=i1.id)
            Comment.objects.create(author='Jane Smith', content='Please check the middleware implementation.', item_type='issue', item_id=i1.id)
            Comment.objects.create(author='Alice Johnson', content='Doc updates in progress.', item_type='issue', item_id=i2.id)

        if Task.objects.count() == 0:
            # Seed default tasks
            t1 = Task.objects.create(
                title='Verify OAuth integration',
                description='Test third-party OAuth redirect flows.',
                status='in_progress',
                priority='high',
                assigned_to='John Doe',
                due_date=(datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d"),
                progress=50,
                parent_issue_id=1
            )
            t2 = Task.objects.create(
                title='Review API routes definition',
                description='Validate endpoint prefix matches /api/v1/.',
                status='pending',
                priority='medium',
                assigned_to='Alice Johnson',
                due_date=(datetime.now() + timedelta(days=4)).strftime("%Y-%m-%d"),
                progress=10,
                parent_issue_id=2
            )
            
            Comment.objects.create(author='John Doe', content='OAuth credentials validated.', item_type='task', item_id=t1.id)

    except Exception as e:
        logger.error(f"Error seeding database: {str(e)}")

# ============================================
# MAIN DASHBOARD VIEWS
# ============================================
def issues_tasks_dashboard(request):
    """Main Issues and Tasks dashboard view"""
    seed_initial_data_if_empty()
    context = {
        'page_title': 'Issues & Tasks Tracking',
        'active_tab': 'issues',
    }
    return render(request, 'grl_api/IssuesAndTasksTracking.html', context)

def get_issues_tasks_data(request):
    """Get combined data for dashboard"""
    try:
        seed_initial_data_if_empty()
        issues = [i.to_dict() for i in Issue.objects.all()]
        tasks = [t.to_dict() for t in Task.objects.all()]
        return JsonResponse({
            'success': True,
            'data': {
                'issues': issues,
                'tasks': tasks,
                'stats': {
                    'total_issues': len(issues),
                    'total_tasks': len(tasks),
                    'open_issues': len([i for i in issues if i['status'] == 'open']),
                    'completed_tasks': len([t for t in tasks if t['status'] == 'completed'])
                }
            }
        })
    except Exception as e:
        logger.error(f"Error getting issues tasks data: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

# ============================================
# ISSUE API ENDPOINTS
# ============================================
@require_http_methods(["GET"])
def get_issues(request):
    """Get all issues with filtering and pagination"""
    try:
        status = request.GET.get('status', 'all')
        priority = request.GET.get('priority', 'all')
        assigned_to = request.GET.get('assigned_to')
        search = request.GET.get('search', '')
        page = int(request.GET.get('page', 1))
        per_page = int(request.GET.get('per_page', 20))
        
        qs = Issue.objects.all().order_by('-id')
        if status != 'all':
            qs = qs.filter(status=status)
        if priority != 'all':
            qs = qs.filter(priority=priority)
        if assigned_to:
            qs = qs.filter(assigned_to__icontains=assigned_to)
        if search:
            qs = qs.filter(title__icontains=search) | qs.filter(description__icontains=search)
            
        total = qs.count()
        start = (page - 1) * per_page
        end = start + per_page
        
        issues = [i.to_dict() for i in qs[start:end]]
        return JsonResponse({
            'success': True,
            'issues': issues,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total,
                'total_pages': (total + per_page - 1) // per_page if total > 0 else 1
            }
        })
    except Exception as e:
        logger.error(f"Error fetching issues: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def create_issue(request):
    """Create a new issue"""
    try:
        data = json.loads(request.body)
        from grl_api.api.serializers import IssueSerializer
        serializer = IssueSerializer(data=data)
        if not serializer.is_valid():
            return JsonResponse({
                'success': False,
                'error': 'Validation Error',
                'details': serializer.errors
            }, status=400)
            
        issue = serializer.save()
        return JsonResponse({
            'success': True,
            'issue': issue.to_dict(),
            'message': 'Issue created successfully'
        })
    except Exception as e:
        logger.error(f"Error creating issue: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@require_http_methods(["GET"])
def get_issue_details(request, issue_id):
    """Get detailed information about a specific issue"""
    try:
        issue = Issue.objects.filter(id=issue_id).first()
        if not issue:
            return JsonResponse({'success': False, 'error': 'Issue not found'}, status=404)
            
        issue_data = issue.to_dict()
        comments = [c.to_dict() for c in Comment.objects.filter(item_type='issue', item_id=issue_id).order_by('id')]
        issue_data['comments'] = comments
        issue_data['comment_count'] = len(comments)
        
        return JsonResponse({
            'success': True,
            'issue': issue_data
        })
    except Exception as e:
        logger.error(f"Error fetching issue details: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["PUT"])
def update_issue(request, issue_id):
    """Update an existing issue"""
    try:
        issue = Issue.objects.filter(id=issue_id).first()
        if not issue:
            return JsonResponse({'success': False, 'error': 'Issue not found'}, status=404)
            
        data = json.loads(request.body)
        from grl_api.api.serializers import IssueSerializer
        serializer = IssueSerializer(issue, data=data, partial=True)
        if not serializer.is_valid():
            return JsonResponse({
                'success': False,
                'error': 'Validation Error',
                'details': serializer.errors
            }, status=400)
            
        updated_issue = serializer.save()
        return JsonResponse({
            'success': True,
            'issue': updated_issue.to_dict(),
            'message': 'Issue updated successfully'
        })
    except Exception as e:
        logger.error(f"Error updating issue: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["DELETE"])
def delete_issue(request, issue_id):
    """Delete an issue"""
    try:
        issue = Issue.objects.filter(id=issue_id).first()
        if not issue:
            return JsonResponse({'success': False, 'error': 'Issue not found'}, status=404)
            
        issue.delete()
        Comment.objects.filter(item_type='issue', item_id=issue_id).delete()
        return JsonResponse({
            'success': True,
            'message': f'Issue {issue_id} deleted successfully'
        })
    except Exception as e:
        logger.error(f"Error deleting issue: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def assign_issue(request, issue_id):
    """Assign an issue to a user"""
    try:
        issue = Issue.objects.filter(id=issue_id).first()
        if not issue:
            return JsonResponse({'success': False, 'error': 'Issue not found'}, status=404)
            
        data = json.loads(request.body)
        assigned_to = data.get('assigned_to', 'Unassigned')
        issue.assigned_to = assigned_to
        issue.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Issue {issue_id} assigned to {assigned_to}',
            'assigned_to': assigned_to
        })
    except Exception as e:
        logger.error(f"Error assigning issue: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["PUT"])
def update_issue_status(request, issue_id):
    """Update issue status"""
    try:
        issue = Issue.objects.filter(id=issue_id).first()
        if not issue:
            return JsonResponse({'success': False, 'error': 'Issue not found'}, status=404)
            
        data = json.loads(request.body)
        status = data.get('status')
        if not status:
            return JsonResponse({'success': False, 'error': 'Status field is required'}, status=400)
            
        issue.status = status
        issue.save()
        return JsonResponse({
            'success': True,
            'message': 'Issue status updated successfully',
            'issue': issue.to_dict()
        })
    except Exception as e:
        logger.error(f"Error updating issue status: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["PUT"])
def update_issue_priority(request, issue_id):
    """Update issue priority"""
    try:
        issue = Issue.objects.filter(id=issue_id).first()
        if not issue:
            return JsonResponse({'success': False, 'error': 'Issue not found'}, status=404)
            
        data = json.loads(request.body)
        priority = data.get('priority')
        if not priority:
            return JsonResponse({'success': False, 'error': 'Priority field is required'}, status=400)
            
        issue.priority = priority
        issue.save()
        return JsonResponse({
            'success': True,
            'message': 'Issue priority updated successfully',
            'issue': issue.to_dict()
        })
    except Exception as e:
        logger.error(f"Error updating issue priority: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

# ============================================
# TASK API ENDPOINTS
# ============================================
@require_http_methods(["GET"])
def get_tasks(request):
    """Get all tasks with filtering and pagination"""
    try:
        status = request.GET.get('status', 'all')
        priority = request.GET.get('priority', 'all')
        assigned_to = request.GET.get('assigned_to')
        search = request.GET.get('search', '')
        page = int(request.GET.get('page', 1))
        per_page = int(request.GET.get('per_page', 20))
        
        qs = Task.objects.all().order_by('-id')
        if status != 'all':
            qs = qs.filter(status=status)
        if priority != 'all':
            qs = qs.filter(priority=priority)
        if assigned_to:
            qs = qs.filter(assigned_to__icontains=assigned_to)
        if search:
            qs = qs.filter(title__icontains=search) | qs.filter(description__icontains=search)
            
        total = qs.count()
        start = (page - 1) * per_page
        end = start + per_page
        
        tasks = [t.to_dict() for t in qs[start:end]]
        return JsonResponse({
            'success': True,
            'tasks': tasks,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total,
                'total_pages': (total + per_page - 1) // per_page if total > 0 else 1
            }
        })
    except Exception as e:
        logger.error(f"Error fetching tasks: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def create_task(request):
    """Create a new task"""
    try:
        data = json.loads(request.body)
        from grl_api.api.serializers import TaskSerializer
        serializer = TaskSerializer(data=data)
        if not serializer.is_valid():
            return JsonResponse({
                'success': False,
                'error': 'Validation Error',
                'details': serializer.errors
            }, status=400)
            
        task = serializer.save()
        # Read fields directly if we need to sync parent issue or progress
        if 'progress' in data:
            task.progress = data['progress']
        if 'parent_issue' in data:
            task.parent_issue_id = data['parent_issue']
        task.save()
        
        return JsonResponse({
            'success': True,
            'task': task.to_dict(),
            'message': 'Task created successfully'
        })
    except Exception as e:
        logger.error(f"Error creating task: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@require_http_methods(["GET"])
def get_task_details(request, task_id):
    """Get detailed information about a specific task"""
    try:
        task = Task.objects.filter(id=task_id).first()
        if not task:
            return JsonResponse({'success': False, 'error': 'Task not found'}, status=404)
            
        task_data = task.to_dict()
        comments = [c.to_dict() for c in Comment.objects.filter(item_type='task', item_id=task_id).order_by('id')]
        task_data['comments'] = comments
        task_data['comment_count'] = len(comments)
        
        return JsonResponse({
            'success': True,
            'task': task_data
        })
    except Exception as e:
        logger.error(f"Error fetching task details: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["PUT"])
def update_task(request, task_id):
    """Update an existing task"""
    try:
        task = Task.objects.filter(id=task_id).first()
        if not task:
            return JsonResponse({'success': False, 'error': 'Task not found'}, status=404)
            
        data = json.loads(request.body)
        from grl_api.api.serializers import TaskSerializer
        serializer = TaskSerializer(task, data=data, partial=True)
        if not serializer.is_valid():
            return JsonResponse({
                'success': False,
                'error': 'Validation Error',
                'details': serializer.errors
            }, status=400)
            
        updated_task = serializer.save()
        if 'progress' in data:
            updated_task.progress = data['progress']
        if 'parent_issue' in data:
            updated_task.parent_issue_id = data['parent_issue']
        updated_task.save()
        
        return JsonResponse({
            'success': True,
            'task': updated_task.to_dict(),
            'message': 'Task updated successfully'
        })
    except Exception as e:
        logger.error(f"Error updating task: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["DELETE"])
def delete_task(request, task_id):
    """Delete a task"""
    try:
        task = Task.objects.filter(id=task_id).first()
        if not task:
            return JsonResponse({'success': False, 'error': 'Task not found'}, status=404)
            
        task.delete()
        Comment.objects.filter(item_type='task', item_id=task_id).delete()
        return JsonResponse({
            'success': True,
            'message': f'Task {task_id} deleted successfully'
        })
    except Exception as e:
        logger.error(f"Error deleting task: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def complete_task(request, task_id):
    """Mark a task as complete"""
    try:
        task = Task.objects.filter(id=task_id).first()
        if not task:
            return JsonResponse({'success': False, 'error': 'Task not found'}, status=404)
            
        task.status = 'completed'
        task.progress = 100
        task.save()
        return JsonResponse({
            'success': True,
            'task': task.to_dict(),
            'message': 'Task completed successfully'
        })
    except Exception as e:
        logger.error(f"Error completing task: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def assign_task(request, task_id):
    """Assign a task to a user"""
    try:
        task = Task.objects.filter(id=task_id).first()
        if not task:
            return JsonResponse({'success': False, 'error': 'Task not found'}, status=404)
            
        data = json.loads(request.body)
        assigned_to = data.get('assigned_to')
        if not assigned_to:
            return JsonResponse({'success': False, 'error': 'assigned_to is required'}, status=400)
            
        task.assigned_to = assigned_to
        task.save()
        return JsonResponse({
            'success': True,
            'message': f'Task {task_id} assigned to {assigned_to}',
            'assigned_to': assigned_to
        })
    except Exception as e:
        logger.error(f"Error assigning task: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def update_task_priority(request, task_id):
    """Update task priority"""
    try:
        task = Task.objects.filter(id=task_id).first()
        if not task:
            return JsonResponse({'success': False, 'error': 'Task not found'}, status=404)
            
        data = json.loads(request.body)
        priority = data.get('priority')
        if not priority:
            return JsonResponse({'success': False, 'error': 'Priority field is required'}, status=400)
            
        task.priority = priority
        task.save()
        return JsonResponse({
            'success': True,
            'message': 'Task priority updated successfully',
            'task': task.to_dict()
        })
    except Exception as e:
        logger.error(f"Error updating task priority: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

# ============================================
# COMMENT ENDPOINTS
# ============================================
@require_http_methods(["GET"])
def get_issue_comments(request, issue_id):
    """Get comments for an issue"""
    try:
        comments = [c.to_dict() for c in Comment.objects.filter(item_type='issue', item_id=issue_id).order_by('id')]
        return JsonResponse({'success': True, 'comments': comments})
    except Exception as e:
        logger.error(f"Error fetching issue comments: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def add_issue_comment(request, issue_id):
    """Add comment to issue"""
    try:
        data = json.loads(request.body)
        author = data.get('author', 'Anonymous')
        content = data.get('content')
        if not content:
            return JsonResponse({'success': False, 'error': 'Content is required'}, status=400)
            
        comment = Comment.objects.create(author=author, content=content, item_type='issue', item_id=issue_id)
        return JsonResponse({
            'success': True,
            'comment': comment.to_dict(),
            'message': 'Comment added successfully'
        })
    except Exception as e:
        logger.error(f"Error adding comment to issue: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@require_http_methods(["GET"])
def get_task_comments(request, task_id):
    """Get comments for a task"""
    try:
        comments = [c.to_dict() for c in Comment.objects.filter(item_type='task', item_id=task_id).order_by('id')]
        return JsonResponse({'success': True, 'comments': comments})
    except Exception as e:
        logger.error(f"Error fetching task comments: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def add_task_comment(request, task_id):
    """Add comment to task"""
    try:
        data = json.loads(request.body)
        author = data.get('author', 'Anonymous')
        content = data.get('content')
        if not content:
            return JsonResponse({'success': False, 'error': 'Content is required'}, status=400)
            
        comment = Comment.objects.create(author=author, content=content, item_type='task', item_id=task_id)
        return JsonResponse({
            'success': True,
            'comment': comment.to_dict(),
            'message': 'Comment added successfully'
        })
    except Exception as e:
        logger.error(f"Error adding comment to task: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

# ============================================
# ANALYTICS & BULK OPERATIONS
# ============================================
@require_http_methods(["GET"])
def get_issues_analytics(request):
    """Get analytics for issues"""
    try:
        total = Issue.objects.count()
        analytics = {
            'total': total,
            'open': Issue.objects.filter(status='open').count(),
            'in_progress': Issue.objects.filter(status='in_progress').count(),
            'review': Issue.objects.filter(status='review').count(),
            'closed': Issue.objects.filter(status='closed').count(),
            'blocked': Issue.objects.filter(status='blocked').count(),
            'critical': Issue.objects.filter(priority='critical').count(),
            'high': Issue.objects.filter(priority='high').count(),
            'medium': Issue.objects.filter(priority='medium').count(),
            'low': Issue.objects.filter(priority='low').count()
        }
        return JsonResponse({'success': True, 'analytics': analytics})
    except Exception as e:
        logger.error(f"Error getting issues analytics: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@require_http_methods(["GET"])
def get_tasks_analytics(request):
    """Get analytics for tasks"""
    try:
        total = Task.objects.count()
        progress_sum = sum(t.progress for t in Task.objects.all())
        analytics = {
            'total': total,
            'pending': Task.objects.filter(status='pending').count(),
            'in_progress': Task.objects.filter(status='in_progress').count(),
            'review': Task.objects.filter(status='review').count(),
            'completed': Task.objects.filter(status='completed').count(),
            'critical': Task.objects.filter(priority='critical').count(),
            'high': Task.objects.filter(priority='high').count(),
            'medium': Task.objects.filter(priority='medium').count(),
            'low': Task.objects.filter(priority='low').count(),
            'avg_progress': (progress_sum / total) if total > 0 else 0
        }
        return JsonResponse({'success': True, 'analytics': analytics})
    except Exception as e:
        logger.error(f"Error getting tasks analytics: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@require_http_methods(["GET"])
def get_dashboard_stats(request):
    """Get combined dashboard statistics"""
    try:
        now = datetime.now()
        last_week = now - timedelta(days=7)
        stats = {
            'issues': {
                'total': Issue.objects.count(),
                'open': Issue.objects.filter(status='open').count(),
                'critical': Issue.objects.filter(priority='critical').count()
            },
            'tasks': {
                'total': Task.objects.count(),
                'pending': Task.objects.filter(status='pending').count(),
                'in_progress': Task.objects.filter(status='in_progress').count(),
                'completed': Task.objects.filter(status='completed').count()
            },
            'recent': {
                'issues': Issue.objects.filter(created_at__gte=last_week).count(),
                'tasks': Task.objects.filter(created_at__gte=last_week).count()
            }
        }
        return JsonResponse({'success': True, 'stats': stats})
    except Exception as e:
        logger.error(f"Error getting dashboard stats: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def bulk_update_issues(request):
    """Bulk update multiple issues"""
    try:
        data = json.loads(request.body)
        issue_ids = data.get('issue_ids', [])
        updates = data.get('updates', {})
        
        if not issue_ids:
            return JsonResponse({'success': False, 'error': 'No issue IDs provided'}, status=400)
            
        Issue.objects.filter(id__in=issue_ids).update(**updates)
        return JsonResponse({
            'success': True,
            'updated_count': len(issue_ids),
            'message': f'Successfully updated {len(issue_ids)} issues'
        })
    except Exception as e:
        logger.error(f"Error in bulk update: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def bulk_update_tasks(request):
    """Bulk update multiple tasks"""
    try:
        data = json.loads(request.body)
        task_ids = data.get('task_ids', [])
        updates = data.get('updates', {})
        
        if not task_ids:
            return JsonResponse({'success': False, 'error': 'No task IDs provided'}, status=400)
            
        Task.objects.filter(id__in=task_ids).update(**updates)
        return JsonResponse({
            'success': True,
            'updated_count': len(task_ids),
            'message': f'Successfully updated {len(task_ids)} tasks'
        })
    except Exception as e:
        logger.error(f"Error in bulk update: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

# ============================================
# EXPORT & SEARCH
# ============================================
@require_http_methods(["GET"])
def export_issues(request):
    """Export issues as CSV"""
    try:
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['ID', 'Title', 'Status', 'Priority', 'Assigned To', 'Created By', 'Created At', 'Due Date'])
        
        for issue in Issue.objects.all().order_by('id'):
            writer.writerow([
                issue.id,
                issue.title,
                issue.status,
                issue.priority,
                issue.assigned_to,
                issue.created_by,
                issue.created_at.strftime("%Y-%m-%d %H:%M:%S") if issue.created_at else '',
                issue.due_date or ''
            ])
            
        response = HttpResponse(output.getvalue(), content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="issues_{datetime.now().strftime("%Y%m%d")}.csv"'
        return response
    except Exception as e:
        logger.error(f"Error exporting issues: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@require_http_methods(["GET"])
def export_tasks(request):
    """Export tasks as CSV"""
    try:
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['ID', 'Title', 'Status', 'Priority', 'Assigned To', 'Progress', 'Created At', 'Due Date'])
        
        for task in Task.objects.all().order_by('id'):
            writer.writerow([
                task.id,
                task.title,
                task.status,
                task.priority,
                task.assigned_to,
                f"{task.progress}%",
                task.created_at.strftime("%Y-%m-%d %H:%M:%S") if task.created_at else '',
                task.due_date or ''
            ])
            
        response = HttpResponse(output.getvalue(), content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="tasks_{datetime.now().strftime("%Y%m%d")}.csv"'
        return response
    except Exception as e:
        logger.error(f"Error exporting tasks: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@require_http_methods(["GET"])
def search_issues(request):
    """Search issues by keyword"""
    try:
        query = request.GET.get('q', '')
        if not query:
            return JsonResponse({'success': True, 'issues': []})
            
        qs = Issue.objects.filter(title__icontains=query) | Issue.objects.filter(description__icontains=query)
        results = [i.to_dict() for i in qs[:50]]
        return JsonResponse({'success': True, 'issues': results})
    except Exception as e:
        logger.error(f"Error searching issues: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@require_http_methods(["GET"])
def search_tasks(request):
    """Search tasks by keyword"""
    try:
        query = request.GET.get('q', '')
        if not query:
            return JsonResponse({'success': True, 'tasks': []})
            
        qs = Task.objects.filter(title__icontains=query) | Task.objects.filter(description__icontains=query)
        results = [t.to_dict() for t in qs[:50]]
        return JsonResponse({'success': True, 'tasks': results})
    except Exception as e:
        logger.error(f"Error searching tasks: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

# ============================================
# NOTIFICATIONS (MOCK PER SISTENCY)
# ============================================
@require_http_methods(["GET"])
def get_notifications(request):
    """Get user notifications"""
    try:
        # Simple notifications related to open/high-priority items in DB
        notifications = []
        critical_issues = Issue.objects.filter(priority='critical') | Issue.objects.filter(priority='high')
        for i, issue in enumerate(critical_issues[:3]):
            notifications.append({
                'id': i + 1,
                'type': 'issue_assigned',
                'content': f"High-priority issue alert: {issue.title} assigned to {issue.assigned_to}",
                'created_at': issue.created_at.isoformat() if issue.created_at else datetime.now().isoformat(),
                'read': False,
                'related_id': issue.id
            })
        
        # Fallback default if DB is freshly seeded
        if not notifications:
            notifications = [
                {
                    'id': 1,
                    'type': 'issue_assigned',
                    'content': 'You have been assigned to issue: Fix login bug',
                    'created_at': datetime.now().isoformat(),
                    'read': False,
                    'related_id': 1
                }
            ]
            
        return JsonResponse({
            'success': True,
            'notifications': notifications,
            'count': len(notifications)
        })
    except Exception as e:
        logger.error(f"Error fetching notifications: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def mark_notifications_read(request):
    """Mark notifications as read (stub)"""
    try:
        return JsonResponse({'success': True, 'message': 'Notifications marked as read'})
    except Exception as e:
        logger.error(f"Error marking notifications read: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)