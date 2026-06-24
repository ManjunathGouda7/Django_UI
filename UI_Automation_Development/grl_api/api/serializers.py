from rest_framework import serializers
from grl_api.models import Issue, Task

class TestcaseHeaderSerializer(serializers.Serializer):
    TestID = serializers.CharField(max_length=100)
    TestName = serializers.CharField(max_length=200, required=False, allow_blank=True)
    Description = serializers.CharField(max_length=1000, required=False, allow_blank=True)
    Product = serializers.CharField(max_length=100)
    Category = serializers.CharField(max_length=100)
    Testsuits = serializers.ListField(child=serializers.CharField(), required=False, default=list)
    TestTags = serializers.ListField(child=serializers.CharField(), required=False, default=list)

class IssueSerializer(serializers.ModelSerializer):
    class Meta:
        model = Issue
        fields = '__all__'
        extra_kwargs = {
            'title': {'required': True, 'error_messages': {'required': 'Title is required'}}
        }

class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = '__all__'
        extra_kwargs = {
            'title': {'required': True, 'error_messages': {'required': 'Title is required'}}
        }
