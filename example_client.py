import websockets
import asyncio
import json # to send and receive payloads
import time # to keep console opened for a bit after code is finished

def confirm_server_payload(message):
    '''
    Checks if there was an error with the schema validation according to the proxy and terminates the client if there is.

    Args:
        message: the payload from the message. If something went wrong, then it'll be a string that says "Error: schema validation failed"
    
    Returns:
        The message payload if there were no schema errors.
    '''
    if message == "Error: schema validation failed":
        print("There has been an error with the server payload. Closing client...")
        time.sleep(5)
        exit()
    else: return message


 
async def ws_client():
    '''
    Handles connection and sends and receives payloads according to interation with user.
    '''
    try:
        print("Connecting client...")
        url = "ws://127.0.0.1:7891" # 7891 is proxy port

        # Connect to the proxy/server
        async with websockets.connect(url) as ws:
            # protocol defined by server

            # Greeting procedure
            name = input("Hi! What is your name?: ")
            await ws.send("Protocol: A") # choosing protocol
            await ws.send("Greeting") # choosing "action" (session in a protocol)
            await ws.send(json.dumps(name)) # sending info
            nickname = confirm_server_payload(json.loads(await ws.recv()))
            print(f'Your assigned nickname is: {nickname}')
            
            # negation
            await ws.send("Neg") # choosing "action"
            given_num = input(f'{nickname}, please give a number to negate: ')
            await ws.send(json.dumps(int(given_num)))
            neg_result = confirm_server_payload(json.loads(await ws.recv()))
            print(f'The negated number is: {neg_result}')

            # Adding a number!
            await ws.send("Add") # choosing "action"
            age_person = input(f'{nickname}, please tell me your age: ')
            age_other = input(f"{nickname}, please tell me someone else's age: ")
            await ws.send(json.dumps(int(age_person)))
            await ws.send(json.dumps(int(age_other)))
            combined_ages = confirm_server_payload(json.loads(await ws.recv()))
            print(f'The ages of you and the other person combined are: {str(combined_ages)}')


            # Goodbye procedure
            await ws.send("Goodbye") # choosing "action"
            farewell = confirm_server_payload(json.loads(await ws.recv()))
            print(f'{farewell} {nickname}!')

            # close code
            await ws.send("Quit") # quit protocol
            print("Client code finished. Closing terminal in 5 seconds ...")
            time.sleep(5)
    except:
        print("Connection with proxy interrupted, most likely due to wrong payload sent from client.")
        print("Closing client in 5 seconds...")
        time.sleep(5)
        exit()
 
# Start the client code
asyncio.run(ws_client())