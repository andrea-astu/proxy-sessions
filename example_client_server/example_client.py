import websockets
import asyncio
import json # to send and receive payloads
import time # to keep console opened for a bit after code is finished

from typing import Any
 
async def ws_client():
    '''
    Handles connection and sends and receives payloads according to interaCtion with user.
    '''
    try:
        print("Connecting client...")
        url = "ws://127.0.0.1:7891" # 7891 is proxy port

        # Connect to the proxy/server
        async with websockets.connect(url) as ws:
            # protocol defined by server

            # Greeting procedure
            name = input("Hi! What is your name?: ")
            await send(ws, "Protocol: A") # choosing protocol
            await send(ws, ["Greeting", name]) # choosing "action" (session in a protocol) and sending payload
            nickname = await receive(ws)
            print(f'Your assigned nickname is: {nickname}')
            
            # negation
            given_num = input(f'{nickname}, please give a number to negate: ')
            await send(ws, ["Neg", int(given_num)]) # choosing "action" and sendinf payload
            neg_result = await receive(ws)
            print(f'The negated number is: {neg_result}')

            # Adding a number!
            age_person = input(f'{nickname}, please tell me your age: ')
            age_other = input(f"{nickname}, please tell me someone else's age: ")
            await send(ws, ["Add", [int(age_person), int(age_other)]]) # choosing "action" and sending payload along with it
            combined_ages = await receive(ws)
            print(f'The ages of you and the other person combined are: {str(combined_ages)}')


            # Goodbye procedure
            await send(ws, "Goodbye") # choosing "action"
            farewell = await receive(ws)
            print(f'{farewell} {nickname}!')

            # close code
            await send(ws, "Quit") # quit protocol
            # await receive(ws) # still get error or success code bc. "Quit" is still an action in the protocol
            print("Client code finished. Closing terminal in 5 seconds ...")
            time.sleep(5)
    except:
        print("Connection with proxy interrupted.")
        print("Closing client in 5 seconds...")
        time.sleep(5)
        exit()

# [ADD DESCRIPTION]
async def receive(websocket)-> Any: # return type list?
    proxy_msg = json.loads(await websocket.recv())
    if "500" not in proxy_msg[0]: # ok?
        print(f"Error {proxy_msg[0]}")
        print("The client will close itself in 5 seconds...")
        time.sleep(5)
        exit()
    elif len(proxy_msg) > 1: # if not only error or success code in proxy
        return proxy_msg[1] # return everything in message that is left
    
async def send(websocket, message:Any):
    await websocket.send(json.dumps(message))
    proxy_msg = json.loads(await websocket.recv())
    if "500" not in proxy_msg:
        print(f"Error {proxy_msg}")
        print("The client will close itself in 5 seconds...")
        time.sleep(5)
        exit()

# Start the client code
asyncio.run(ws_client())