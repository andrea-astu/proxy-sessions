# to be able to use modules from other files
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

import websockets
import asyncio
import json
import argparse

from typing import Any

# in order to write sessions and convert them to or from strings
from session_logic.session_types import *
from session_logic.parsers import session_into_message, payload_to_string # to convert session to str

from websockets.legacy.server import WebSocketServerProtocol, serve # for websockets

async def ws_server(websocket:WebSocketServerProtocol):
    '''
    Main function of server where protocols are defined and information is sent back and forth.

    Args:
        websocket: Server's websocket (will receive and send information) provided by websockets.serve function.
    '''
    
    print("Connection succesful...")
    try:
        while True:

            # use functions to create payload strings for payload types
            two_num_recv = payload_to_string("tuple", ["number", "number"])
            num_payload = payload_to_string("number")
            str_payload = payload_to_string("string")

            # define sessions and transform them to strings in order to send them to proxy as a JSON object
            protocol_a_session = Def(
            name="A",
            cont=Choice(
                dir=Dir("send"),
                alternatives={
                    Label("Add"): Single(
                        dir=Dir("recv"),
                        payload=two_num_recv,
                        cont=Single(
                            dir=Dir("send"),
                            payload=num_payload,
                            cont=Ref("A")
                        )
                    ),
                    Label("Neg"): Single(
                        dir=Dir("recv"),
                        payload=num_payload,
                        cont=Single(
                            dir=Dir("send"),
                            payload=num_payload,
                            cont=Ref("A")
                        )
                    ),
                    Label("Greeting"): Single(
                        dir=Dir("recv"),
                        payload=str_payload,
                        cont=Single(
                            dir=Dir("send"),
                            payload=str_payload,
                            cont=Ref("A")
                        )
                    ),
                    Label("Goodbye"): Single(
                        dir=Dir("send"),
                        payload=str_payload,
                        cont=Ref("A")
                    ),
                    Label("Quit"): End()
                }
                )
            )

            protocol_b_session = Def(
            name="B",
            cont=Choice(
                dir=Dir("send"),
                alternatives={
                    Label("Divide"):  Single(
                        dir=Dir("recv"),
                        payload=two_num_recv,
                        cont=Single(
                            dir=Dir("send"),
                            payload=num_payload,
                            cont=Ref("B")
                        )
                    ),
                    Label("List"): Single(
                        dir=Dir("recv"),
                        payload='{ type: "string" }',
                        cont=Single(
                            dir=Dir("send"),
                            payload='{ type: "array", payload: { type: "number" } }',
                            cont=Ref("B")
                        )
                    ),
                    Label("Quit"): End()
                }
            )
            )

            protocol_a_str = session_into_message(protocol_a_session)
            protocol_b_str = session_into_message(protocol_b_session)

            # send protocols to proxy
            print("Sending protocols to proxy...")
            await send(websocket, protocol_a_str)
            await send(websocket, protocol_b_str)
            await send(websocket, "Session: End") # signals we are done sending protocols

            while True:
                # receive protocol info
                protocol = await receive(websocket)
                print(f'Got protocol {protocol}')

                # process previously defined prtocols
                match protocol:
                    case "A":
                        # choose option in protocol
                        action = await receive(websocket)
                        print(f'Doing action: {action}')
                        # action refers to a specific session inside a protocol

                        match action:
                            case "Add":
                                nums = await receive(websocket) # payload
                                c = int(nums[0]) + int(nums[1])
                                await send(websocket, c) # convert payload to json and send to proxy
                                print(f'Sent payload: {c}')
                             
                            case "Neg":
                                a = await receive(websocket) # payload
                                b = -int(a)
                                await send(websocket, b) # convert payload to json and send to proxy
                                print(f'Sent payload: {b}')
                            
                            case "Greeting":
                                name = await receive(websocket) # payload
                                nickname = name[:3] # first three letters of name
                                await send(websocket, nickname) # send changed name
                                print('Sent payload')

                            case "Goodbye":
                                await send(websocket, "May we meet again")
                                print('Sent payload')

                            case "Quit":
                                break

                            case _:
                                raise SessionError("This action does not exist in the curent protocol")

                    
                    case "B":
                         # choose option in protocol
                        action = await receive(websocket)
                        # action refers to a specific session inside a protocol
                        print(f'Doing action: {action}')

                        match action:
                            case "Divide":
                                nums = await receive(websocket) # payload
                                division = int(nums[0]) / int(nums[1])
                                await send(websocket, division) # send result of division
                            
                            case "List":
                                sentence = await receive(websocket) # receive string -> payload
                                new_list = sentence.split() # split a sentence by spaces
                                await send(websocket, new_list)
                                 
                            case "Quit":
                                break

                            case _:
                                raise SessionError("This action does not exist in the curent protocol")


                    case _:
                        print(f'This protocol is not recognized') # could be handled as an exception
                        await send(websocket, "Session: End")
    # handle ok and unexpected connections
    except websockets.ConnectionClosedOK:
        print("Client connection finished...")
    except websockets.ConnectionClosedError:
        print("Error: Client connection lost unexpectedly.")
    except Exception as e:
        print(f"Unexpected server error: {e}")
    finally:
        await websocket.close()


 # -- [Description] -----------------------------------------------------------------------------------------
async def receive(websocket)-> Any: # return type list?
    proxy_msg = json.loads(await websocket.recv())
    print(proxy_msg) # debugging
    if "500" not in proxy_msg[0]: # ok?
        raise SessionError(f"Receiving Error {proxy_msg[0]}")
    elif len(proxy_msg) > 1: # if not only error or success code in proxy
        return proxy_msg[1] # return everything in message that is left
    
async def send(websocket, message:Any): # return smthng?
    print(f"sending {type(message)}") # debugging
    await websocket.send(json.dumps(message))
    proxy_msg = json.loads(await websocket.recv())
    if "500" not in proxy_msg:
        raise SessionError(f"Sending Error {proxy_msg}")
    # print("message sent ok") # debugging

# -- [Description] -----------------------------------------------------------------------------------------
async def main(port:int):
    '''
    Creates a WebSocket server that listens on localhost:7890.
    Whenever a client connects to the server, websockets.serve automatically calls ws_server, 
    passing in a new websocket object (which represents the connection with that client).

    Args:
        port: The port from which server is reachable.
    '''
    print(f"Using port {port}")
    async with serve(ws_server, "localhost", port): # the port can be changed depending on preference
        await asyncio.Future()  # run forever because servers must always be active
 
if __name__ == "__main__":
    # take port as flag
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--port", default = "7890", help="Port number")
    args = parser.parse_args()

    # start code
    print("Server started ...")
    asyncio.run(main(args.port))