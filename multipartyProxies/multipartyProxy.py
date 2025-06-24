# to be able to use modules from other files
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from typing import Callable, Any, cast

# websockets imports
import websockets
import asyncio
from websockets.legacy.server import WebSocketServerProtocol, serve # for websockets server
from websockets.legacy.client import WebSocketClientProtocol # for websockets client

# to check payload types are ok
from session_logic import schema_validation

# to send schema error message to client
import json

# to define ports as flags (optional arguments)
import argparse

# for session types, dictionary and errors
from session_logic.session_types import *

# for parsing messages back and forth, and functions taht alter messages
from session_logic.parsers import *

# -- define vars -----------------------------------------------------------------------

# remember: actor names are protocols referenced

actorsClients = {} # dict that keeps track of which actors reference which websockets

# -- Interactions with server ---------------------------------------------------------------------

async def define_protocols(server_socket:WebSocketClientProtocol):
    '''
    Description here.
    '''
    try:
        session_as_str = json.loads(await receive(server_socket)) # first protocol; minimum one has to be defined
        protocol_definition= message_into_session(session_as_str) # send type to session conversion so it can be added to name
        assert isinstance(protocol_definition, Def), "Expected a Def session from server" # to ensure only def sessions are given here
        protocol_info.add(protocol_definition) # add server protocol to global dictionary
        await send_code(501, server_socket)

        # define more protocols
        while protocol_definition.kind != "end":
            session_as_str = json.loads(await receive(server_socket))
            protocol_definition = message_into_session(session_as_str)
            match (protocol_definition):
                case End():
                    await send_code(501, server_socket)
                    break
                case Def():
                    protocol_info.add(protocol_definition) # add server protocol to global dictionary
                    await send_code(501, server_socket)
                case _:
                    raise SessionError("Trying to define session that is not a Def")
    except:
        await send_code(201, server_socket)

    print(f"Registered protocols") # to track what proxy is doing at moment -> could be removed

# -- Handle timeouts ->  for now timeouts disabled and will figure it out later --------------------------------------------------------------
async def receive(socket:WebSocketServerProtocol|WebSocketClientProtocol) -> Any:
    '''
    Description
    '''
    try:
        return await socket.recv()
    except Exception as e:
        print(f"Receiving failed: {e}")

    # edit later to include timeouts
    """
        match socket:
            case "client":
                return await asyncio.wait_for(client_socket.recv(), timeout=30) # give it two minutes
            case "server":
                return await asyncio.wait_for(server_socket.recv(), timeout=30) # give it two minutes
            # add case _?
    except asyncio.TimeoutError:
        match socket:
            case "client":
                await send_code(400, server_socket, client_socket)
                raise TimeoutError("Client timeout error")
            case "server":
                await send_code(401, server_socket, client_socket)
                raise TimeoutError("Server timeout error")
            case _:
                raise TimeoutError("Timeout error")
                await send_code(402, server_socket, client_socket) # proxy error because timeout should be either with server or client
                raise websockets.ConnectionClosedError
    """

#-- Define proxy errors + success messages and exceptions ----------------------------------------------------------------------------------

async def send_code(code:int, socket:WebSocketClientProtocol|WebSocketServerProtocol, info:str=""):
    match code:
        case 201:
            await socket.send(json.dumps("201: There was an error defining the protocol. Please check the session syntax."))
        case 501: # server success
            await socket.send(json.dumps("502: Operation succesful."))

# ------------- Proxy-Server Interaction ----------------------------------------------------------------------
async def serverCode(server_address: str):
    # maybe add error handling here
    '''
    Define
    '''
    async with websockets.connect(server_address) as server_ws:
        print("Connected with server. Defining protocols...")
        await define_protocols(server_ws)
    print("Protocols defined.")
    # add catch exceptions

# -- start code ------------------------------------------------------------------------------------------------------------

if __name__ == "__main__":
    # while True:
    protocol_info = GlobalDict({}) # initialize global dictionary for protocols

    # define ports for proxy and server as flags
    parser = argparse.ArgumentParser()
    parser.add_argument("-pr", "--proxyport", default = "7891", help="Proxy port number")
    parser.add_argument("-s", "--serverport", default = "7890", help="Server port number")
    args = parser.parse_args()
    print(f"Welcome to the proxy!\nProxy port: {args.proxyport}\nServer port or address: {args.serverport}")

    # check server val
    if args.serverport.isnumeric():
        server_address = f"ws://127.0.0.1:{args.serverport}"
    else:
        server_address = args.serverport

    # connect with server, get info needed
    print("Connecting with server ...")
    try:
        asyncio.run(serverCode(server_address))
        print(protocol_info) # debugging
    except Exception as e:
        print(f"The proxy encountered an error. Please try again!")