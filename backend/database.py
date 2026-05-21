import asyncio
import os
from pathlib import Path
from typing import Any

import gridfs
import mongomock
import pymongo
from bson import json_util
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
from mongomock.gridfs import enable_gridfs_integration
from mongomock_motor import AsyncMongoMockClient

load_dotenv(Path(__file__).parent / ".env")

mongo_url = os.environ["MONGO_URL"]
db_name = os.environ["DB_NAME"]
use_mock_db = os.environ.get("MONGO_USE_MOCK", "").strip().lower() in {"1", "true", "yes"}
mock_state_dir = Path(__file__).parent / ".mock_state"
mock_metadata_path = mock_state_dir / "metadata.json"
mock_gridfs_path = mock_state_dir / "gridfs.json"
_mock_state_dirty = False
_mock_state_lock = asyncio.Lock()
_mock_gridfs_loaded = False
_mock_gridfs_lock = asyncio.Lock()

if use_mock_db:
    enable_gridfs_integration()
    client = AsyncMongoMockClient()
    db = client[db_name]
    sync_client = mongomock.MongoClient()
else:
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    sync_client = pymongo.MongoClient(mongo_url)

sync_db = sync_client[db_name]
fs = gridfs.GridFS(sync_db)


def mark_mock_state_dirty() -> None:
    global _mock_state_dirty
    if use_mock_db:
        _mock_state_dirty = True


def clear_mock_state_dirty() -> None:
    global _mock_state_dirty
    if use_mock_db:
        _mock_state_dirty = False


async def restore_mock_state(load_gridfs: bool = True) -> None:
    if not use_mock_db:
        return

    if mock_metadata_path.exists():
        metadata = json_util.loads(mock_metadata_path.read_text(encoding="utf-8"))
        for collection_name, documents in metadata.items():
            await db[collection_name].delete_many({})
            if documents:
                await db[collection_name].insert_many(documents)

    if load_gridfs:
        await restore_mock_gridfs_state()


async def restore_mock_gridfs_state() -> None:
    global _mock_gridfs_loaded

    if not use_mock_db:
        return

    async with _mock_gridfs_lock:
        if _mock_gridfs_loaded:
            return

        if mock_gridfs_path.exists():
            gridfs_state = json_util.loads(mock_gridfs_path.read_text(encoding="utf-8"))
            for collection_name, documents in gridfs_state.items():
                for document in documents:
                    if "_id" in document:
                        sync_db[collection_name].replace_one({"_id": document["_id"]}, document, upsert=True)
                    else:
                        sync_db[collection_name].insert_one(document)

        _mock_gridfs_loaded = True


async def ensure_mock_gridfs_loaded() -> None:
    if use_mock_db:
        await restore_mock_gridfs_state()


async def persist_mock_state(force: bool = False) -> None:
    global _mock_state_dirty

    if not use_mock_db:
        return
    if not force and not _mock_state_dirty:
        return

    async with _mock_state_lock:
        if not force and not _mock_state_dirty:
            return

        mock_state_dir.mkdir(parents=True, exist_ok=True)

        metadata: dict[str, list[dict[str, Any]]] = {}
        for collection_name in await db.list_collection_names():
            metadata[collection_name] = await db[collection_name].find({}, {"_id": 0}).to_list(20000)

        metadata_tmp = mock_metadata_path.with_suffix(".tmp")
        metadata_tmp.write_text(json_util.dumps(metadata, ensure_ascii=False), encoding="utf-8")
        metadata_tmp.replace(mock_metadata_path)

        if _mock_gridfs_loaded:
            gridfs_state: dict[str, list[dict[str, Any]]] = {}
            for collection_name in sync_db.list_collection_names():
                gridfs_state[collection_name] = list(sync_db[collection_name].find({}))

            gridfs_tmp = mock_gridfs_path.with_suffix(".tmp")
            gridfs_tmp.write_text(json_util.dumps(gridfs_state, ensure_ascii=False), encoding="utf-8")
            gridfs_tmp.replace(mock_gridfs_path)

        _mock_state_dirty = False
