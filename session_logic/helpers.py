import json # to send and receive payloads
from typing import Any
from websockets.legacy.server import WebSocketServerProtocol, serve # for websockets server websocket
from websockets import ClientProtocol # for websockets client

# -- Send and receive functions -------------------------------------------------------------------
async def receive(websocket:ClientProtocol|WebSocketServerProtocol)-> Any:
    """
    Receives and deserializes the proxy message that is in the form of a JSON object, checks if the messages
    carries a succes code(500) and returns a payload if there is one.

    Args:
        websocket (ClientProtocol | WebSocketServerProtocol):
            The client or server socket.

    Returns:
        Any: The payload forwarded from the proxy, if there is one.

    Raises:
        ProxyError: If the proxy message reports an error.
    """
    payload = None
    proxy_msg = json.loads(await websocket.recv())
    if type(proxy_msg) == list: # separate payload from ok/failure message
        message = proxy_msg[0]
        payload = proxy_msg[1]
    else:
        message = proxy_msg
    if "502" not in message: # handle errors
        raise ProxyError("Proxy error " + proxy_msg)
    if payload: # if not only error or success code in proxy
        return payload # return everything in message that is left
    
async def send(websocket:ClientProtocol|WebSocketServerProtocol, message:Any):
        """
        Packs the payload to be sent into a JSON object and receives succes or failure message
        back from the proxy.

        Args:
            websocket(ClientProtocol|WebSocketServerProtocol): client or server socket
            message(Any): The message to send given as a python object.
        
        Raises:
            ProxyError: If the proxy message includes an error code.
        """
        await websocket.send(json.dumps(message))
        proxy_msg = json.loads(await websocket.recv())
        if "502" not in proxy_msg:
            raise ProxyError("Proxy error " + proxy_msg)
        
# -- Define exceptions -------------------------------------------------------------------------------------------------
class ProxyError(Exception):
    """Exception raised for when proxy sends a message reporting an error."""
    def __init__(self, message:str="Proxy error"):
        self.message = message
        super().__init__(self.message) 