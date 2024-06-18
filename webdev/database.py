import json
import torch
import bittensor as bt

import os
from os import getenv
from redis import StrictRedis
from datetime import datetime
from pydantic import BaseModel
from typing import Optional, Union, List

redis_db = None

os.environ["REDIS_DB"] = "2"

METAGRAPH_ATTRIBUTES = [
    "n",
    "block",
    "stake",
    "total_stake",
    "ranks",
    "trust",
    "consensus",
    "validator_trust",
    "incentive",
    "emission",
    "dividends",
    "active",
    "last_update",
    "validator_permit",
    "weights",
    "bonds",
    "uids"
]


def get_database() -> StrictRedis:
    redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
    redis_password = os.getenv('REDIS_PASSWORD')  # Retrieve password from environment
    # Include the password in the connection
    return StrictRedis.from_url(redis_url, password=redis_password, db=os.getenv("REDIS_DB", 2)) if redis_db is None else redis_db

def startup():
    global redis_db
    redis_db = get_database()
    if redis_db.get("service:has_launched") is None:
        redis_db.set("service:service", "UserDatabase")
        redis_db.set("service:userCount", "0")
        redis_db.set("service:totalFiles", "0")
        redis_db.set("service:has_launched", "True")

    redis_db.set("service:started", datetime.today().ctime())

def get_server_wallet():
    server_wallet = bt.wallet(name="server", hotkey="default")
    server_wallet.create_if_non_existent(coldkey_use_password=False)
    if redis_db.hget("server_wallet", "name") is None:
        server_wallet.create(coldkey_use_password=False, hotkey_use_password=False)
        redis_db.hset("server_wallet", "name", server_wallet.name)
        redis_db.hset("server_wallet", "hotkey", server_wallet.hotkey.ss58_address)
        redis_db.hset("server_wallet", "mnemonic", server_wallet.coldkey.mnemonic)

    return server_wallet

# User Model and Database
class User(BaseModel):
    username: str
    user_max_storage: int
    user_current_storage: int

class UserInDB(User):
    hashed_password: str
    seed: str
    wallet_name: str
    wallet_hotkey: str
    wallet_mnemonic: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

def serialize_model(model: BaseModel) -> str:
    """Serialize Pydantic model to JSON string."""
    return model.json()

def deserialize_model(model_str: str, model_class: type) -> BaseModel:
    """Deserialize JSON string back into Pydantic model."""
    return model_class.parse_raw(model_str)

def get_user(username: str) -> Optional[UserInDB]:
    user_str = redis_db.get("user:" + username)
    if user_str:
        return deserialize_model(user_str, UserInDB)
    return None

def create_user(user: UserInDB):
    username = user.username
    user_str = serialize_model(user)
    redis_db.set("user:" + username, user_str)
    redis_db.set("storage:" + username, 0)
    redis_db.set("usercap:" + username, 1024 ** 3 * 5) # 5 GB init capacity
    redis_db.incr("service:userCount")

def update_user(user: UserInDB):
    username = user.username
    user_str = serialize_model(user)
    redis_db.set("user:" + username, user_str)

def get_server_stats():
    return {
        "userCount": int(redis_db.get("service:userCount")),
        "totalFiles": int(redis_db.get("service:totalFiles")),
        "started": redis_db.get("service:started").decode(),
    }

def get_user_stats(username: str):
    return {
        "filecount" : int(redis_db.get("filecount:" + username) or 0),
        "storage" : int(redis_db.get("storage:" + username) or 0),
        "usercap" : int(redis_db.get("usercap:" + username)),
    }

def store_file_metadata(
    username: str,
    filename: str,
    cid: str,
    hotkeys: List[str],
    payload: dict,
    ext: str,
    size: int = 0,
    incr: bool = True,
):
    redis_db.hset(
        "metadata:" + username,
        cid,
        json.dumps(
            {
                "filename": filename,
                "hotkeys": hotkeys,
                "encryption_payload": payload,
                "ext": ext,
                "size": size,
                "uploaded": str(datetime.today()), # datetime.today().ctime(),
            }
        )
    )
    if redis_db.get("filecount:" + username) is None:
        redis_db.set("filecount:" + username, 0)
    if incr:
        redis_db.incr("filecount:" + username, 1)
    redis_db.incr("storage:" + username, size)
    redis_db.incr("service:totalFiles")

# Files should be retrieved by CID, and not by filename (which is not unique)
def get_cid_metadata(cid: str, username: str) -> Optional[dict]:
    md = redis_db.hget("metadata:" + username, cid)
    if md is None:
        return None
    return json.loads(md)

def delete_cid_metadata(cid: str, username: str):
    md = get_cid_metadata(cid, username)
    if md is not None:
        redis_db.hdel("metadata:" + username, cid)
        redis_db.decr("filecount:" + username, 1)
        redis_db.decr("storage:" + username, md.get("size", 0))
        redis_db.decr("service:totalFiles", 1)

def file_cid_exists(username: str, cid: str) -> bool:
    return redis_db.hget("metadata:" + username, cid) is not None

def filename_exists(username: str, filename: str) -> bool:
    """"Check if a file already exists in the user's storage"""
    cids = redis_db.hkeys("metadata:" + username)
    for cid in cids:
        md = get_cid_metadata(cid, username)
        if md.get("filename", "") == filename:
            return True
    return False

def get_cid_by_filename(filename: str, username: str) -> List[str]:
    """Retrieve the cid for a user by filename"""
    cids = redis_db.hkeys("metadata:" + username)
    for cid in cids:
        md = get_cid_metadata(cid, username)
        if md.get("filename", "") == filename:
            return cid

def rename_file(username: str, cid: str, new_filename: str):
    md = get_cid_metadata(cid, username)
    if md is not None:
        md["filename"] = new_filename
        redis_db.hset("metadata:" + username, cid, json.dumps(md))

def get_user_metadata(username: str) -> Optional[str]:
    return redis_db.hgetall("metadata:" + username)

def get_hotkeys_by_cid(cid: str, username: str) -> List[str]:
    md = get_cid_metadata(cid, username)
    return md.get("hotkeys", [])

def get_metagraph(netuid: int = 21, network: str = "finney") -> bt.metagraph:
    metagraph_str = redis_db.get(f"metagraph:{netuid}")
    if metagraph_str:
        metagraph = deserialize_metagraph(metagraph_str.decode())
        last_block = metagraph.block.item()
        current_block = bt.subtensor(network).get_current_block()
        if current_block - last_block < 100:
            return metagraph

    metagraph = bt.subtensor(network).metagraph(netuid)
    metagraph_str = serialize_metagraph(metagraph, dump=True)
    redis_db.set(f"metagraph:{netuid}", metagraph_str)
    return metagraph

def serialize_metagraph(metagraph_obj: bt.metagraph, dump=False) -> Union[str, dict]:
    serialized_data = {}
    for attr in METAGRAPH_ATTRIBUTES:
        tensor = getattr(metagraph_obj, attr, None)
        if tensor is not None:
            serialized_data[attr] = tensor.cpu().numpy().tolist()

    serialized_data["netuid"] = metagraph_obj.netuid
    serialized_data["network"] = metagraph_obj.network
    serialized_data["version"] = metagraph_obj.version.item()
    serialized_data["axons"] = [axon.to_string() for axon in metagraph_obj.axons]
    serialized_data["netuid"] = metagraph_obj.netuid

    return json.dumps(serialized_data) if dump else serialized_data

def deserialize_metagraph(serialized_str) -> bt.metagraph:
    if isinstance(serialized_str, str):
        data = json.loads(serialized_str)
    else:
        data = serialized_str
    metagraph_obj = bt.metagraph(
        netuid=data["netuid"], network=data["network"], lite=False, sync=False
    )
    metagraph_obj.version = torch.nn.Parameter(
        torch.tensor([data["version"]], dtype=torch.int64), requires_grad=False
    )

    for attr in METAGRAPH_ATTRIBUTES:
        if attr in data:
            setattr(
                metagraph_obj,
                attr,
                torch.nn.Parameter(torch.tensor(data[attr]), requires_grad=False),
            )

    metagraph_obj.axons = [
        bt.chain_data.AxonInfo.from_string(axon_data) for axon_data in data["axons"]
    ]

    return metagraph_obj
