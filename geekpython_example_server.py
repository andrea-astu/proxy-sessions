import websockets
import asyncio
import proxy_with_middle as proxy # check defs. don't clash
import json
 
# Creating WebSocket server
async def ws_server(websocket):
    print("WebSocket: Server Started.")
 
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
                        print(f'Sent paylaod: {c}')
                        protocol == "A"
                    
                    if action == "Neg":
                        a = json.loads(await websocket.recv()) # receive number
                        b = -a
                        await websocket.send(json.dumps(b)) # convert payload to json and send to proxy
                        print(f'Sent payload: {b}')
                        protocol == "A"

                    # if action == "Quit":
                        # print(f'currently in A quit')
                
                elif protocol == "B":
                    # choose option in protocol
                    action = await websocket.recv()
                    print(f'Doing action {action}')

                    if action == "Greeting":
                        name = json.loads(await websocket.recv()) # receive name
                        nickname = name[:2] # first three letters of name
                        await websocket.send(json.dumps(nickname)) # send changed name
                        protocol == "B"
                    

                    if action == "Goodbye":
                        await websocket.send(json.dumps("May we meet again"))
                        protocol == "B"

                    # if action == "Quit":
                        # print(f'in quit B') # DEBUG

                else:
                    # code as raising an exception instead
                    print(f'This protocol is not recognized')
                    await websocket.send("Session: End")
 
    except websockets.ConnectionClosedError:
        print("Internal Server Error.")
 
 
async def main():
    async with websockets.serve(ws_server, "localhost", 7890):
        await asyncio.Future()  # run forever*
 
if __name__ == "__main__":
    # start code
    asyncio.run(main())