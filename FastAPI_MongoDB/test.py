# # import traceback
# # import asyncio
# # from SRC.Util import DBmodule,JsonOperations
# # DBmod = DBmodule()
# # inputs_Collection = DBmod.get_collection("UIDB","Inputs")
# # Testcases_Collection = DBmod.get_collection("UIDB","Testcases")
# # POM_Collection = DBmod.get_collection("UIDB","POM")

# # async def test(TestID):
# #     try:
# #         projection={
# #         "_id":0,
# #         "Details.StepID":1,
# #         "Details.Description":1,
# #         }

# #         existing = await Testcases_Collection.find_one({'TestID':"Test01q"})
# #         print(existing)
# #         # if len(testcases)>0:

# #         # print(testcases)
# #         # print(testcases[0]['Details'])


# #         # stepcnt = len(TCs['Details'])+1
# #         # StepID = f"{TestID}_{str(stepcnt).zfill(3)}"
# #         # print(TCs)
# #         # while True:
# #         #     stepsexist = await Testcases_Collection.find_one({"TestID": TestID,"Details.StepID": StepID})
# #         #     print(stepsexist)
# #         #     if stepsexist is None:
# #         #         break
# #         #     else:
# #         #         print(StepID)
# #         #         StepID = f"{TestID}_{str(stepcnt+1).zfill(3)}"
# #         # print(StepID)
# #     except Exception:
# #         traceback.print_exc()

# # asyncio.run(test('Test01'))

# import os
# from urllib.parse import quote_plus
# from motor.motor_asyncio import AsyncIOMotorClient
# from dotenv import load_dotenv
# import asyncio


# class MongoDBService:

#     def __init__(self):
#         load_dotenv()

#         username = quote_plus(os.getenv("MONGO_USER", "admin"))
#         password = quote_plus(os.getenv("MONGO_PASS", "Grl@2026"))
#         host = os.getenv("MONGO_HOST", "localhost")
#         port = os.getenv("MONGO_PORT", "27017")

#         self.mongo_url = f"mongodb://{username}:{password}@{host}:{port}/"

#         self.client = AsyncIOMotorClient(
#             self.mongo_url,
#             serverSelectionTimeoutMS=3000
#         )

#     async def check_connection(self):
#         try:
#             await self.client.admin.command("ping")
#             return {"status": "connected"}
#         except Exception as e:
#             return {"status": "failed", "error": str(e)}

#     def get_database(self, db_name: str):
#         return self.client[db_name]

#     def get_collection(self, db_name: str, collection_name: str):
#         return self.client[db_name][collection_name]


# db = MongoDBService()

# async def main():
#     result = await db.check_connection()
#     print(result)

# asyncio.run(main())

import json

Value =  "{\"Type\": \"Direct\", \"Value\": \"False\"}"

d = json.loads(Value)

print(type(d['Value']))