from typing import Callable

import re # to parse Connection addresses

# websockets imports
import websockets
import asyncio

# to check payload types are ok
import schema_validation

# to send schema error message to client
import json

# to define ports as flags (optional arguments)
import argparse

#
from session_types import * # for session types, dictionary and schema error

        
# ---- Client and server communications, session handlers -----------------------------------------------

async def handle_session(ses_server: Session, ses_client: Session, server_socket, client_socket, 
                         server_parser: Callable, client_parser: Callable, command:str="") -> tuple[Session, Session] | Exception:
    '''
    Performs actions depending on the given sessions and compares the server and client sessions are actually mirrored.
    Def sessions are not handled here because those define protocols and are instead handled in the define_protocols function.

        Args:
            ses_server (Session): actual session the server is carrying out
            ses_client (Session): actual session the client is carrying out
            server_socket: socket to communicate between proxy and server
            client_socket: socket to communicate between proxy and client
            server_parser (Callable): function that changes the server message before sending it to the client
            client_parser (Callable): function that changes the client message before sending it to the server
            command (str): Optional argument that refrences the action to be carried out; used for choice sessions

        Returns:
            Two sessions; one for the server and one for the client. However, in case there is an exception, it returns it.
    '''
    # initialize sessions
    actual_sessions = (ses_server, ses_client)
    ses_server_actual = actual_sessions[0]
    ses_client_actual = actual_sessions[1]
    # carry out sessions in a loop (useful for cont)
    while ses_server_actual.kind != "end" and ses_client_actual.kind != "end":
        # type single (transports payload from server to client or vice versa)
        # returns End sessions if schema validation fails -> could be handled differently
        match (ses_server_actual.kind, ses_client_actual.kind):
            case ("single", "single"):
                match (ses_server_actual.dir, ses_client_actual.dir):
                    # client sends payload to server
                    case ("recv", "send"):
                        payload_to_transport = client_parser(await client_socket.recv())
                        # check the payload type being transported matches the payload types defined in the sessions
                        try:
                            print(schema_validation.checkPayload(payload_to_transport, ses_client_actual.payload, ses_server_actual.payload))
                            await server_socket.send(payload_to_transport)
                            print("Message sent from client to server") # to track what proxy is doing at moment -> could be removed
                        except Exception as e:
                            raise SchemaValidationError(f"Schema validation from client payload failed: {e}")
                    # server sends payload to client
                    case ("send", "recv"):
                        payload_to_transport = server_parser(await server_socket.recv())
                        # check the payload type being transported matches the payload types defined in the sessions
                        try:
                            print(schema_validation.checkPayload(payload_to_transport, ses_server_actual.payload, ses_client_actual.payload))
                            await client_socket.send(payload_to_transport) # transport payload if type is ok
                            print("Message sent from server to client") # to track what proxy is doing at moment -> could be removed
                        except Exception as e:
                            # if server schema validation fails
                            await client_socket.send(json.dumps("Error: schema validation failed")) # send error message to cleint
                            raise SchemaValidationError(f"Schema validation from client payload failed: {e}")
                    case _:
                        print ("Error: The direction given to the Single session is not recognized or server and client do not have opposing directions.") # not handled as exception but could be
                        return End(), End()
                actual_sessions = (ses_server_actual.cont, ses_client_actual.cont) # after a single session start next session
            # type choice (choose a session inside a protocol)
            case("choice", "choice"):
                # print(f'Looking up action: {command}...') # comment out to debug
                actual_sessions = (ses_server_actual.lookup(Label(command)), ses_client_actual.lookup(Label(command)))
            # type ref (always returns a session of type choice)
            case("ref", "ref"):
                # print(f'Referencing server session {ses_server_actual.name} and client session {ses_client_actual.name}...') # comment out to debug
                found_server = protocol_info.lookup(ses_server_actual.name)
                found_client = protocol_info.lookup(ses_client_actual.name)
                return found_server, found_client
            case _:
                print ("Error: Unknown session type or sessions don't match") # not handled as exception but could be
                return End(), End()
        # update sessions to use in while loop
        ses_server_actual = actual_sessions[0]
        ses_client_actual = actual_sessions[1]
    return End(), End() # only returned when both sessions are end sessions
    

async def define_protocols(ws_socket):
    '''
    Receives strings from client or server that define protocols as Def sessions and adds them to the global
    dictionary until an End Session is received.

        Args:
            ws_socket: client or server socket to receive and send information
            type_socket (str): can either be "server" or "client" depending on which party is sending the protocols
    '''
    session_as_str = json.loads(await ws_socket.recv()) # first protocol; minimum one has to be defined
    # define server session
    protocol_definition_server = message_into_session(session_as_str, "server") # send type to session conversion so it can be added to name
    protocol_info.add(protocol_definition_server) # add server protocol to global dictionary
    # define client session
    protocol_definition_client = message_into_session(session_as_str, "client") # send type to session conversion so it can be added to name
    protocol_info.add(protocol_definition_client) # add client protocol to global dictionary

    # define more protocols
    while protocol_definition_server.kind != "end":
        session_as_str = json.loads(await ws_socket.recv())
        protocol_definition_server = message_into_session(session_as_str, "server")
        if protocol_definition_server.kind != "end":
            protocol_info.add(protocol_definition_server) # add server protocol to global dictionary
            protocol_definition_client = message_into_session(session_as_str, "client") # make client session
            protocol_info.add(protocol_definition_client) # add client protocol to global dictionary
    
    print(f"Registered protocols") # to track what proxy is doing at moment -> could be removed

async def proxy_websockets(server:str, websocket_client, server_parser: Callable, client_parser: Callable):
    '''
    Manages the connection between the client and the server via sessions.

        Args:
            server (str): uri of the server to establish a connection with it
            websocket_client: client websocket to exchange information between it and the proxy
            server_parser (Callable): function that changes the server message before sending it to the client
            client_parser (Callable): function that changes the client message before sending it to the server
    '''
    async with websockets.connect(server) as server_ws:
        try:
            # define protocols
            await define_protocols(server_ws)
        
            while True:
                protocol_name = await websocket_client.recv() # client chooses protocol 
                protocol_name = protocol_name[10:] # protocol message structure: "Protocol: ___" 
                print(f'Executing protocol {protocol_name}...') # to track what proxy is doing at moment -> could be removed
                # get both client and server sessions by referencing protocol
                actual_ses_server, actual_ses_client = await handle_session(Ref(f"{protocol_name}_server"), Ref(f"{protocol_name}_client"),
                                                                            server_ws, websocket_client, server_parser, client_parser) # choice session
                # recursively carry out sessions until we get two "End" sessions back
                while actual_ses_server.kind != "end" and actual_ses_client.kind != "end":
                    await server_ws.send(protocol_name) # always have to tell server which protocol is being used
                    command = await websocket_client.recv() # action name
                    print(f'Carrying out {command} action...') # to track what proxy is doing at moment -> could be removed
                    await server_ws.send(command)
                    actual_ses_server, actual_ses_client = await handle_session(actual_ses_server, actual_ses_client, server_ws, #  carries out exchange dictated in that protocol's action 
                                                                                websocket_client, server_parser, client_parser, command)
        # handle ok and unexpected connections
        except (websockets.ConnectionClosedOK, websockets.ConnectionClosedError):
            print("Client connection terminated. Closing connections ...")
        except (SchemaValidationError) as e:
            print(f"{e}. Restarting ...")
        except Exception as e:
            print(f"Unexpected error in proxy: {e}")
        finally:
            await server_ws.close()
            await websocket_client.close()

#------------ Messages and Session Parsers -------------------------------------------------------------------

def message_into_session(ses_info:str, type_socket:str=None) -> Session:
    '''
    Parses a string and transforms into into a session object.

        Args:
            ses_info (str): session as a string
            type_socket (str): optional string for Def sessions to add server or client marker to protocol name and change dir
                               (has to be either "client" or "server")
        
        Returns:
            The parsed session
    '''
    if ses_info.startswith("Session: "):
        ses_info = ses_info[9:] # split string to figure out which kind of session
        # print(f"Parsing session {ses_info}...") # comment out for debugging

        # single session
        if ses_info.startswith("Single"):
            pattern = r"Single, Dir: (.*?), Payload: (.*?), Cont: (.*)"
            match = re.match(pattern, ses_info)
            if match:
                dir_given, pay_given, cont_ses = match.groups()
                match (dir_given, type_socket):
                    case ("send", "server"):
                        dir_given = "send"
                    case ("send", "client"):
                        dir_given = "recv"
                    case ("recv", "server"):
                        dir_given = "recv"
                    case ("recv", "client"):
                        dir_given = "send"
                    case _:
                        print("Error: invalid direction given") # not handled as exception but could be
                #return single session and parse the cont str to make it a session too
                session_changed = Single(dir=dir_given, payload=pay_given, cont=message_into_session(cont_ses, type_socket))
            else:
                print("Error: wrong syntax")

        # def session; uses type_socket parameter
        if ses_info.startswith("Def"):
            pattern = r"Def, Name: (.*?), Cont: (.*)"
            match = re.match(pattern, ses_info)
            if match:
                name_given, cont_ses = match.groups()
                # print(f"Parsing protocol {name_given}") # comment put to debug
                # recursively parse choice sessions defined in protocol with "cont"
                session_changed = Def(name=f"{name_given}_{type_socket}", cont=message_into_session(cont_ses, type_socket))
            else:
                print("Error: wrong syntax") # not handled as exception but could be

        # ref session
        if ses_info.startswith("Ref"):
            if ses_info.startswith("Ref, Name: "):
                name_given = ses_info[11:] # references protocol name
                session_changed = Ref(name=f"{name_given}_{type_socket}")
            else:
                print("Error: wrong syntax") # not handled as exception but could be

        # choice session
        # Idea: session would look like: Session: Choice, Dir: send, Alternatives: [{Label: Add, Session: Single, }]
        if ses_info.startswith("Choice"):
            pattern = r"Choice, Dir: (.*?), Alternatives: \[(.*)\]" # alternatives like that so it's dict
            match = re.match(pattern, ses_info)
            if match:
                dir_given, alternatives_given = match.groups()
                # parse alternatives
                alternatives_parsed = {} # to keep track of all sessions in alternatives dictionay
                alt_matches = re.findall(r"\(Label: (.*?), Session: (.*?)\)", alternatives_given) # find all things with this structure in alternatives
                for label, alt_session in alt_matches:
                    # Parse each alternative's session recursively
                    alternatives_parsed[Label(label.strip())] = message_into_session(f"Session: {alt_session.strip()}", type_socket)
                session_changed = Choice(dir=dir_given, alternatives=alternatives_parsed)
            else:
                print("Error: wrong syntax") # not handled as exception but could be

        # end session
        if ses_info == "End":
            session_changed = End()
        # return resulting session
        return session_changed

    else:
        print("Errror: Invalid request") # not handled as exception but could be

# DEFINE OPTIONAL FUNCTIONS HERE!
def server_parser_func(message):
    return message

def client_parser_func(message):
    return message

# ------------- Initialize Proxy  ----------------------------------------------------------------------
async def start_proxy(proxy_address: int, server_address: str):
    '''
    Initializes the proxy's websocket connection and connects it to server, then starts main proxy function
    to handle client-server communication

        Args:
            proxy_address (int): port where a connection with the proxy can be established
            server_address (str): server address
    '''
    stop_event = asyncio.Event()  # Create event to track when to stop
    
    async def handler(websocket):
        try:
            await proxy_websockets(server_address, websocket, server_parser_func, client_parser_func)
        except Exception as e:
            print(f"Error in handler: {e}")
        finally:
            print("Handler finished ...")
            stop_event.set()  # Trigger stop when all clients are gone

    try:
        server = await websockets.serve(handler, "localhost", proxy_address)
        print("Proxy started, waiting for client...")
        await stop_event.wait()  # Exit when stop_event is set
        print("Closing connection with server...")
        server.close()
        await server.wait_closed()  # Ensure server fully shuts down
    except Exception as e:
        print(f"The proxy encountered an error. Please try again!")

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
