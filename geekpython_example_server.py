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

            # if there's TWO types of ref, how to indicate which one I'm referring to?
            # Also momentarily defined End as cont
            # Also momentarily defined "send" as dir but not sure if that's ok :/

            # dict for alternatives in A
            # does it work to define Labels this way???
            # Ref A indicates should be ready to carry out more Sessions in protocol
            # HOW to define TYPE of payload???? Like here it should be "receive number"!! Maybe JSON Schema??
            add_session = proxy.Single(dir="recv", payload=proxy.Payload("number"),
                                   cont=(proxy.Single(dir="recv", payload=proxy.Payload("number"),
                                   cont=(proxy.Single(dir="send", payload=proxy.Payload("number"),
                                   cont=(proxy.Ref("A")))))))
            neg_session = proxy.Single(dir="recv", payload=proxy.Payload("number"),
                                   cont=(proxy.Single(dir="send", payload=proxy.Payload("number"),
                                   cont=(proxy.Ref("A")))))
            a_alt = {proxy.Label("Add"): add_session,
                     proxy.Label("Neg"): neg_session,
                     proxy.Label("Quit"): proxy.End}

            # define A
            protocol_a = proxy.Def(name="A", cont=proxy.Choice(dir="send", alternatives=a_alt))

            # other protocol to try switching in between. Protocol to give/return name
            greeting_session = proxy.Single(dir="recv", payload=proxy.Payload("string"),
                                   cont=(proxy.Single(dir="send", payload=proxy.Payload("string"),
                                   cont=(proxy.Ref("B")))))
            goodbye_session = proxy.Single(dir="send", payload=proxy.Payload("string"),
                                   cont=(proxy.Ref("B")))
            b_alt = {proxy.Label("Greeting"): greeting_session,
                     proxy.Label("Goodbye"): goodbye_session,
                     proxy.Label("Quit"): proxy.End}

            # define B
            protocol_b = proxy.Def(name="B", cont=proxy.Choice(dir="send", alternatives=b_alt))

            # as a string!!!
            # ?: payload "" or not?
            protocol_a_str = """Session: Def, Name: A, Cont: Session: Choice, Dir: send, Alternatives: [{Label: Add, Session: Single, Dir: recv, Payload: number, Cont: Session: Single, Dir: recv, Payload: number, Cont: Session: Single, Dir: send, Payload: number, Cont: Session: Ref, Name: A}, {Label: Neg, Session: Single, Dir: recv, Payload: number, Cont: Session: Single, Dir: send, Payload: number, Cont: Session: Ref, Name: A}, {Label: Quit, Session: End}]"""
            
            protocol_b_str = """Session: Def, Name: B, Cont: Session: Choice, Dir: send, Alternatives: [{Label: Greeting, Session: Single, Dir: recv, Payload: string, Cont: Session: Single, Dir: send, Payload: string, Cont: Session: Ref, Name: B}, {Label: Goodbye, Session: Single, Dir: send, Payload: number, Cont: Session: Ref, Name: B}, {Label: Quit, Session: End}]"""




            # send protocols to proxy (as sessions or as String??)
            # await websocket.send("Sending protocols")
            print("BACK AT PROTOCOL DEF IN SERVER") # DEBUG
            await websocket.send(protocol_a_str)
            await websocket.send(protocol_b_str)
            await websocket.send("Session: End") # signals we are done sending protocols??
            # await websocket.send("Finished sending protocols")

            while True: # listen always to proxy?? Maybe break connection eventually
                # accept request for protocol/session from proxy
                protocol = await websocket.recv()
                print(f'got protocol {protocol}') # DEBUG
                # check what to do in case of protocol:
                if protocol == "A": # or do I get it as a Ref??
                    # choose option in protocol
                    action = await websocket.recv() # will be a Label I think! Or str????
                    print(f'in protocol A got action: {action}') # DEBUG

                    if action == "Add":
                        a = json.loads(await websocket.recv()) # receive number
                        b = json.loads(await websocket.recv()) # receive number
                        print(f'in add got this from client: {a}, {b}') # DEBUG
                        c = a + b # perform calculation
                        await websocket.send(json.dumps(c)) # say it's payload or not??
                        print(f'sent answer {c}') # DEBUG
                        protocol == "A"
                    
                    if action == "Neg":
                        a = json.loads(await websocket.recv()) # receive number
                        print(f'in neg got this from client: {a}') # DEBUG
                        b = -a # perform calculation
                        await websocket.send(json.dumps(b))
                        print(f'sent answer {b}') # DEBUG
                        protocol == "A"

                    if action == "Quit":
                        print(f'currently in A quit') # DEBUG
                        # normally would quit protocol but for now pass
                        # await websocket.send("Session: End")
                        # break # will this work? get me out of protocol A if?
                
                elif protocol == "B": # or do I get it as a Ref??
                    # choose option in protocol
                    action = await websocket.recv() # will be a Label I think! Or str????
                    print(f'in b got action {action}') # DEBUG

                    if action == "Greeting":
                        name = json.loads(await websocket.recv()) # receive name
                        nickname = name[:2] # first three letters of name
                        await websocket.send(json.dumps(nickname))
                        protocol == "B"
                    

                    if action == "Goodbye":
                        await websocket.send(json.dumps("May we meet again"))
                        protocol == "B"

                    if action == "Quit":
                        print(f'in quit B') # DEBUG
                        # await websocket.send("Session: End") -> don't need to send end!!
                        # break # ?

                else:
                    print(f'for some reason protocol neither A nor B') # DEBUG
                    await websocket.send("Session: End") # send End session or just message something went wrong??



            """""
            # Receiving values from client
            await websocket.send(f'Session: Single, Dir: recv, Payload: "", Cont: End') # but what abount Cont here?... Or Choice??
            name = await websocket.recv() # but will receive session
            print("received name!")
            await websocket.send(f'Session: Single, Dir: recv, Payload: "", Cont: End')
            age = await websocket.recv() # same: session
 
            # Prompt message when any of the field is missing
            if name == "" or age == "":
                print("Error Receiving Value from Client.")
                break
 
            # Printing details received by client
            print("Details Received from Client:")
            print(f"Name: {name}")
            print(f"Age: {age}")
 
            # Sending a response back to the client
            # Choice HERE?
            if int(age) < 18:
                await websocket.send(f'Session: Single, Dir:send, Payload: "Sorry! {name}, You cannot join the club.", Cont: End')
            else:
                await websocket.send(f'Session: Single, Dir:send, Payload: "Welcome aboard, {name}.", Cont: End')
            """
 
    except websockets.ConnectionClosedError:
        print("Internal Server Error.")
 
 
async def main():
    async with websockets.serve(ws_server, "localhost", 7890):
        await asyncio.Future()  # run forever
 
if __name__ == "__main__":
    asyncio.run(main())