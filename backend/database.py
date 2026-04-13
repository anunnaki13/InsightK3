import os

import gridfs
import pymongo
from motor.motor_asyncio import AsyncIOMotorClient

mongo_url = os.environ["MONGO_URL"]
db_name = os.environ["DB_NAME"]

client = AsyncIOMotorClient(mongo_url)
db = client[db_name]

sync_client = pymongo.MongoClient(mongo_url)
sync_db = sync_client[db_name]
fs = gridfs.GridFS(sync_db)
