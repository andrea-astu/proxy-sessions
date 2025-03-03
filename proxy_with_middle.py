from typing import List, Dict, Callable
import re # to parse Connection addresses

#websockets imports
import websockets
import asyncio
import schema_validation
# import logging # used to debug in past codes
 

# define type (find a way to only have certain values)
class Type:  # "types" of type: any, string, number, bool, null
    def __init__(self, kind: str):
        self.kind = kind

class Union(Type): # check it correctly inherits kind
    def __init__(self, components: List[Type]): # add kind = "union"?
        super().__init__("union")
        self.components = components

class Payload(Type): # i don't remember why it's a dictionary -> make NOT dictionary, check later
    def __init__(self, name: str):
        super().__init__("payload")
        # self.payload = payload
        self.name = name
    
class Ref(Type):
    def __init__(self, name: str):
        super().__init__("ref")
        self.name = name

class Tuple(Type):
    def __init__(self, payload: List[Type]):
        super().__init__("tuple")
        self.payload = payload

class Array(Type):
    def __init__(self, payload: Type):
        super().__init__("array")
        self.payload = payload

# ------------------- define session types -----------------------------------------------

# define dir and label
class Dir:
    def __init__(self, dir: str):
        self.dir = dir # only send or recv

class Label:
    def __init__(self, label):
        self.label = label

    # make it hashable so it can be looked up in the dictionary -> check if works
    def __hash__(self):
        # Generate a hash based on the label value
        return hash(self.label)

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
    def __init__(self, dir: Dir, payload, cont: Session):
        super().__init__("single")
        self.dir = dir
        self.payload = payload
        self.cont = cont

class Choice(Session):
    def __init__(self, dir: Dir, alternatives: Dict[Label, Session]):
        super().__init__("choice")
        self.dir = dir
        self.alternatives = alternatives
    
    # function that adds a new session to the dictionary of known ones
    def add(self, name: Label, new_ses: Session):
        if name in self.alternatives:
            print("This session already exists. Please define a new one.") # print or return string?
            return
        else:
            self.alternatives[name] = new_ses
    
    def lookup(self, name: Label):
        print(f'Looking up command: {name.label}')
        if not name in self.alternatives:
            print("This session does not exist.")
            return
        else:
            return self.alternatives[name]

    # do I still need this??
    """
    def switch_sessions(self, name: Label):
        if not name in self.alternatives:
            response = "This session does not exist."
        else:
            return self.alternatives[name]
    """

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

# ----------------------------------------------------------------------------------------------------------------

# global dict to keep info about protocols and sessions
class GlobalDict:
    def __init__(self, records: Dict[Label, Session]):
        self.dir = dir
        self.records = records
    
    # function that adds a new protocol
    def add(self, def_ses=Def):
        if def_ses.name in self.records:
            print("This session already exists. Please define a new one.") # print or return string?
            return
        else:
            print(f'Defining {def_ses.name}, cont of type {def_ses.cont.kind}')
            self.records[def_ses.name] = def_ses.cont
    
    # function that returns a protocol's session, usually in the form of a Choice session
    def lookup(self, name: Label):
        print(f"looking for label: {name} in dict {self.records}") # DEBUG
        if not name in self.records:
            print("not found") # DEBUG
            print("This session does not exist.")
        else:
            print("found") # DEBUG
            return self.records[name] # returns session referenced by name; usually a choice
        
protocol_info = GlobalDict({})

async def receive_from_client(websocket):
    response = await websocket.recv()
    return response

async def send_to_client(websocket, message):
    await websocket.send(message)

# in handler, always return a ses. so it is known it's not an End
async def handle_session(ses_server, ses_client, command, server_socket, client_socket): # idk yet abt prot/command params.
    print(f'carry out: {ses_server.kind}, {ses_client.kind}, from {command}') # DEBUG
    # websocket is client
    # always return two sessions, one for server and one for client!
    actual_sessions = (ses_server, ses_client) # initialize actual ses
    ses_server_actual = actual_sessions[0]
    ses_client_actual = actual_sessions[1]
    while ses_server_actual.kind != "end" and ses_client_actual.kind != "end":
        if ses_server_actual.kind == "single" and ses_client_actual.kind == "single":
            if ses_server_actual.dir == "recv" and ses_client_actual.dir == "send": # server has to recv; therefore first get thing from client and then send to server
                payload_to_transport = await client_socket.recv()
                print(f'payload from client: {repr(payload_to_transport)}') # DEBUG
                print("confirm type of payload")# DEBUG
                print(schema_validation.checkPayload(payload_to_transport, ses_client_actual.payload, ses_server_actual.payload))
                await server_socket.send(payload_to_transport)
                print("Message sent from client to server")
                # ref_return_server, ref_return_client = await handle_session(ses_server.cont, ses_client.cont, command, server_socket, client_socket) # continue to next session
                # actual_sessions = (ses_server_actual.cont, ses_client_actual.cont)
            elif ses_server_actual.dir == "send" and ses_client_actual.dir == "recv":
                payload_to_transport = await server_socket.recv()
                await client_socket.send(payload_to_transport)
                print(schema_validation.checkPayload(payload_to_transport, ses_server_actual.payload, ses_client_actual.payload))
                print(f'payload from server: {payload_to_transport}') # DEBUG
                print("Message sent from server to client")
                # ref_return_server, ref_return_client = await handle_session(ses_server.cont, ses_client.cont, command, server_socket, client_socket) # continue to next session
                # return ref_return_server, ref_return_client
            else:
                print ("The direction given to the Single session is not recognized or server and client do not ahve opposing directions")
                return End(), End()
            actual_sessions = (ses_server_actual.cont, ses_client_actual.cont) # in any case in single continue with cont
        elif ses_server_actual.kind == "choice" and ses_client_actual.kind == "choice":
            # ref_return_server, ref_return_client = await handle_session(ses_server_actual.lookup(Label(command)), ses_client_actual.lookup(Label(command)), command, server_socket, client_socket) # command has to be Label; will that work if str? or typecast as Label in proxy?
            actual_sessions = (ses_server_actual.lookup(Label(command)), ses_client_actual.lookup(Label(command)))
        elif ses_server_actual.kind == "ref" and ses_client_actual.kind == "ref": # ref ALWAYS returns session of type Choice!
            print(f'referencing server session {ses_server_actual.name} and client session {ses_client_actual.name}') # DEBUG
            found_server = protocol_info.lookup(ses_server_actual.name)
            found_client = protocol_info.lookup(ses_client_actual.name)
            print(f'actual ses. server session of type {found_server.kind}')
            return found_server, found_client
        else:
            print ("Unknown session type or sessions don't match")
            return End(), End()
        # necessary or automatically assigned if actual_sessions changes??
        ses_server_actual = actual_sessions[0]
        ses_client_actual = actual_sessions[1]
    # if ses_server.kind == "end" and ses_client.kind == "end":
        # return End(), End() 
    # if ses_server_actual.kind == "end" and ses_client_actual.kind == "end":
        # print ("Unknown session type or sessions don't match")
    return End(), End()
    

# type_socket can be "client" or "server"
async def define_protocols(ws_socket, type_socket:str):
    # ws_socket can be client or server; type defines which one
    session_as_str = await ws_socket.recv() # first protocol; has to be min 1
    # send type to session conversion so it can be added to name
    protocol_definition = message_into_session(session_as_str, type_socket)
    # sockets not needed to define a protocol, only session
    # await handle_session(ses=protocol_definition, command=None, server_socket=None, client_socket=None) # declares 1st protocol
    protocol_info.add(protocol_definition)

    while protocol_definition.kind != "end": # wait until server defines all protocols
        session_as_str = await ws_socket.recv()
        # print(f'protocol received: {session_as_str}') # DEBUG
        protocol_definition = message_into_session(session_as_str, type_socket) # all of these should be Def sessions! maybe give error if not;  received as string, transformed into Session
        #if protocol_definition.kind == "end":
            # break # break while
        # else:
        (print("session transformed ok :) Going to handler")) # Debug
        # await handle_session(ses=protocol_definition, command=None, server_socket=None, client_socket=None) # Giving Def to handler; will add protocol to list of protocols; command None
        if protocol_definition.kind != "end":
            protocol_info.add(protocol_definition)

# server_parser is a function that transforms what the server says in something the client understands
# client parser is a function that transforms what the client says in something the server understands
# proxy session work: data -> single, def -> def, ref -> ref, quit -> exit proxy
# websocket is the "direction" the client is gonna be listening on
async def proxy_websockets(server:str, websocket_client, server_parser: Callable, client_parser: Callable): # server as uri for now; add client somehow! Or amybe client message though idk how
    # actual_ses = Ref(name="temp") #  just to initialize var with something
    async with websockets.connect(server) as server_ws:
        try:
            # define protocols
            await define_protocols(server_ws, "server")
            await define_protocols(websocket_client, "client")
        
            while True:
                # client chooses protocol
                print("start of protocol def") # DEBUG 
                protocol_name = await websocket_client.recv() # protocol
                protocol_name = protocol_name[10:]# protocol of type "Protocol: ___" 
                print(f'prot:{protocol_name}') # DEBUG
                # get both client and server sessions based on protocol
                actual_ses_server, actual_ses_client = await handle_session(Ref(f"{protocol_name}_server"), Ref(f"{protocol_name}_client"), None, server_ws, websocket_client) # choice ses
                print(f'actual session: {actual_ses_server}, {actual_ses_client} under protocol {protocol_name}') # DEBUG
                # step 3: recursively carry out sessions until we get an "End" back -> idk if it'll work :/
                while actual_ses_server.kind != "end" and actual_ses_client.kind != "end": # MAYBE DEFINE ACTUAL_SES BEFORE???
                    await server_ws.send(protocol_name) # always have to tell server which is protocol!
                    command = await websocket_client.recv() # (action/operation) name
                    print(f'command: {command}') # DEBUG
                    await server_ws.send(command)
                    print(f"actual server ses before: {actual_ses_server}")
                    actual_ses_server, actual_ses_client = await handle_session(actual_ses_server, actual_ses_client, command, server_ws, websocket_client) # carries out exchange dictated in that protocol's command
                    # print(f'actual ses kind: {actual_ses.kind}') # DEBUG
                    print(f'actual ses server : {actual_ses_server}') # DEBUG
                    # if actual_ses.kind == "ref":
                print("exited end loop") # DEBUG  


        except websockets.ConnectionClosedError:
            print("There has been an error!")

#------------ Messages and Session Parsers (not needed for now) -------------------------------------------------------------------

# function to parse the messages sent to 
# type parameter is only for def sessions to add server or client to protocol name
def message_into_session(ses_info:str, type_socket:str=None) -> Session:
    if ses_info.startswith("Session: "):
        ses_info = ses_info[9:] # split string to figure out which kind of session; check if this splitting works
        print(f'ses_info: "{ses_info}"')
        # transform single -> how to make cont optional? For now just Cont
        if ses_info.startswith("Single"):
            print("Parsing single") # DEBUG
            pattern = r"Single, Dir: (.*?), Payload: (.*?), Cont: (.*)" # for now without cont End! While I figure it out // * is to pass remaining string
            match = re.match(pattern, ses_info)
            if match:
                dir_given, pay_given, cont_ses = match.groups()
                if ((dir_given != "send") and (dir_given != "recv")): return "Invalid direction given" # make sure direction can ONLY be send or receive
                # cont_ses = message_into_session(cont_ses) # turn cont into a proper Session
                session_changed = Single(dir=dir_given, payload=pay_given, cont=message_into_session(cont_ses, type_socket)) # first without cont
                # tryyyy
                # cont_parsed = message_into_session(cont_sessions)
                # session_changed =  Single(
                    # dir=Dir(dir_given),
                    # payload=Payload(payload_given),
                    # cont=cont_parsed

            else:
                print("Wrong syntax!")
        
        # transform def
        # use parameter "type"
        if ses_info.startswith("Def"):
            print("Parsing def") # DEBUG
            # pattern = r"Def, Name: (.*?), Cont: \{(.*)\}"
            pattern = r"Def, Name: (.*?), Cont: (.*)"
            match = re.match(pattern, ses_info)
            if match:
                name_given, cont_ses = match.groups()
                print(f'name: {name_given} \n')
                print(f'{cont_ses}\n')
                # cont_ses = message_into_session(cont_ses) # turn cont into a proper Session
                session_changed = Def(name=f"{name_given}_{type_socket}", cont=message_into_session(cont_ses, type_socket))
            else:
                print("Wrong syntax!")

        # transform ref
        if ses_info.startswith("Ref"): # for ref use string "parsing" bc match is not working
            print("Parsing ref") # DEBUG
            if ses_info.startswith("Ref, Name: "):
                name_given = ses_info[11:]
                print(f'name given for ref: {name_given}') # DEBUG
                session_changed = Ref(name=f"{name_given}_{type_socket}")
            else:
                print("Wrong syntax!")

            
        # transform choice
        # Idea: session would look like: Session: Choice, Dir: send, Alternatives: [{Label: Add, Session: Single, }]
        if ses_info.startswith("Choice"):
            print("Parsing choice") # DEBUG
            pattern = r"Choice, Dir: (.*?), Alternatives: \[(.*)\]" # alternatives like that so it's dict
            match = re.match(pattern, ses_info)
            if match:
                dir_given, alternatives_given = match.groups()

                # parse alternatives
                alternatives_parsed = {} # check if ok
                alt_matches = re.findall(r"\(Label: (.*?), Session: (.*?)\)", alternatives_given) # find all things with this structure in alternatives
                for label, alt_session in alt_matches:
                    # Parse each alternative's session recursively
                    alternatives_parsed[Label(label.strip())] = message_into_session(f"Session: {alt_session.strip()}", type_socket)

                session_changed = Choice(dir=dir_given, alternatives=alternatives_parsed) # alternatives parsing has to be re-written
            else:
                print("Wrong syntax!")

        # transform End
        if ses_info == "End":
            print("Parsing end") # DEBUG
            session_changed = End()

        # return resulting session
        return session_changed

    else:
        print("Invalid request")


def session_into_message(ses:Session) -> str:
    return ""

# for now just return message
def server_parser(message):
    return message

def client_parser(message):
    return message


# ------------- Initialize Proxy  ----------------------------------------------------------------------
async def start_proxy(proxy_address:int, server_address):

    # in order to pass the proxy_websockets function's parameters with websockets.serve
    async def handler(websocket):
        await proxy_websockets(server_address, websocket, server_parser, client_parser)

    async with websockets.serve(handler, "localhost", proxy_address):
        await asyncio.Future()

if __name__ == "__main__":
    # establish connections
    connection_given = False
    print("Welcome! To start, please establish a connection.\n") # get info about port connections

    while (not connection_given):
        dir_info = input("")
        # parse input to extract address info
        pattern = r"Connection: \{(.*?), (.*?)\}"
        match = re.match(pattern, dir_info)

        if match:
            proxy_val, server_val = match.groups()

            # check proxy val
            if proxy_val == "default":
                proxy_address = 7891
            else:
                proxy_address = int(proxy_val)
            # check server val
            if server_val == "default":
                server_address = "ws://127.0.0.1:7890"
            elif server_val.isdigit():
                server_address = f"ws://127.0.0.1:{server_val}"
            else:
                server_address = server_val
            
            # stop while loop
            connection_given = True
            print("Connection succesful!")
        else:
            print("There was an error with your request, please review the format and try again:\n")

    # run proxy
    asyncio.run(start_proxy(proxy_address, server_address))
