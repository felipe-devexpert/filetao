import time
import bittensor as bt
from typing import Union, List

class timed_dendrite(bt.dendrite):

    async def call(
        self,
        target_axon: Union[bt.AxonInfo, bt.axon],
        synapse: bt.Synapse = bt.Synapse(),
        timeout: float = 12.0,
        deserialize: bool = True,
    ) -> bt.Synapse:
        """
        Asynchronously sends a request to a specified Axon and processes the response.

        This function establishes a connection with a specified Axon, sends the encapsulated
        data through the Synapse object, waits for a response, processes it, and then
        returns the updated Synapse object.

        Args:
            target_axon (Union['bt.AxonInfo', 'bt.axon']): The target Axon to send the request to.
            synapse (bt.Synapse, optional): The Synapse object encapsulating the data. Defaults to a new :func:`bt.Synapse` instance.
            timeout (float, optional): Maximum duration to wait for a response from the Axon in seconds. Defaults to ``12.0``.
            deserialize (bool, optional): Determines if the received response should be deserialized. Defaults to ``True``.

        Returns:
            bt.Synapse: The Synapse object, updated with the response data from the Axon.
        """

        # Record start time
        target_axon = (
            target_axon.info()
            if isinstance(target_axon, bt.axon)
            else target_axon
        )

        # Build request endpoint from the synapse class
        request_name = synapse.__class__.__name__
        url = self._get_endpoint_url(target_axon, request_name=request_name)

        # Preprocess synapse for making a request
        synapse = self.preprocess_synapse_for_request(target_axon, synapse, timeout)

        try:
            # Log outgoing request
            self._log_outgoing_request(synapse)

            # Make the HTTP POST request
            start_time = time.time()
            async with (await self.session).post(
                url,
                headers=synapse.to_headers(),
                json=synapse.dict(),
                timeout=timeout,
            ) as response:
                # Extract the JSON response from the server
                json_response = await response.json()

                # Set process time and log the response
                process_time = time.time() - start_time # type: ignore

                # Process the server response and fill synapse
                self.process_server_response(response, json_response, synapse)
                synapse.dendrite.process_time = process_time

        except Exception as e:
            self._handle_request_errors(synapse, request_name, e)

        finally:
            self._log_incoming_response(synapse)

            # Log synapse event history
            self.synapse_history.append(
                bt.Synapse.from_headers(synapse.to_headers())
            )

            # Return the updated synapse object after deserializing if requested
            if deserialize:
                return synapse.deserialize()
            else:
                return synapse
