import websockets
import asyncio
import json
import argparse

# in order to write sessions and convert them to or from strings
from session_types import *
from proxy import session_into_message # to convert session to str

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

            # define sessions and transform them to strings in order to send them to proxy as a JSON object

            protocol_a_session = Def(
            name="A",
            cont=Choice(
                dir=Dir("send"),
                alternatives={
                    Label("Add"): Single(
                        dir=Dir("recv"),
                        payload='{ type: "number" }',
                        cont=Single(
                            dir=Dir("recv"),
                            payload='{ type: "number" }',
                            cont=Single(
                                dir=Dir("send"),
                                payload='{ type: "number" }',
                                cont=Ref("A")
                            )
                        )
                    ),
                    Label("Neg"): Single(
                        dir=Dir("recv"),
                        payload='{ type: "number" }',
                        cont=Single(
                            dir=Dir("send"),
                            payload='{ type: "number" }',
                            cont=Ref("A")
                        )
                    ),
                    Label("Greeting"): Single(
                        dir=Dir("recv"),
                        payload='{ type: "string" }',
                        cont=Single(
                            dir=Dir("send"),
                            payload='{ type: "string" }',
                            cont=Ref("A")
                        )
                    ),
                    Label("Goodbye"): Single(
                        dir=Dir("send"),
                        payload='{ type: "string" }',
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
                    Label("Divide"): Single(
                        dir=Dir("recv"),
                        payload='{ type: "number" }',
                        cont=Single(
                            dir=Dir("recv"),
                            payload='{ type: "number" }',
                            cont=Single(
                                dir=Dir("send"),
                                payload='{ type: "number" }',
                                cont=Ref("B")
                            )
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
            await websocket.send(json.dumps(protocol_a_str))
            await websocket.send(json.dumps(protocol_b_str))
            await websocket.send(json.dumps("Session: End")) # signals we are done sending protocols

            while True:
                # receive protocol info
                protocol = await websocket.recv()
                print(f'Got protocol {protocol}')

                # process previously defined prtocols
                match protocol:
                    case "A":
                        # choose option in protocol
                        action = await websocket.recv()
                        # action refers to a specific session inside a protocol
                        print(f'Doing action: {action}')

                        match action:
                            case "Add":
                                a = json.loads(await websocket.recv()) # receive number
                                b = json.loads(await websocket.recv()) # receive number
                                c = a + b
                                await websocket.send(json.dumps(c)) # convert payload to json and send to proxy
                                print(f'Sent payload: {c}')
                            
                            case "Neg":
                                a = json.loads(await websocket.recv()) # receive number
                                b = -a
                                await websocket.send(json.dumps(b)) # convert payload to json and send to proxy
                                print(f'Sent payload: {b}')
                            
                            case "Greeting":
                                name = json.loads(await websocket.recv()) # receive name
                                nickname = name[:3] # first three letters of name
                                await websocket.send(json.dumps(nickname)) # send changed name

                            case "Goodbye":
                                await websocket.send(json.dumps("May we meet again"))
                            
                            case "Quit":
                                break

                            case _:
                                raise SessionError("This action does not exist in the curent protocol")

                    
                    case "B":
                        # choose option in protocol
                        action = await websocket.recv()
                        print(f'Doing action {action}')

                        match action:
                            case "Divide":
                                num1 = json.loads(await websocket.recv())
                                num2 = json.loads(await websocket.recv())
                                division = num1 / num2
                                await websocket.send(json.dumps(division)) # send result of division

                            
                            case "List":
                                sentence = json.loads(await websocket.recv()) # receive string
                                new_list = sentence.split() # split a sentence by spaces
                                await websocket.send(json.dumps(new_list))
                                
                            
                            case "Quit":
                                break

                            case _:
                                raise SessionError("This action does not exist in the curent protocol")


                    case _:
                        print(f'This protocol is not recognized') # could be handled as an exception
                        await websocket.send("Session: End")
    # handle ok and unexpected connections
    except websockets.ConnectionClosedOK:
        print("Client connection finished...")
    except websockets.ConnectionClosedError:
        print("Error: Client connection lost unexpectedly.")
    except Exception as e:
        print(f"Unexpected server error: {e}")
    finally:
        await websocket.close()
 
 
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