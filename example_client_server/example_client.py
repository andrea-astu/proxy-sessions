# to be able to use modules from other files
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

# for sending/receiving with proxy + proxy error exceptions
from session_logic.helpers import *

import websockets
import asyncio
import time # to keep console opened for a bit after code is finished

 
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
            print("Client code finished.")
    except websockets.exceptions.ConnectionClosed:
        print(f"Connection lost, most likely due to a timeout")
    except ProxyError as e:
        print(e)
    except Exception as e:
        print("Unexpected error {e}")
    finally:
        print("Closing client in 5 seconds...")
        time.sleep(5)
        exit()  

#-- Start the client code ------------------------------------------------------------------------------------------
asyncio.run(ws_client())