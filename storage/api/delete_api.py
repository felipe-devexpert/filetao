# The MIT License (MIT)
# Copyright © 2021 Yuma Rao
# Copyright © 2023 Opentensor Foundation
# Copyright © 2024 Philantrope

# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
# documentation files (the “Software”), to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all copies or substantial portions of
# the Software.

# THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO
# THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.

import os
import json
import torch
import base64
import random
import asyncio
import bittensor as bt
from abc import ABC, abstractmethod
from typing import Any, List, Union, Dict
from storage.protocol import DeleteUser
from storage.validator.cid import generate_cid_string
from storage.validator.encryption import encrypt_data
from storage.api.utils import get_query_api_axons
from storage.cli.default_values import defaults
from storage.shared.utils import list_all_hashes


class DeleteUserAPI(bt.SubnetsAPI):
    def __init__(self, wallet: "bt.wallet"):
        super().__init__(wallet)
        self.netuid = 21

    def prepare_synapse(self, cid: str) -> DeleteUser:
        synapse = DeleteUser(data_hash=cid)
        return synapse

    def process_responses(self, responses: List[Union["bt.Synapse", Any]]) -> Union[str, List[str]]:
        success = False
        failure_modes = {"code": [], "message": []}
        for response in responses:
            if response.dendrite.status_code != 200:
                failure_modes["code"].append(response.dendrite.status_code)
                failure_modes["message"].append(response.dendrite.status_message)
                continue

            success = True

        return success


async def delete(
    cid: str,
    wallet: "bt.wallet",
    subtensor: "bt.subtensor" = None,
    chain_endpoint: str = "finney",
    netuid: int = 21,
    timeout: int = 10,
    uids: List[int] = None,
    hotkeys: List[str] = None,
    metadata_path: str = None,
    name: str = None,
    max_retries: int = 3,
    backoff_factor: float = 2.0,
) -> bytes:
    """
    Delete data from the FileTAO network.

    Args:
        cid (str): The hash of the data to retrieve.
        wallet (bt.wallet): The wallet to use for the retrieval.
        subtensor (bt.subtensor, optional): The subtensor network to use. Defaults to None.
        chain_endpoint (str, optional): The chain endpoint to use. Defaults to "finney".
        netuid (int, optional): The netuid to use. Defaults to 21.
        timeout (int, optional): The timeout for the retrieval. Defaults to 60.
        uids (List[int], optional): The uids to use for the retrieval. Defaults to None.
        hotkeys (List[str], optional): The hotkeys to use for the retrieval. Defaults to None.
        metadata_path (str, optional): The path to the hash metadata. Defaults to None.
        name (str, optional): The name of the file to find metadata for. Defaults to None.
    """
    retry_count = 0
    delay = 2

    delete_handler = DeleteUserAPI(wallet)

    subtensor = subtensor or bt.subtensor(chain_endpoint)
    metagraph = subtensor.metagraph(netuid=netuid)

    metadata_path = os.path.expanduser(metadata_path or defaults.hash_basepath)
    hash_filepath = os.path.join(metadata_path, wallet.name + ".json")

    if hotkeys is None:
        hashes_dict = list_all_hashes(hash_filepath)
        reverse_hashes_dict = {v: k for k, v in hashes_dict.items() if "hotkeys" not in k}
        if cid in reverse_hashes_dict:
            filename = reverse_hashes_dict[cid]
            hotkeys = hashes_dict[filename + "_hotkeys"]

    if uids is None and hotkeys is not None:
        uids = [metagraph.hotkeys.index(hotkey) for hotkey in hotkeys]

    axons = await get_query_api_axons(wallet=wallet, metagraph=metagraph, uids=uids)

    while retry_count < max_retries:
        try:

            data = await delete_handler(
                axons=axons,
                cid=cid,
                timeout=timeout,
            )

            if data != b"":
                return data

        except Exception as e:
            print(f"Attempt {retry_count + 1} failed: {str(e)}")

        await asyncio.sleep(delay)

        delay *= backoff_factor
        retry_count += 1

    return data
