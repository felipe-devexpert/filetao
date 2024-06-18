import asyncio
import bittensor as bt
from abc import ABC, abstractmethod
from typing import Any, List, Union, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed


class Subnet21API(ABC):
    def __init__(self, wallet: "bt.wallet"):
        self.wallet = wallet
        self.dendrite = bt.dendrite(wallet=wallet)

    async def __call__(self, *args, **kwargs):
        return await self.query_api(*args, **kwargs)

    @abstractmethod
    def prepare_synapse(self, *args, **kwargs) -> Any:
        """
        Prepare the synapse-specific payload.
        """
        ...

    @abstractmethod
    def process_responses(self, responses: List[Union["bt.Synapse", Any]]) -> Any:
        """
        Process the responses from the network.
        """
        ...

    async def query_api(
        self,
        axons: Union[bt.axon, List[bt.axon]],
        deserialize: Optional[bool] = False,
        timeout: Optional[int] = 600,
        n: Optional[float] = 0.1,
        uid: Optional[int] = None,
        **kwargs: Optional[Any],
    ) -> Any:
        """
        Queries the API nodes of a subnet using the given synapse and bespoke query function.

        Args:
            axons (Union[bt.axon, List[bt.axon]]): The list of axon(s) to query.
            deserialize (bool, optional): Whether to deserialize the responses. Defaults to False.
            timeout (int, optional): The timeout in seconds for the query. Defaults to 12.
            n (float, optional): The fraction of top nodes to consider based on stake. Defaults to 0.1.
            uid (int, optional): The specific UID of the API node to query. Defaults to None.
            **kwargs: Keyword arguments for the prepare_synapse_fn.

        Returns:
            Any: The result of the process_responses_fn.
        """
        synapse = self.prepare_synapse(**kwargs)
        bt.logging.debug(f"Querying validator axons with synapse {synapse.name}...")

        # Ensure axons is a list for consistency in processing
        axons = [axons] if not isinstance(axons, list) else axons

        async def query_axon(axon):
            return await self.dendrite(
                axons=axon,
                synapse=synapse,
                deserialize=deserialize,
                timeout=timeout,
            )

        tasks = [asyncio.create_task(query_axon(axon)) for axon in axons]

        def is_successful(response):
            return response.axon.status_code == 200

        try:
            while tasks:
                done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)

                for task in done:
                    if task.done():
                        try:
                            response = await task
                            if is_successful(response):
                                for p in pending:
                                    p.cancel()
                                await asyncio.gather(*pending, return_exceptions=True)
                                return self.process_responses([response])
                        except Exception as e:
                            bt.logging.error(f"Task failed: {e}")

                tasks = list(pending)

            return None, []

        finally:
            for task in tasks:
                if not task.done():
                    task.cancel()

            await asyncio.gather(*tasks, return_exceptions=True)
