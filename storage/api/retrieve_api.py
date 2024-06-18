# The MIT License (MIT)
# Copyright © 2021 Yuma Rao
# Copyright © 2023 Opentensor Foundation
# Copyright © 2024 Philanthrope

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
import torch
import base64
import asyncio
import bittensor as bt
from typing import Any, List, Union
from storage.protocol import RetrieveUser
from storage.validator.encryption import decrypt_data_with_private_key
from storage.api.utils import get_query_api_axons
from storage.shared.utils import list_all_hashes
from storage.cli.default_values import defaults


class RetrieveUserAPI(bt.SubnetsAPI):
    def __init__(self, wallet: "bt.wallet"):
        super().__init__(wallet)
        self.netuid = 21

    def prepare_synapse(self, cid: str) -> RetrieveUser:
        synapse = RetrieveUser(data_hash=cid)
        return synapse

    def process_responses(self, responses: List[Union["bt.Synapse", Any]]) -> bytes:
        success = False
        decrypted_data = b""
        for response in responses:
            bt.logging.trace(f"response: {response.dendrite.dict()}")
            if response.dendrite.status_code != 200 or response.encrypted_data is None:
                continue

            # Decrypt the response
            bt.logging.trace(f"encrypted_data: {response.encrypted_data[:100]}")
            encrypted_data = base64.b64decode(response.encrypted_data)
            bt.logging.debug(f"encryption_payload: {response.encryption_payload}")
            if (
                response.encryption_payload is None
                or response.encryption_payload == ""
                or response.encryption_payload == "{}"
            ):
                bt.logging.warning("No encryption payload found. Unencrypted data.")
                decrypted_data = encrypted_data
            else:
                decrypted_data = decrypt_data_with_private_key(
                    encrypted_data,
                    response.encryption_payload,
                    bytes(self.wallet.coldkey.private_key.hex(), "utf-8"),
                )
            bt.logging.trace(f"decrypted_data: {decrypted_data[:100]}")
            success = True
            break

        if success:
            bt.logging.info(f"Returning retrieved data: {decrypted_data[:100]}")
        else:
            bt.logging.error("Failed to retrieve data.")

        return decrypted_data


async def retrieve(
    cid: str,
    wallet: "bt.wallet",
    subtensor: "bt.subtensor" = None,
    chain_endpoint: str = "finney",
    netuid: int = 21,
    timeout: int = 100,
    uids: List[int] = None,
    hotkeys: List[str] = None,
    metadata_path: str = None,
    name: str = None,
    max_retries: int = 3,
    backoff_factor: float = 2.0,
) -> bytes:
    """
    Retrieve data from the FileTAO network.

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

    retrieve_handler = RetrieveUserAPI(wallet)

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

            data = await retrieve_handler(
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
