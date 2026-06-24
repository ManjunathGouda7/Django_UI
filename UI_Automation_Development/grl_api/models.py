from django.db import models

class Issue(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, default='')
    status = models.CharField(max_length=20, default='open')
    priority = models.CharField(max_length=20, default='medium')
    assigned_to = models.CharField(max_length=100, default='Unassigned')
    created_by = models.CharField(max_length=100, default='Anonymous')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    due_date = models.CharField(max_length=100, blank=True, null=True, default=None)
    tags = models.JSONField(default=list, blank=True)

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'status': self.status,
            'priority': self.priority,
            'assigned_to': self.assigned_to,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'due_date': self.due_date,
            'tags': self.tags or [],
            'comment_count': Comment.objects.filter(item_type='issue', item_id=self.id).count()
        }

class Task(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, default='')
    status = models.CharField(max_length=20, default='pending')
    priority = models.CharField(max_length=20, default='medium')
    assigned_to = models.CharField(max_length=100, default='Unassigned')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    due_date = models.CharField(max_length=100, blank=True, null=True, default=None)
    progress = models.IntegerField(default=0)
    parent_issue_id = models.IntegerField(blank=True, null=True)

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'status': self.status,
            'priority': self.priority,
            'assigned_to': self.assigned_to,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'due_date': self.due_date,
            'progress': self.progress,
            'parent_issue': self.parent_issue_id,
            'comment_count': Comment.objects.filter(item_type='task', item_id=self.id).count()
        }

class Comment(models.Model):
    author = models.CharField(max_length=100, default='Anonymous')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    item_type = models.CharField(max_length=20) # issue / task
    item_id = models.IntegerField()

    def to_dict(self):
        return {
            'id': self.id,
            'author': self.author,
            'content': self.content,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'item_type': self.item_type,
            'item_id': self.item_id
        }
