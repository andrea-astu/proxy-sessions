from typing import Optional, Dict, Callable

import re # to parse Connection addresses

# websockets imports
import websockets
import asyncio

# to check payload types are ok
import schema_validation

# ------------------- define session types -----------------------------------------------

# define dir and label
class Dir:
    def __init__(self, dir: str):
        self.dir = dir # only send or recv

class Label:
    def __init__(self, label):
        self.label = label

    # make it hashable so it can be looked up in the dictionary
    def __hash__(self):
        return hash(self.label) # Generate a hash based on the label value

    def __eq__(self, other):
        # Ensure equality is based on the label value
        if isinstance(other, Label):
            return self.label == other.label
        return False


# define session
class Session:
    def __init__(self, kind: str):
        self.kind = kind

class Single(Session):
    def __init__(self, dir: Dir, payload:str, cont: Session):
        super().__init__("single")
        self.dir = dir
        self.payload = payload
        self.cont = cont

class Choice(Session):
    def __init__(self, dir: Dir, alternatives: Dict[Label, Session]):
        super().__init__("choice")
        self.dir = dir
        self.alternatives = alternatives
    
    def add(self, name: Label, new_ses: Session):
        '''
        Adds a new session to the choice session dictionary.

        Args:
            name (Label): what the session is called
            new_ses (Session): actual session to be added
        '''
        if name in self.alternatives:
            print(f"Error: defining existing session {name.label}") # not handled as exception but could be
        else:
            self.alternatives[name] = new_ses
    
    def lookup(self, name: Label) -> Optional[Session]:
        '''
        Looks for session in alternatives (the choice session dictionary)

        Args:
            name (Label): name of session
        
        Returns:
            A session if there is one in the dictionary and nothing otherwise
        '''
        if not name in self.alternatives:
            print(f"The session {name.label} does not exist.") # not handled as exception but could be
        else:
            return self.alternatives[name]

class Def(Session):
    def __init__(self, name: str, cont: Session):
        super().__init__("def")
        self.name = name
        self.cont = cont

class Ref(Session):
    def __init__(self, name: str):
        super().__init__("ref")
        self.name = name

class End(Session):
    def __init__(self):
        super().__init__("end")

# ---- Client and server communications, session handlers -----------------------------------------------

# global dictionary to keep info about protocols and sessions
class GlobalDict:
    def __init__(self, records: Dict[Label, Session]):
        self.dir = dir
        self.records = records
    
    def add(self, def_ses=Def):
        '''
        Adds a new protocol to the global dicitonary of protocols.

            Args:
                def_ses (Def): def session that works as protocol
        '''
        if def_ses.name in self.records:
            print(f"The session {def_ses.name} already exists. Please define a new one.") # not handled as exception but could be
        else:
            print(f"Defining protocol {def_ses.name}...") # to track what proxy is doing at moment -> could be removed
            self.records[def_ses.name] = def_ses.cont
    
    def lookup(self, name: Label) -> Optional[Session]:
        '''
        Function that returns a protocol's session, usually in the form of a Choice session

            Args:
                name (Label): name of the session to be returned

            Returns:
                A protocol's session if found in the global dictionary or nothing otherwise
        '''
        # print(f"Looking for label: {name} in dictionary...") # comment out to debug
        if not name in self.records:
            print(f"The session {name.label} does not exist.") # not handled as exception but could be
        else:
            return self.records[name]


async def handle_session(ses_server: Session, ses_client: Session, server_socket, client_socket, command:str=""):
    '''
    Performs actions depending on the given sessions and compares the server and client sessions are actually mirrored.
    Def sessions are not handled here because those define protocols and are instead handled in the define_protocols function.

        Args:
            ses_server (Session): actual session the server is carrying out
            ses_client (Session): actual session the client is carrying out
            server_socket: socket to communicate between proxy and server
            client_socket: socket to communicate between proxy and client
            command (str): Optional argument that refrences the action to be carried out; used for choice sessions

        Returns:
            Two sessions; one for the server and one for the client
    '''
    # initialize sessions
    actual_sessions = (ses_server, ses_client)
    ses_server_actual = actual_sessions[0]
    ses_client_actual = actual_sessions[1]
    # carry out sessions in a loop (useful for cont)
    while ses_server_actual.kind != "end" and ses_client_actual.kind != "end":
        # type single (transports payload from server to client or vice versa)
        # rteurns End sessions if schema validation fails -> could be handled differently
        if ses_server_actual.kind == "single" and ses_client_actual.kind == "single":
            # client sends payload to server
            if ses_server_actual.dir == "recv" and ses_client_actual.dir == "send":
                payload_to_transport = await client_socket.recv()
                # check the payload type being transported matches the payload types defined in the sessions
                try:
                    schema_validation.checkPayload(payload_to_transport, ses_client_actual.payload, ses_server_actual.payload)
                except Exception as e:
                    print(f"Schema validation failed: {e}")
                    return End(), End()
                await server_socket.send(payload_to_transport)
                print("Message sent from client to server") # to track what proxy is doing at moment -> could be removed
            # server sends payload to client
            elif ses_server_actual.dir == "send" and ses_client_actual.dir == "recv":
                payload_to_transport = await server_socket.recv()
                # check the payload type being transported matches the payload types defined in the sessions
                try:
                    schema_validation.checkPayload(payload_to_transport, ses_server_actual.payload, ses_client_actual.payload)
                except Exception as e:
                    print(f"Schema validation failed: {e}")
                    return End(), End()
                await client_socket.send(payload_to_transport) # transport payload if type is ok
                print("Message sent from server to client") # to track what proxy is doing at moment -> could be removed
            else:
                print ("Error: The direction given to the Single session is not recognized or server and client do not have opposing directions.") # not handled as exception but could be
                return End(), End()
            actual_sessions = (ses_server_actual.cont, ses_client_actual.cont) # after a single session start next session
        # type choice (choose a session inside a protocol)
        elif ses_server_actual.kind == "choice" and ses_client_actual.kind == "choice":
            # print(f'Looking up action: {command}...') # comment put to debug
            actual_sessions = (ses_server_actual.lookup(Label(command)), ses_client_actual.lookup(Label(command)))
        # type ref (always returns a session of type choice)
        elif ses_server_actual.kind == "ref" and ses_client_actual.kind == "ref":
            # print(f'Referencing server session {ses_server_actual.name} and client session {ses_client_actual.name}...') # comment out to debug
            found_server = protocol_info.lookup(ses_server_actual.name)
            found_client = protocol_info.lookup(ses_client_actual.name)
            return found_server, found_client
        else:
            print ("Error: Unknown session type or sessions don't match") # not handled as exception but could be
            return End(), End()
        # update sessions to use in while loop
        ses_server_actual = actual_sessions[0]
        ses_client_actual = actual_sessions[1]
    return End(), End() # only returned when both sessions are end sessions
    

async def define_protocols(ws_socket, type_socket:str):
    '''
    Receives strings from client or server that define protocols as Def sessions and adds them to the global
    dictionary until an End Session is received.

        Args:
            ws_socket: client or server socket to receive and send information
            type_socket (str): can either be "server" or "client" depending on which party is sending the protocols
    '''
    session_as_str = await ws_socket.recv() # first protocol; minimum one has to be defined
    protocol_definition = message_into_session(session_as_str, type_socket) # send type to session conversion so it can be added to name
    protocol_info.add(protocol_definition) # add protocl to global dictionary

    # define more protocols
    while protocol_definition.kind != "end":
        session_as_str = await ws_socket.recv()
        protocol_definition = message_into_session(session_as_str, type_socket)
        if protocol_definition.kind != "end":
            protocol_info.add(protocol_definition)
    
    print(f"Registered {type_socket} protocols") # to track what proxy is doing at moment -> could be removed

async def proxy_websockets(server:str, websocket_client, server_parser: Callable, client_parser: Callable):
    '''
    Manages the connection between the client and the server via sessions.

        Args:
            server (str): uri of the server to establish a connection with it
            websocket_client: client websocket to exchange information between it and the proxy
            server_parser (Callable): optional function that changes the server message before sending it to the client
            client_parser (Callable): optional function that changes the client message before sending it to the server
    '''
    async with websockets.connect(server) as server_ws:
        try:
            # define protocols
            await define_protocols(server_ws, "server")
            await define_protocols(websocket_client, "client")
        
            while True:
                protocol_name = await websocket_client.recv() # client chooses protocol 
                protocol_name = protocol_name[10:] # protocol message structure: "Protocol: ___" 
                print(f'Executing protocol {protocol_name}...') # to track what proxy is doing at moment -> could be removed
                # get both client and server sessions by referencing protocol
                actual_ses_server, actual_ses_client = await handle_session(Ref(f"{protocol_name}_server"), Ref(f"{protocol_name}_client"), server_ws, websocket_client) # choice session
                # recursively carry out sessions until we get two "End" sessions back
                while actual_ses_server.kind != "end" and actual_ses_client.kind != "end":
                    await server_ws.send(protocol_name) # always have to tell server which protocol is being used
                    command = await websocket_client.recv() # action name
                    print(f'Carrying out {command} action...') # to track what proxy is doing at moment -> could be removed
                    await server_ws.send(command)
                    actual_ses_server, actual_ses_client = await handle_session(actual_ses_server, actual_ses_client, server_ws, websocket_client, command) # carries out exchange dictated in that protocol's action 
        # handle ok and unexpected connections
        except (websockets.ConnectionClosedOK, websockets.ConnectionClosedError):
            print("Client connection terminated. Closing connections ...")
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
            type_socket (str): optional string for Def sessions to add server or client marker to protocol name
        
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
                if ((dir_given != "send") and (dir_given != "recv")): # make sure direction can ONLY be send or receive
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

# DEFINE OPTIONAL FUNCTIONS HERE!!
def server_parser(message):
    return message

def client_parser(message):
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
            await proxy_websockets(server_address, websocket, server_parser, client_parser)
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
        print("Welcome! To start, please establish a connection. Write 'quit' if you wish to quit the proxy.")

        # user input
        proxy_val = input("Proxy port: ")
        server_val = input("Server port or address: ")

        # quit if user wishes to do so
        if proxy_val.lower() == "quit" or server_val.lower() == "quit":
            print("Closing proxy...")
            asyncio.sleep(3)  # Wait before exit
            exit()

        # check proxy val
        if proxy_val.lower() == "default":
            proxy_address = 7891
        elif proxy_val.isnumeric():
            proxy_address = int(proxy_val)
        else:
            proxy_address = proxy_val
        # check server val
        if server_val.lower() == "default":
            server_address = "ws://127.0.0.1:7890"
        elif server_val.isnumeric():
            server_address = f"ws://127.0.0.1:{server_val}"
        else:
            server_address = server_val
        
        print("Connecting...")

        try:
            # run proxy
            asyncio.run(start_proxy(proxy_address, server_address))
        except Exception as e:
            print(f"The proxy encountered an error. Please try again!")