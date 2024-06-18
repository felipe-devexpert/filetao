import pandas as pd
import datetime
import time
import threading
import uvicorn

from typing import List, Dict, Union
from time import time
from pydantic import BaseModel
from fastapi import FastAPI
from redis import asyncio as aioredis

from .sqlite import query

app = FastAPI()

class MinerStatItem(BaseModel):
    TIMESTAMP: str
    HOTKEY: str
    INCENTIVE: int
    EMISSION: int
    TIER: str
    CURRENT_STORAGE: int
    CAPACITY: int
    PERCENT_USAGE: float
    NUM_HASHES: int
    TOTAL_SUCCESSES: int
    STORE_SUCCESSES: int
    STORE_ATTEMPTS: int
    CHALLENGE_SUCCESSES: int
    CHALLENGE_ATTEMPTS: int
    RETRIEVE_SUCCESSES: int
    RETRIEVE_ATTEMPTS: int

MINER_QUERY = """SELECT * FROM HotkeysTable WHERE timestamp BETWEEN datetime(?, 'unixepoch') AND datetime(?, 'unixepoch') ORDER BY timestamp DESC LIMIT ? OFFSET ?"""

@app.get("/miner_statistics", response_model=List[MinerStatItem])
async def get_miner_statistics_endpoint(start_time: Union[int, None] = None, end_time: Union[int, None] = None, limit: int = 50, offset: int = 0):
    if not start_time:
        now = time()
        start_time = int(now) - 3600

    if not end_time:
        now = time()
        end_time = int(now)

    miner_data = query(MINER_QUERY, [start_time, end_time, limit, offset])
    if not miner_data:
        return []

    data_rows = []

    for (
        id,
        timestamp,
        hotkey,
        incentive,
        emission,
        tier,
        current_storage,
        capacity,
        percent_usage,
        num_hashes,
        total_successes,
        store_successes,
        store_attempts,
        challenge_successes,
        challenge_attempts,
        retrieve_successes,
        retrieve_attempts
    ) in miner_data:
        row = MinerStatItem(
            TIMESTAMP=timestamp,
            HOTKEY=hotkey,
            INCENTIVE=incentive,
            EMISSION=emission,
            TIER=tier,
            CURRENT_STORAGE=current_storage,
            CAPACITY=capacity,
            PERCENT_USAGE=percent_usage,
            NUM_HASHES=num_hashes,
            TOTAL_SUCCESSES=total_successes,
            STORE_SUCCESSES=store_successes,
            STORE_ATTEMPTS=store_attempts,
            CHALLENGE_SUCCESSES=challenge_successes,
            CHALLENGE_ATTEMPTS=challenge_attempts,
            RETRIEVE_SUCCESSES=retrieve_successes,
            RETRIEVE_ATTEMPTS=retrieve_attempts,
        )
        data_rows.append(row.dict())

    return data_rows

SPECIFIC_MINER_QUERY = """SELECT * FROM HotkeysTable WHERE (timestamp BETWEEN datetime(?, 'unixepoch') AND datetime(?, 'unixepoch')) AND hotkey == ? ORDER BY timestamp DESC LIMIT ? OFFSET ?"""

@app.get("/miner/{search_hotkey}", response_model=List[MinerStatItem])
async def get_specific_miner_stats(search_hotkey: str, start_time: Union[int, None] = None, end_time: Union[int, None] = None, limit: int = 50, offset: int = 0):
    if not start_time:
        now = time()
        start_time = int(now) - 3600

    if not end_time:
        now = time()
        end_time = int(now)

    miner_data = query(SPECIFIC_MINER_QUERY, [start_time, end_time, search_hotkey, limit, offset])
    if not miner_data:
        return []

    data_rows = []

    for (
        id,
        timestamp,
        hotkey,
        incentive,
        emission,
        tier,
        current_storage,
        capacity,
        percent_usage,
        num_hashes,
        total_successes,
        store_successes,
        store_attempts,
        challenge_successes,
        challenge_attempts,
        retrieve_successes,
        retrieve_attempts
    ) in miner_data:
        row = MinerStatItem(
            TIMESTAMP=timestamp,
            HOTKEY=hotkey,
            INCENTIVE=incentive,
            EMISSION=emission,
            TIER=tier,
            CURRENT_STORAGE=current_storage,
            CAPACITY=capacity,
            PERCENT_USAGE=percent_usage,
            NUM_HASHES=num_hashes,
            TOTAL_SUCCESSES=total_successes,
            STORE_SUCCESSES=store_successes,
            STORE_ATTEMPTS=store_attempts,
            CHALLENGE_SUCCESSES=challenge_successes,
            CHALLENGE_ATTEMPTS=challenge_attempts,
            RETRIEVE_SUCCESSES=retrieve_successes,
            RETRIEVE_ATTEMPTS=retrieve_attempts,
        )
        data_rows.append(row.dict())

    return data_rows

class TierStatItem(BaseModel):
    TIMESTAMP: str
    TIER: str
    COUNTS: int
    CAPACITY: int
    CURRENT_STORAGE: int
    PERCENT_USAGE: float
    CURRENT_ATTEMPTS: int
    CURRENT_SUCCESSES: int
    GLOBAL_SUCCESS_RATE: float
    TOTAL_GLOBAL_SUCCESSES: int

TIERS_QUERY = """SELECT * FROM TierStatsTable WHERE timestamp BETWEEN datetime(?, 'unixepoch') AND datetime(?, 'unixepoch') ORDER BY timestamp DESC LIMIT ? OFFSET ?"""

@app.get("/tiers_data", response_model=List[TierStatItem])
async def get_tiers_data_endpoint(start_time: Union[int, None] = None, end_time: Union[int, None] = None, limit: int = 50, offset: int = 0):
    if not start_time:
        now = time()
        start_time = int(now) - 3600

    if not end_time:
        now = time()
        end_time = int(now)

    tiers_data = query(TIERS_QUERY, [start_time, end_time, limit, offset])
    if not tiers_data:
        return []

    data_rows = []

    for (
        id,
        timestamp,
        tier,
        counts,
        capacity,
        current_storage,
        percent_usage,
        current_attempts,
        current_successes,
        global_success_rate,
        total_global_successes
    ) in tiers_data:
        row = TierStatItem(
            TIMESTAMP=timestamp,
            TIER=tier,
            COUNTS=counts,
            CAPACITY=capacity,
            CURRENT_STORAGE=current_storage,
            PERCENT_USAGE=percent_usage,
            CURRENT_ATTEMPTS=current_attempts,
            CURRENT_SUCCESSES=current_successes,
            GLOBAL_SUCCESS_RATE=global_success_rate,
            TOTAL_GLOBAL_SUCCESSES=total_global_successes
        )
        data_rows.append(row.dict())

    return data_rows

class NetworkDataItem(BaseModel):
    TIMESTAMP: str
    CURRENT_STORAGE: int
    NETWORK_CAPACITY: int
    TOTAL_SUCCESSFUL_REQUESTS: int
    REDIS_INDEX_SIZE_MB: int
    GLOBAL_CURRENT_ATTEMPTS: int
    GLOBAL_CURRENT_SUCCESSES: int
    GLOBAL_CURRENT_SUCCESS_RATE: float
    TOTAL_EMISSION: int

NETWORK_QUERY = """SELECT * FROM NetworkStatsTable WHERE timestamp BETWEEN datetime(?, 'unixepoch') AND datetime(?, 'unixepoch') ORDER BY timestamp DESC LIMIT ? OFFSET ?"""

@app.get("/network_data", response_model=List[NetworkDataItem])
async def get_network_data_endpoint(start_time: Union[int, None] = None, end_time: Union[int, None] = None, limit: int = 50, offset: int = 0):
    if not start_time:
        now = time()
        start_time = int(now) - 3600

    if not end_time:
        now = time()
        end_time = int(now)

    network_data = query(NETWORK_QUERY, [start_time, end_time, limit, offset])
    if not network_data:
        return []

    data_rows = []

    for (
        id,
        timestamp,
        current_storage,
        network_capacity,
        total_successful_requests,
        redis_index_size_mb,
        global_current_attempts,
        global_current_successes,
        global_current_success_rate,
        total_emission
    ) in network_data:
        row = NetworkDataItem(
            TIMESTAMP=timestamp,
            CURRENT_STORAGE=current_storage,
            NETWORK_CAPACITY=network_capacity,
            TOTAL_SUCCESSFUL_REQUESTS=total_successful_requests,
            REDIS_INDEX_SIZE_MB=redis_index_size_mb,
            GLOBAL_CURRENT_ATTEMPTS=global_current_attempts,
            GLOBAL_CURRENT_SUCCESSES=global_current_successes,
            GLOBAL_CURRENT_SUCCESS_RATE=global_current_success_rate,
            TOTAL_EMISSION=total_emission
        )
        data_rows.append(row.dict())

    return data_rows

def startup():
    uvicorn.run(app, host="0.0.0.0", port=8000, server_header=False)

def run_in_thread():
    thread = threading.Thread(target=startup, daemon=True)
    thread.start()