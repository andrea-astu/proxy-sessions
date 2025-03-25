import websockets
import asyncio
import json # to send and receive payloads
import time # to keep console opened for a bit after code is finished
 
async def ws_client():
    '''
    Handles connection and sends and receives payloads according to intrecation with user.
    '''
    print("Connecting client...")
    url = "ws://127.0.0.1:7891" # 7891 is proxy port

    # protocols (server should have same protcols but mirrored)
    protocol_a_str = 'Session: Def, Name: A, Cont: Session: Choice, Dir: recv, Alternatives: [(Label: Add, Session: Single, Dir: send, Payload: { type: "number" }, Cont: Session: Single, Dir: send, Payload: { type: "number" }, Cont: Session: Single, Dir: recv, Payload: { type: "number" }, Cont: Session: Ref, Name: A), (Label: Neg, Session: Single, Dir: send, Payload: { type: "number" }, Cont: Session: Single, Dir: recv, Payload: { type: "number" }, Cont: Session: Ref, Name: A), (Label: Quit, Session: End)]'
    protocol_b_str = 'Session: Def, Name: B, Cont: Session: Choice, Dir: recv, Alternatives: [(Label: Greeting, Session: Single, Dir: send, Payload: { type: "string" }, Cont: Session: Single, Dir: recv, Payload: { type: "string" }, Cont: Session: Ref, Name: B), (Label: Goodbye, Session: Single, Dir: recv, Payload: { type: "string" }, Cont: Session: Ref, Name: B), (Label: Quit, Session: End)]'

    # Connect to the proxy/server
    async with websockets.connect(url) as ws:

        # define protocols
        print("Defining protocols...")
        await ws.send(protocol_a_str)
        await ws.send(protocol_b_str)
        await ws.send("Session: End") # signals we are done sending protocols
        
        # Greeting procedure
        name = input("Hi! What is your name?: ")
        await ws.send("Protocol: B") # choosing protocol
        await ws.send("Greeting") # choosing "operation" or "action" (session in a protocol)
        await ws.send(json.dumps(name)) # sending info
        nickname = json.loads(await ws.recv())
        print(f'Your assigned nickname is: {nickname}')
        await ws.send("Quit") # quit protocol b
        
        # negation
        await ws.send("Protocol: A") # choosing protocol
        await ws.send("Neg") # choosing "action"
        given_num = input(f'{nickname}, please give a number to negate: ')
        await ws.send(json.dumps(int(given_num)))
        neg_result = json.loads(await ws.recv())
        print(f'The negated number is: {neg_result}')

        # Adding a number!
        await ws.send("Add") # choosing "action"
        age_person = input(f'{nickname}, please tell me your age: ')
        age_other = input(f"{nickname}, please tell me someone else's age: ")
        await ws.send(json.dumps(int(age_person)))
        await ws.send(json.dumps(int(age_other)))
        combined_ages = json.loads(await ws.recv())
        print(f'The ages of you and the other person combined are: {str(combined_ages)}')

        await ws.send("Quit") # quit operations protocol*

        # Goodbye procedure
        await ws.send("Protocol: B") # choosing protocol
        await ws.send("Goodbye") # choosing "action"
        farewell = json.loads(await ws.recv())
        print(f'{farewell} {nickname}!')
        await ws.send("Quit") # quit protocol b

        # close code
        print("Client code finished. Closing terminal in 5 seconds ...")
        time.sleep(5)
 
# Start the client code
asyncio.run(ws_client())