from redis import Redis, ConnectionPool
from typing import List, Tuple, Dict, Optional, Any

import json

from storage.shared.utils import get_redis_password

MB_DIV = 1024 ** 2

connection_pool = None

def get_redis(config=None):
    global connection_pool
    if not connection_pool:
        if config:
            host = config.database.host
            db_index = config.database.index
            port = config.database.port
        else:
            db_index = 1
            port = 6379
            host = "localhost"
        print("db_index:", db_index)
        print("host:", host)
        print("port:", port)
        connection_pool = ConnectionPool(
            host=host,
            port=port,
            db=db_index,
            password=get_redis_password(),
            decode_responses=False,
            # socket_connect_timeout=5,
            # max_connections=100,
            health_check_interval=30,
        )
    return Redis(
        connection_pool=connection_pool
    )

def get_miner_statistics(config = None):
    database = get_redis(config)
    stats = {}
    for key in database.scan_iter(b"stats:*", count=10_000):
        # Await the hgetall call and then process its result
        key_stats = database.hgetall(key)
        # Process the key_stats as required
        processed_stats = {
            k.decode("utf-8"): v.decode("utf-8") for k, v in key_stats.items()
        }
        stats[key.decode("utf-8").split(":")[-1]] = processed_stats

    return stats

def get_metadata_for_hotkey_and_hash(
    ss58_address: str, data_hash: str, verbose: bool = False
) -> Optional[Dict[str, Any]]:
    """
    Retrieves specific metadata from a hash in Redis for the given field_key.

    Parameters:
        ss58_address (str): The hotkey assoicated.
        data_hash (str): The data hash associated.

    Returns:
        The deserialized metadata as a dictionary, or None if not found.
    """
    database = get_redis()
    # Get the JSON string from Redis
    metadata_json = database.hget(f"hotkey:{ss58_address}", data_hash)
    if verbose:
        print(
            f"hotkey {ss58_address[:16]} | data_hash {data_hash[:16]} | metadata_json {metadata_json}"
        )
    if metadata_json:
        # Deserialize the JSON string to a Python dictionary
        metadata = json.loads(metadata_json)
        return metadata
    else:
        print(f"No metadata found for {data_hash} in hash {ss58_address}.")
        return None

def total_hotkey_storage(
    hotkey: str, verbose: bool = False
) -> int:
    """
    Calculates the total storage used by a hotkey in the database.

    Parameters:
        hotkey (str): The key representing the hotkey.

    Returns:
        The total storage used by the hotkey in bytes.
    """
    database = get_redis()
    total_storage = 0
    keys = database.hkeys(f"hotkey:{hotkey}")
    for data_hash in keys:
        if data_hash.startswith(b"ttl:"):
            continue
        # Get the metadata for the current data hash
        metadata = get_metadata_for_hotkey_and_hash(
            hotkey, data_hash, verbose
        )
        if metadata:
            # Add the size of the data to the total storage
            total_storage += metadata["size"]
    return total_storage

def cache_hotkeys_capacity(
    hotkeys: List[str], verbose: bool = False, config = None
) -> Dict[str, Tuple[int, Optional[int]]]:
    """
    Caches the capacity information for a list of hotkeys.

    Parameters:
        hotkeys (list): List of hotkey strings to check.
        verbose (bool): A flag indicating if verbose logging is enabled.

    Returns:
        dict: A dictionary with hotkeys as keys and a tuple of (total_storage, limit) as values.
    """
    database = get_redis(config)
    hotkeys_capacity = {}

    for hotkey in hotkeys:
        # Get the total storage used by the hotkey
        total_storage = total_hotkey_storage(hotkey, verbose)
        # Get the byte limit for the hotkey
        byte_limit = database.hget(f"stats:{hotkey}", "storage_limit")

        if byte_limit is None:
            print(f"Could not find storage limit for {hotkey}.")
            limit = None
        else:
            try:
                limit = int(byte_limit)
            except Exception as e:
                print(f"Could not parse storage limit for {hotkey} | {e}.")
                limit = None

        hotkeys_capacity[hotkey] = (total_storage, limit)

    return hotkeys_capacity

def get_hashes_for_hotkey(
    ss58_address: str
) -> List[str]:
    """
    Retrieves all data hashes and their metadata for a given hotkey.

    Parameters:
        ss58_address (str): The key representing the hotkey.

    Returns:
        A dictionary where keys are data hashes and values are the associated metadata.
    """
    database = get_redis()
    # Fetch all fields (data hashes) and values (metadata) for the hotkey
    all_data_hashes = database.hgetall(f"hotkey:{ss58_address}")

    # Deserialize the metadata for each data hash
    return [
        data_hash.decode("utf-8") for data_hash, metadata in all_data_hashes.items()
    ]

def tier_statistics(
    by_tier: bool = False,
    stats: Dict[str, Dict[str, int]] = None,
    registered_hotkeys: List[str] = None
) -> Dict[str, Dict[str, int]]:
    tier_counts = {
        "Super Saiyan": 0,
        "Ruby": 0,
        "Emerald": 0,
        "Diamond": 0,
        "Platinum": 0,
        "Gold": 0,
        "Silver": 0,
        "Bronze": 0,
    } 
    tier_capacity = {
        "Super Saiyan": 0,
        "Ruby": 0,
        "Emerald": 0,
        "Diamond": 0,
        "Platinum": 0,
        "Gold": 0,
        "Silver": 0,
        "Bronze": 0,
    }
    tier_usage = {
        "Super Saiyan": 0,
        "Ruby": 0,
        "Emerald": 0,
        "Diamond": 0,
        "Platinum": 0,
        "Gold": 0,
        "Silver": 0,
        "Bronze": 0,
    }

    if stats is None:
        stats = get_miner_statistics()

    for k,v in stats.items():
        tier = v.get('tier', None)
        if tier:
            hotkey = k.split(":")[-1]
            if hotkey not in registered_hotkeys: continue # Skip unregistered hotkey
            tier_counts[tier] += 1
            tier_capacity[tier] += int(v.get('storage_limit', 0))
            tier_usage[tier] += total_hotkey_storage(hotkey, False)

    tier_percent_usage = {
        k: 100 * (v / tier_capacity[k]) if tier_capacity[k] > 0 else 0
        for k,v in tier_usage.items()
    }

    type_dict = {
        "counts": tier_counts,
        "capacity": {
            k: v / MB_DIV
            for k,v in tier_capacity.items()
        },
        "usage": {
            k: v / MB_DIV
            for k,v in tier_usage.items()
        },
        "percent_usage": tier_percent_usage
    }

    if by_tier:
        inverted_dict = {}

        for category, tier_dict in type_dict.items():
            for tier, value in tier_dict.items():
                if tier not in inverted_dict:
                    inverted_dict[tier] = {}
                inverted_dict[tier][category] = value

        return inverted_dict

    return type_dict

def compute_by_tier_stats(stats: Dict[str, Dict[str, int]] = None):
    if stats is None:
        stats = get_miner_statistics()

    tier_stats = {}
    for _, d in stats.items():
        tier = d['tier']

        if tier not in tier_stats:
            tier_stats[tier] = {
                'store_attempts': 0,
                'store_successes': 0,
                'challenge_attempts': 0,
                'challenge_successes': 0,
                'retrieve_attempts': 0,
                'retrieve_successes': 0,
                'total_current_attempts': 0,
                'total_current_successes': 0,
                'total_global_successes': 0,
            }

        tier_stats[tier]['store_attempts'] += int(d.get('store_attempts', 0))
        tier_stats[tier]['store_successes'] += int(d.get('store_successes', 0))
        tier_stats[tier]['challenge_attempts'] += int(d.get('challenge_attempts', 0))
        tier_stats[tier]['challenge_successes'] += int(d.get('challenge_successes', 0))
        tier_stats[tier]['retrieve_attempts'] += int(d.get('retrieve_attempts', 0))
        tier_stats[tier]['retrieve_successes'] += int(d.get('retrieve_successes', 0))

        tier_stats[tier]['total_current_attempts'] = sum([
            tier_stats[tier]['store_attempts'], 
            tier_stats[tier]['challenge_attempts'], 
            tier_stats[tier]['retrieve_attempts']
        ])
        tier_stats[tier]['total_current_successes'] = sum([
            tier_stats[tier]['store_successes'], 
            tier_stats[tier]['challenge_successes'], 
            tier_stats[tier]['retrieve_successes']
        ])
        tier_stats[tier]['total_global_successes'] += int(d.get('total_successes', 0))

        total_attempts = tier_stats[tier]['total_current_attempts']
        total_successes = tier_stats[tier]['total_current_successes']
        success_rate = (total_successes / total_attempts * 100) if total_attempts else 0
        tier_stats[tier]['success_rate'] = success_rate

    return tier_stats

def get_network_capacity(stats: Dict[str, Dict[str, int]], registered_hotkeys: List[str]) -> int:
    """
    Get the total storage capacity of the network in bytes.
    """
    cap = 0
    for k,v in get_miner_statistics().items():
        cap += int(v.get('storage_limit', 0))

    return cap

def get_redis_db_size() -> int:
    """
    Calculates the total approximate size of all keys in a Redis database.
    Returns:
        int: Total size of all keys in bytes
    """
    database = get_redis()
    total_size = 0
    for key in database.scan_iter("*", count=10_000):
        size = database.execute_command("MEMORY USAGE", key)
        if size:
            total_size += size
    return total_size

def total_successful_requests() -> int:
    return sum(
        [
            int(v.get('total_successes', 0))
            for k,v in get_miner_statistics().items()
        ]
    )

def active_hotkeys() -> List[str]:
    """
    Returns a list of all active hotkeys in the database.
    """
    database = get_redis()
    return [
        x.decode().split(":")[-1] for x in database.scan_iter("hotkey:*", count=10_000)
    ]