import websockets
import asyncio
 
# The main function that will handle connection and communication
# with the server
async def ws_client():
    print("WebSocket: Client Connected.")
    url = "ws://127.0.0.1:7891"

    # define protocol sessions
    protocol_a_str = """Session: Def, Name: A, Cont: Session: Choice, Dir: recv, Alternatives: [{Label: Add, Session: Single, Dir: send, Payload: int, Cont: Session: Single, Dir: send, Payload: int, Cont: Session: Single, Dir: recv, Payload: int, Cont: Session: Ref, Name: A}, {Label: Neg, Session: Single, Dir: send, Payload: int, Cont: Session: Single, Dir: recv, Payload: int, Cont: Session: Ref, Name: A}, {Label: Quit, Session: End}]"""
            
    protocol_b_str = """Session: Def, Name: B, Cont: Session: Choice, Dir: recv, Alternatives: [{Label: Greeting, Session: Single, Dir: send, Payload: str, Cont: Session: Single, Dir: recv, Payload: str, Cont: Session: Ref, Name: B}, {Label: Goodbye, Session: Single, Dir: recv, Payload: int, Cont: Session: Ref, Name: B}, {Label: Quit, Session: End}]"""


    # Connect to the server
    async with websockets.connect(url) as ws:

        # define protocols
        print("Defining protocols...") # DEBUG
        await ws.send(protocol_a_str)
        await ws.send(protocol_b_str)
        await ws.send("Session: End") # signals we are done sending protocols
        
        # Greeting procedure
        name = input("Hi! What is your name?: ")
        await ws.send("Protocol: B") # choosing protocol
        await ws.send("Greeting") # choosing "operation"
        await ws.send(name) # sending info
        nickname = await ws.recv()
        print(f'Your assigned nickname is: {nickname}')
        await ws.send("Quit") # quit protocol b
        
        # negation
        await ws.send("Protocol: A") # choosing protocol
        await ws.send("Neg") # choosing "operation"
        given_num = input(f'{nickname}, please give a number to negate: ')
        await ws.send(given_num)
        neg_result = await ws.recv()
        print(f'The negated number is: {neg_result}')

        # Adding a number!
        await ws.send("Add") # choosing "operation"
        age_person = input(f'{nickname}, please tell me your age: ')
        age_mom = input(f"{nickname}, please tell me your mom's age: ")
        await ws.send(age_person)
        await ws.send(age_mom)
        combined_ages = await ws.recv()
        print(f'The ages of you and your mom combined are: {combined_ages}')

        await ws.send("Quit") # quit operations protocol

        # Goodbye procedure
        await ws.send("Protocol: B") # choosing protocol
        await ws.send("Goodbye") # choosing "operation"
        farewell = ws.recv()
        print(f'{farewell} {nickname}')
        await ws.send("Quit") # quit protocol b

        # Stay alive forever, listen to incoming msgs
        while True:
            await ws.recv()
 
# Start the connection
asyncio.run(ws_client())