import json
from django.test import TestCase, Client
from django.urls import reverse
from grl_api.models import Issue, Task, Comment

class APIRobustnessTestCase(TestCase):
    def setUp(self):
        self.client = Client()

    def test_api_v1_routing_and_health_check(self):
        """Verify that health check works under /api/v1/health/"""
        response = self.client.get('/api/v1/health/')
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertEqual(data.get('status'), 'healthy')

    def test_api_index_endpoints_schema(self):
        """Verify the API index endpoints use the v1 prefix"""
        response = self.client.get('/api/v1/')
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertEqual(data.get('status'), 'success')
        self.assertIn('v1', data.get('message'))
        
        endpoints = data.get('endpoints', {})
        self.assertEqual(endpoints.get('health'), '/api/v1/health/')
        self.assertEqual(endpoints.get('UIChecks'), '/api/v1/UIChecks/')

    def test_issue_serializer_validation_failure(self):
        """Verify that creating an issue without a title fails with 400 validation error"""
        payload = {
            "description": "This issue is missing a title parameter",
            "priority": "high"
        }
        
        response = self.client.post(
            '/api/v1/IssuesAndTasksTracking/api/issues/create/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertEqual(data.get('success'), False)
        self.assertEqual(data.get('error'), 'Validation Error')
        self.assertIn('title', data.get('details'))

    def test_issue_serializer_validation_success(self):
        """Verify that creating an issue with a title succeeds in the database"""
        payload = {
            "title": "Bug: Test Execution Fails",
            "description": "Detailed bug description",
            "priority": "high",
            "assigned_to": "Engineer",
            "tags": ["bug", "high-priority"]
        }
        
        # Verify db is empty
        self.assertEqual(Issue.objects.count(), 0)
        
        response = self.client.post(
            '/api/v1/IssuesAndTasksTracking/api/issues/create/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data.get('success'), True)
        self.assertEqual(data.get('issue', {}).get('title'), "Bug: Test Execution Fails")
        
        # Verify database record exists
        self.assertEqual(Issue.objects.count(), 1)
        db_issue = Issue.objects.first()
        self.assertEqual(db_issue.title, "Bug: Test Execution Fails")
        self.assertEqual(db_issue.priority, "high")

    def test_issue_details_with_comments(self):
        """Verify fetching issue details returns seeded comments"""
        # Seed an issue and comment
        issue = Issue.objects.create(title="Sample Issue", priority="medium")
        Comment.objects.create(author="Alice", content="This is a comment", item_type="issue", item_id=issue.id)
        
        response = self.client.get(f'/api/v1/IssuesAndTasksTracking/api/issues/{issue.id}/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data.get('success'), True)
        self.assertEqual(data.get('issue', {}).get('comment_count'), 1)
        self.assertEqual(data.get('issue', {}).get('comments', [])[0]['author'], "Alice")
