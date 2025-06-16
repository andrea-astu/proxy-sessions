# to be able to use modules from other files
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from typing import Callable, Any, cast

# websockets imports
import websockets
import asyncio
from websockets.legacy.server import WebSocketServerProtocol, serve # for websockets server
from websockets.legacy.client import WebSocketClientProtocol # for websockets client

# to check payload types are ok
from session_logic import schema_validation

# to send schema error message to client
import json

# to define ports as flags (optional arguments)
import argparse

# for session types, dictionary and errors
from session_logic.session_types import *

# for parsing messages back and forth, and functions taht alter messages
from session_logic.parsers import *

        
# ---- Client and server communications, session handlers -----------------------------------------------

async def handle_session(ses_server: Session, ses_client: Session, server_socket: WebSocketClientProtocol, client_socket: WebSocketServerProtocol, 
                         server_parser: Callable[..., Any], client_parser: Callable[..., Any], command:list[str, Any]|str=[]) -> tuple[Session, Session]:
    '''
    Performs actions depending on the given sessions and compares the server and client sessions are actually mirrored.
    Def sessions are not handled here because those define protocols and are instead handled in the define_protocols function.

        Args:
            ses_server (Session): actual session the server is carrying out
            ses_client (Session): actual session the client is carrying out
            server_socket (WebsocketClientProtocol): socket to communicate between proxy and server (proxy is "client" in this case)
            client_socket (WebsocketServerProtocol): socket to communicate between proxy and client (proxy is "server" in this case)
            server_parser (Callable[..., Any]): function that changes the server message before sending it to the client
            client_parser (Callable[..., Any]): function that changes the client message before sending it to the server
            command (str): Optional argument that refrences the action to be carried out; used for choice sessions

        Returns:
            Two sessions; one for the server and one for the client. However, in case there is an exception, it returns it.
    '''
    # initialize sessions
    actual_sessions = (ses_server, ses_client)
    ses_server_actual = actual_sessions[0]
    ses_client_actual = actual_sessions[1]
    payload = None # initialize but will change when tehrer is one
    # carry out sessions in a loop (useful for cont)
    while (not isinstance(ses_server_actual, End)) and (not isinstance(ses_client_actual, End)):
        # print(payload) # debug
        match (ses_server_actual, ses_client_actual):
            case (Single(), Single()):
                # type single (transports payload from server to client or vice versa)
                # returns End sessions if schema validation fails -> could be handled differently
                match (ses_server_actual.dir.dir, ses_client_actual.dir.dir):
                    # client sends payload to server -> payload already checked in choice
                    case ("recv", "send"):
                        try:
                            print(schema_validation.checkPayload(payload, ses_client_actual.payload, ses_server_actual.payload)) # check client paylaod
                            await send_code(5000, server_socket, client_socket) # let client know payload + action worked ok!
                            await server_socket.send(json.dumps(["500: Operation succesful.", json.loads(payload)])) # send payload to server (case ok payload)
                            payload = None # reset payload to none
                            print("Message sent from client to server") # to track what proxy is doing at moment -> could be removed
                        except Exception as e:
                            await send_code(1010, server_socket, client_socket, e)
                            return End(), End()
                    # server sends payload to client
                    case ("send", "recv"):
                        # check the payload type being transported matches the payload types defined in the sessions
                        try:
                            print("awaiting server payload") # debugging
                            payload = await server_socket.recv() # server has to send payload!
                            print(schema_validation.checkPayload(payload, ses_server_actual.payload, ses_client_actual.payload))
                            await client_socket.send(json.dumps(["500: Operation succesful.", payload])) # transport payload if type is ok
                            payload = None # rest payload
                            print("Message sent from server to client") # to track what proxy is doing at moment -> could be removed
                            await send_code(5001, server_socket, client_socket)
                        except Exception as e:
                            print(f"prob sending payload: {json.loads(payload)}") # debugging
                            await send_code(1011, server_socket, client_socket, e)
                            return End(), End()
                    case _:
                        # print(ses_server_actual.dir, ses_client_actual.dir) # comment out for debugging
                        await send_code(302, server_socket, client_socket) # dir error
                        return End(), End()
                actual_sessions = (ses_server_actual.cont, ses_client_actual.cont) # after a single session start next session
            # type choice (choose a session inside a protocol)
            case(Choice(), Choice()):
                # means you are given action by client and action comes with payload, therefore separate
                # print(f'Looking up action: {command}...') # comment out to debug
                try:
                    # in case the command has payload with it
                    if not isinstance(command, str): # if it has payload it's of type list with action and payload; if not, it'd just string
                        payload = command[1]
                        print(f"payload type in choice: {type(payload)}") # debugging
                        action = command[0]
                    else:
                        action = command
                    print(f'Carrying out {action} action...') # to track what proxy is doing at moment -> could be removed
                    actual_sessions = (ses_server_actual.lookup(Label(action)), ses_client_actual.lookup(Label(action))) # next sessions will be singles
                    await server_socket.send(json.dumps(["500: Operation succesful.", action])) # let server know about command only if it IS a valid one
                    if not payload: # if no payload, means server is sending and therefore client waits for ok of action
                        await send_code(500, server_socket, client_socket)
                except Exception as e:
                    await send_code(303, server_socket, client_socket)
                    return End(), End()
                payload = json.dumps(payload) # pack payload into json again for payload checks and transportation
            # type ref (always returns a session of type choice)
            case(Ref(), Ref()):
                # Attempt to resolve references
                try:
                    found_server = protocol_info.lookup(ses_server_actual.name)
                    found_client = protocol_info.lookup(ses_client_actual.name)
                    return found_server, found_client
                except Exception as e:
                    await send_code(305, server_socket, client_socket)
                    return End(), End()
            case _:
                await send_code(301, server_socket, client_socket)
                return End(), End()
        # update sessions to use in while loop
        ses_server_actual = actual_sessions[0]
        ses_client_actual = actual_sessions[1]
    return End(), End() # only returned when both sessions are end sessions
    

async def define_protocols(server_socket:WebSocketClientProtocol, client_socket:WebSocketServerProtocol):
    '''
    Receives strings from server that define protocols as Def sessions and adds them to the global
    dictionary until an End Session is received.

        Args:
            server_socket (WebsocketClientProtocol): socket of the server
            client_socket (WebsocketServerProtocol): socket of the client
    '''
    session_as_str = json.loads(await server_socket.recv()) # first protocol; minimum one has to be defined
    # define server session
    try: # too long or ok? specially bc. it can fail bc. of dif. things
        protocol_definition_server = message_into_session(session_as_str, "server") # send type to session conversion so it can be added to name
        assert isinstance(protocol_definition_server, Def), "Expected a Def session from server" # to ensure only def sessions are given here
        protocol_info.add(protocol_definition_server) # add server protocol to global dictionary
        # define client session
        protocol_definition_client = message_into_session(session_as_str, "client") # send type to session conversion so it can be added to name
        assert isinstance(protocol_definition_client, Def), "Expected a Def session from server" # to ensure session was properly mirrored as Def
        protocol_info.add(protocol_definition_client) # add client protocol to global dictionary
        await send_code(5001, server_socket, client_socket)

        # define more protocols
        while protocol_definition_server.kind != "end":
            session_as_str = json.loads(await server_socket.recv())
            protocol_definition_server = message_into_session(session_as_str, "server")
            match (protocol_definition_server):
                case End():
                    await send_code(5001, server_socket, client_socket)
                    break
                case Def():
                    protocol_info.add(protocol_definition_server) # add server protocol to global dictionary
                    protocol_definition_client = message_into_session(session_as_str, "client") # make client session
                    assert isinstance(protocol_definition_client, Def), "Expected a Def session from server" # to ensure session was properly mirrored as Def
                    protocol_info.add(protocol_definition_client) # add client protocol to global dictionary
                    await send_code(5001, server_socket, client_socket)
                case _:
                    raise SessionError("Trying to define session that is not a Def")
    except:
        await send_code(201, server_socket, client_socket)

    print(f"Registered protocols") # to track what proxy is doing at moment -> could be removed

async def proxy_websockets(server:WebSocketClientProtocol, websocket_client:WebSocketServerProtocol, server_parser: Callable[..., Any], client_parser: Callable[..., Any]):
    '''
    Manages the connection between the client and the server via sessions.

        Args:
            server (str): uri of the server to establish a connection with it
            websocket_client (WebsocketServerProtocol): client websocket to exchange information between it and the proxy
            server_parser (Callable[..., Any]): function that changes the server message before sending it to the client
            client_parser (Callable[..., Any]): function that changes the client message before sending it to the server
    '''
    # async with websockets.connect(server) as server_ws
    try:
        # define protocols
        await define_protocols(server, websocket_client) # errors already handled inside function
    
        while True:
            protocol_name = json.loads(await websocket_client.recv()) # client chooses protocol 
            protocol_name = protocol_name[10:] # protocol message structure: "Protocol: ___" 
            print(f'Executing protocol {protocol_name}...') # to track what proxy is doing at moment -> could be removed
            # get both client and server sessions by referencing protocol
            actual_ses_server, actual_ses_client = await handle_session(Ref(f"{protocol_name}_server"), Ref(f"{protocol_name}_client"),
                                                                        server, websocket_client, server_parser, client_parser) # ref session
            await send_code(5000, server, websocket_client) # tell client protocol reference went ok
            # recursively carry out sessions until we get two "End" sessions back
            while actual_ses_server.kind != "end" and actual_ses_client.kind != "end":
                await server.send(json.dumps(["500: Operation succesful.", protocol_name])) # always have to tell server which protocol is being used
                command = json.loads(await websocket_client.recv()) # action name; ok code sent in handle_session after checking payload part of command
                try:
                    assert isinstance(command[0], str), "Command should be string" # to ensure command is string
                except:
                    await send_code(304, server, websocket_client)
                    actual_ses_server, actual_ses_client = End(), End() # so handler returns end sessions and conenction is ended
                # carry out action    
                actual_ses_server, actual_ses_client = await handle_session(actual_ses_server, actual_ses_client, server, #  carries out exchange dictated in that protocol's action 
                                                                            websocket_client, server_parser, client_parser, command)
    # handle ok and unexpected connections
    except (websockets.ConnectionClosedOK, websockets.ConnectionClosedError):
        print("Client connection terminated. Closing connections ...")
    except (SchemaValidationError) as e:
        print(f"{e}. Restarting ...")
    except Exception as e:
        await send_code(400, server, websocket_client)
        print(f"Unexpected error in proxy: {e}")
    finally:
        await server.close()
        await websocket_client.close()


# ------------- Initialize Proxy  ----------------------------------------------------------------------
async def start_proxy(proxy_address: int, server_address: str):
    # maybe add error handling here
    '''
    Initializes the proxy's websocket connection and connects it to server, then starts main proxy function
    to handle client-server communication

        Args:
            proxy_address (int): port where a connection with the proxy can be established
            server_address (str): server address
    '''
    stop_event = asyncio.Event()  # Create event to track when to stop
    
    async def handler(websocket:WebSocketServerProtocol):
        async with websockets.connect(server_address) as server_ws:
            try:
                server_ws = cast(WebSocketClientProtocol, server_ws) # to correct type errors in websockets
                await proxy_websockets(server_ws, websocket, server_parser_func, client_parser_func)
            except Exception as e:
                print(f"Error in handler: {e}")
            finally:
                print("Handler finished ...")
                stop_event.set()  # Trigger stop when all clients are gone

    try:
        server = await serve(handler, "localhost", proxy_address)
        print("Proxy started, waiting for client...")
        await stop_event.wait()  # Exit when stop_event is set
        print("Closing connection with server...")
        server.close()
        await server.wait_closed()  # Ensure server fully shuts down
    except Exception:
        print(f"The proxy encountered an error. Please try again!")

#-- Define proxy errors + success message ----------------------------------------------------------------------------------

async def send_code(code:int, server_socket:WebSocketClientProtocol, client_socket:WebSocketServerProtocol, info:str=""):
     # repeated strings
    payload_error = "101: The sent payload does not match the one defined in the session"
    # only to send to client to let know server had problem or vice versa
    server_prob_error = "1011: There was an error with the server."
    client_prob_error = "1010: There was an error with the client."
    print(f"Success/Failure code: {code}") # debug
    match code:
        # 4th num: 1 is for when server caused, 0 is when client did
        case 1010:
            await client_socket.send(json.dumps(payload_error + f" ({info}).")) # add details of schema error?
            await server_socket.send(json.dumps(client_prob_error))
            await client_socket.close() # close conenction -> try it out
        case 1011:
            await client_socket.send(json.dumps(server_prob_error))
            await server_socket.send(json.dumps(payload_error + f" ({e})")) # add details of schema error?
            # for server error, close connection with both
            await client_socket.close()
            await server_socket.close()
        case 201:
            await server_socket.send(json.dumps("201: There was an error defining the protocol. Please check the session syntax."))
            await client_socket.send(json.dumps(server_prob_error))
            # for server error, close connection with both
            await client_socket.close()
            await server_socket.close()
        case 301:
            # not sure if client prob. or server prob...
            await client_socket.send(json.dumps("301: This __ does not match the defined session."))
            await client_socket.close()
        case 302:
            await server_socket.send(json.dumps("302: Invalid direction or it does not match the defined one."))
            await client_socket.send(json.dumps(server_prob_error))
            # not sure if client prob. or server prob. ....
            await client_socket.close()
            await server_socket.close()
        case 303:
            await client_socket.send(json.dumps("303: This action is not defined in the protocol."))
            await server_socket.send(json.dumps(client_prob_error))
            await client_socket.close()
        case 304:
            await client_socket.send(json.dumps("304: The action must be given as a string."))
            await server_socket.send(json.dumps(client_prob_error))
            await client_socket.close()
        case 305:
            await client_socket.send(json.dumps("305: This protocol cannot be found."))
            await server_socket.send(json.dumps(client_prob_error))
            await client_socket.close()
        case 400:
            await client_socket.send(json.dumps("400: Unexpected error in proxy."))
            await server_socket.send(json.dumps("400: Unexpected error in proxy."))
            # for proxy error, disconnect with both
            await client_socket.close()
            await server_socket.close()
        case 500: # signal success for both
            await client_socket.send(json.dumps("500: Operation succesful."))
            await server_socket.send(json.dumps("500: Operation succesful."))
        case 5000: # client success
            await client_socket.send(json.dumps("500: Operation succesful."))
        case 5001: # server success
            await server_socket.send(json.dumps("500: Operation succesful."))

# -- start code ------------------------------------------------------------------------------------------------------------

if __name__ == "__main__":
    # establish connections
    connection_given = False
    
    while True:
        protocol_info = GlobalDict({}) # initialize global dictionary for protocols

        # define ports for proxy and server as flags
        parser = argparse.ArgumentParser()
        parser.add_argument("-pr", "--proxyport", default = "7891", help="Proxy port number")
        parser.add_argument("-s", "--serverport", default = "7890", help="Server port number")
        args = parser.parse_args()
        print(f"Welcome to the proxy!\nProxy port: {args.proxyport}\nServer port or address: {args.serverport}")

        # check server val
        if args.serverport.isnumeric():
            server_address = f"ws://127.0.0.1:{args.serverport}"
        else:
            server_address = args.serverport
        
        print("Connecting...")

        try:
            # run proxy
            asyncio.run(start_proxy(args.proxyport, server_address))
        except Exception as e:
            print(f"The proxy encountered an error. Please try again!")