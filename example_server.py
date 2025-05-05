import websockets
import asyncio
import json
import argparse

# in order to 
from session_types import *


async def ws_server(websocket):
    '''
    Main function of server where protocols are defined and information is sent back and forth.

    Args:
        websocket: Server's websocket (will receive and send information) provided by websockets.serve function.
    '''
    print("Connection succesful...")
    try:
        while True:

            # define protocols
            protocol_a_str = (
                'Session: Def, Name: A, Cont: Session: Choice, Dir: send, Alternatives: '
                '[(Label: Add, Session: Single, Dir: recv, Payload: { type: "number" }, Cont: '
                'Session: Single, Dir: recv, Payload: { type: "number" }, Cont: '
                'Session: Single, Dir: send, Payload: { type: "number" }, Cont: '
                'Session: Ref, Name: A), '
                '(Label: Neg, Session: Single, Dir: recv, Payload: { type: "number" }, Cont: '
                'Session: Single, Dir: send, Payload: { type: "number" }, Cont: '
                'Session: Ref, Name: A), '
                '(Label: Greeting, Session: Single, Dir: recv, Payload: { type: "string" }, Cont: '
                'Session: Single, Dir: send, Payload: { type: "string" }, Cont: '
                'Session: Ref, Name: A), '
                '(Label: Goodbye, Session: Single, Dir: send, Payload: { type: "string" }, Cont: '
                'Session: Ref, Name: A), '
                '(Label: Quit, Session: End)]'
            )

            # protocol_a = 

            protocol_b_str = (
                'Session: Def, Name: B, Cont: Session: Choice, Dir: send, Alternatives: ['
                '(Label: Divide, Session: Single, Dir: recv, Payload: { type: "number" }, Cont: '
                'Session: Single, Dir: recv, Payload: { type: "number" }, Cont: '
                'Session: Single, Dir: send, Payload: { type: "number" }, Cont: '
                'Session: Ref, Name: B), '
                '(Label: List, Session: Single, Dir: recv, Payload: { type: "string" }, Cont: '
                'Session: Single, Dir: send, Payload: { type: "array", payload: { type: "number" } }, Cont: '
                'Session: Ref, Name: B), '
                '(Label: Quit, Session: End)]'
            )

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
 
 
async def main(port):
    '''
    Creates a WebSocket server that listens on localhost:7890.
    Whenever a client connects to the server, websockets.serve automatically calls ws_server, 
    passing in a new websocket object (which represents the connection with that client).

    Args:
        port: The port from which server is reachable.
    '''
    print(f"Using port {port}")
    async with websockets.serve(ws_server, "localhost", port): # the port can be changed depending on preference
        await asyncio.Future()  # run forever because servers must always be active
 
if __name__ == "__main__":
    # take port as flag
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--port", default = "7890", help="Port number")
    args = parser.parse_args()

    # start code
    print("Server started ...")
    asyncio.run(main(args.port))