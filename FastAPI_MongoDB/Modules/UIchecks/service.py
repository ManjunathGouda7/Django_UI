import redis
import json

class RedisServices():
    def __init__(self):
        self.redis_client = redis.Redis(host="localhoist",port=6379,decode_responses=True)
        self.QUEUE_NAME = "execution_queue"
    
    def push_jobs(self,job):
        self.redis_client.lpush(self.QUEUE_NAME,json.dumps(job))
