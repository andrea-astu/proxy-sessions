import websockets
import asyncio
import json


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
            # payloads can only be sent to proxy through string
            protocol_a_str = 'Session: Def, Name: A, Cont: Session: Choice, Dir: send, Alternatives: [(Label: Add, Session: Single, Dir: recv, Payload: { type: "number" }, Cont: Session: Single, Dir: recv, Payload: { type: "number" }, Cont: Session: Single, Dir: send, Payload: { type: "number" }, Cont: Session: Ref, Name: A), (Label: Neg, Session: Single, Dir: recv, Payload: { type: "number" }, Cont: Session: Single, Dir: send, Payload: { type: "number" }, Cont: Session: Ref, Name: A), (Label: Quit, Session: End)]'
            protocol_b_str = 'Session: Def, Name: B, Cont: Session: Choice, Dir: send, Alternatives: [(Label: Greeting, Session: Single, Dir: recv, Payload: { type: "string" }, Cont: Session: Single, Dir: send, Payload: { type: "string" }, Cont: Session: Ref, Name: B), (Label: Goodbye, Session: Single, Dir: send, Payload: { type: "string" }, Cont: Session: Ref, Name: B), (Label: Quit, Session: End)]'

            # send protocols to proxy
            print("Sending protocols to proxy...")
            await websocket.send(protocol_a_str)
            await websocket.send(protocol_b_str)
            await websocket.send("Session: End") # signals we are done sending protocols

            while True:
                # receive protocol info
                protocol = await websocket.recv()
                print(f'Got protocol {protocol}')

                # process previously defined prtocols
                if protocol == "A":
                    # choose option in protocol
                    action = await websocket.recv()
                    # action refers to a specific session inside a protocol
                    print(f'Doing action: {action}')

                    if action == "Add":
                        a = json.loads(await websocket.recv()) # receive number
                        b = json.loads(await websocket.recv()) # receive number
                        c = a + b
                        await websocket.send(json.dumps(c)) # convert payload to json and send to proxy
                        print(f'Sent payload: {c}')
                        protocol == "A"
                    
                    if action == "Neg":
                        a = json.loads(await websocket.recv()) # receive number
                        b = -a
                        await websocket.send(json.dumps(b)) # convert payload to json and send to proxy
                        print(f'Sent payload: {b}')
                        protocol == "A"

                
                elif protocol == "B":
                    # choose option in protocol
                    action = await websocket.recv()
                    print(f'Doing action {action}')

                    if action == "Greeting":
                        name = json.loads(await websocket.recv()) # receive name
                        nickname = name[:3] # first three letters of name
                        await websocket.send(json.dumps(nickname)) # send changed name
                        protocol == "B"
                    

                    if action == "Goodbye":
                        await websocket.send(json.dumps("May we meet again"))
                        protocol == "B"


                else:
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
 
 
async def main():
    '''
    Creates a WebSocket server that listens on localhost:7890.
    Whenever a client connects to the server, websockets.serve automatically calls ws_server, 
    passing in a new websocket object (which represents the connection with that client).
    '''
    async with websockets.serve(ws_server, "localhost", 7890): # the port can be changed depending on preference
        await asyncio.Future()  # run forever because servers must always be active
 
if __name__ == "__main__":
    # start code
    print("Server started ...")
    asyncio.run(main())