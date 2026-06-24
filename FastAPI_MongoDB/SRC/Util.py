import json
import os
import sys
from motor.motor_asyncio import AsyncIOMotorClient
import aiosqlite
import redis
from urllib.parse import quote_plus
import logging
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

class JsonOperations:
    def __init__(self,path):
        self.path =path
    def read_file(self):
        try:
            with open(self.path, "r", encoding="utf-8") as rf:
                values = json.load(rf)
            return values
        except Exception as e:
            print("Read File Error :",e)
    def update_file(self,values):
        with open(self.path, "w") as outfile:
            json.dump(values, outfile)
 
class DBmodule:
    def __init__(self):
        username = quote_plus(os.getenv("MONGO_USER", "admin"))
        password_raw = os.getenv("MONGO_PASS")
        if not password_raw:
            raise ValueError("MONGO_PASS environment variable is not set")
        password = quote_plus(password_raw)
        host = os.getenv("MONGO_HOST", "localhost")
        port = os.getenv("MONGO_PORT", "27017")

        # self.mongo_url = "mongodb://192.168.101.233:27017/"
        self.mongo_url = f"mongodb://{username}:{password}@{host}:{port}/"

        self.client = AsyncIOMotorClient(
            self.mongo_url,
            serverSelectionTimeoutMS=3000
        )

    async def check_connection(self):
        try:
            await self.client.admin.command("ping")
            return {"status": "connected"}
        except Exception as e:
            return {"status": "failed", "error": str(e)}
        
    def get_database(self,db_name: str):
        return self.client[db_name]

    def get_collection(self,db_name: str, collection_name: str):
        return self.client[db_name][collection_name]
    
class SQLiteModule:
    async def get_sqlite():
        return await aiosqlite.connect("offline.db")

class RedisServices():

    def __init__(self):
        redis_password = os.getenv("REDIS_PASS")
        if not redis_password:
            raise ValueError("REDIS_PASS environment variable is not set")
        self.redis_client = redis.Redis(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", 6379)),
            password=redis_password,
            decode_responses=True
        )
        self.QUEUE_NAME = "execution_queue"

    def push_jobs(self, job):
        self.redis_client.lpush(self.QUEUE_NAME, json.dumps(job))

    def get_jobs(self):
        return self.redis_client.lrange(self.QUEUE_NAME, 0, -1)

    def queue_length(self):
        return self.redis_client.llen(self.QUEUE_NAME)

    def delete_job_by_id(self, job_id):
        jobs = self.redis_client.lrange(self.QUEUE_NAME, 0, -1)
        for job in jobs:
            job_data = json.loads(job)
            if job_data["JobID"] == job_id:
                self.redis_client.lrem(self.QUEUE_NAME, 1, job)
                return True
        return False
    def delete_all_jobs(self):
        self.redis_client.delete(self.QUEUE_NAME)
    
class GeneralFunctions:
    def get_path(relative_path):
        """Resolve paths for both dev and packaged (PyInstaller) runs.

        The codebase expects relative paths like:
        - assets/Input.json
        - FastAPI_MongoDB/Modules/UIchecks/pipelines.json

        When running from Django, the working directory may be different.
        We therefore resolve relative paths from the repo root.
        """
        if hasattr(sys, '_MEIPASS'):
            return os.path.join(sys._MEIPASS, relative_path)

        # Default: resolve from current working directory.
        cwd_resolved = os.path.join(os.path.abspath("."), relative_path)
        if os.path.exists(cwd_resolved):
            return cwd_resolved

        # Repo root: d:/MG/MG UI (two levels up from FastAPI_MongoDB/SRC)
        try:
            repo_root = Path(__file__).resolve().parents[2]
            return str(repo_root / relative_path)
        except Exception:
            # Fallback
            return os.path.join(os.path.abspath("."), relative_path)

    
    def GetValuefromJSON(path:str,Jdata:dict):
        try:
            pathlist = path.split('->')
            value = Jdata
            for key in pathlist:
                value = value[key]
            return value
        except Exception as e:
            return None
    
    def Logger():
        os.makedirs("assets/logs", exist_ok=True)
        LOG_FILE = datetime.now().strftime("logs/automation_%Y%m%d_%H%M%S.log")
        logger = logging.getLogger("AutomationFramework")
        if not logger.handlers:
            logger.setLevel(logging.INFO)
            formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")
            # File Handler
            file_handler = logging.FileHandler(LOG_FILE)
            file_handler.setFormatter(formatter)

            # Console Handler
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)

            logger.addHandler(file_handler)
            logger.addHandler(console_handler)


# db = DBmodule()
# result = db.get_collection("UIDB","Inputs")
# v= existing = result.find_one({'Header':'TestTags'})
# print(v)

# r = RedisServices()

# try:
#     print(r.redis_client.ping())
# except Exception as e:
#     print(e)