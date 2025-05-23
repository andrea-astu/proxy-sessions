# to be able to use modules from other files
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from session_logic.session_types import *
import re # for parsing sessions
from typing import Any, Literal, Union, cast # for type definition

import json

# -- Define functions that enable proxy to change payload ------------------------------

# For now they're meant to not change the messages at all
def server_parser_func(message:Any):
    return message

def client_parser_func(message:Any):
    return message


#-- String <--> Session Parsers --------------------------------------------------------

def message_into_session(ses_info:str, type_socket:str="") -> Session:
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
                session_changed = Single(dir=Dir(dir_given), payload=pay_given, cont=message_into_session(cont_ses, type_socket))
            else:
                raise SessionError("Error parsing message into session: wrong syntax")

        # def session; uses type_socket parameter
        elif ses_info.startswith("Def"):
            pattern = r"Def, Name: (.*?), Cont: (.*)"
            match = re.match(pattern, ses_info)
            if match:
                name_given, cont_ses = match.groups()
                # print(f"Parsing protocol {name_given}") # comment put to debug
                # recursively parse choice sessions defined in protocol with "cont"
                session_changed = Def(name=f"{name_given}_{type_socket}", cont=message_into_session(cont_ses, type_socket))
            else:
                raise SessionError("Error parsing message into session: wrong syntax")

        # ref session
        elif ses_info.startswith("Ref"):
            if ses_info.startswith("Ref, Name: "):
                name_given = ses_info[11:] # references protocol name
                session_changed = Ref(name=f"{name_given}_{type_socket}")
            else:
                raise SessionError("Error parsing message into session: wrong syntax")

        # choice session
        # Idea: session would look like: Session: Choice, Dir: send, Alternatives: [{Label: Add, Session: Single, }]
        elif ses_info.startswith("Choice"):
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
                alternatives_parsed:Dict[Label, Session] # in order for the creation of Choice to be ok
                session_changed = Choice(dir=Dir(dir_given), alternatives=alternatives_parsed)
            else:
                raise SessionError("Error parsing message into session: wrong syntax")
        # end session
        elif ses_info == "End":
            session_changed = End()
        # if no cases match
        else:
            raise SessionError("Error parsing session")
        # return resulting session
        return session_changed
    else:
        raise SessionError("Error parsing session")

def session_into_message(session: Session) -> str:
    '''
    Serializes a Session object into a string.
    
        Args:
            session (Session): the session object to serialize
        
        Returns:
            str: string representation of the session
    '''
    if isinstance(session, Single):
        return (
            f"Session: Single, Dir: {session.dir}, Payload: {session.payload}, "
            f"Cont: {session_into_message(session.cont)}"
        )
    
    elif isinstance(session, Def):
        return (
            f"Session: Def, Name: {session.name}, Cont: {session_into_message(session.cont)}"
        )
    
    elif isinstance(session, Ref):
        return f"Session: Ref, Name: {session.name}"
    
    elif isinstance(session, Choice):
        alternatives: list[str] = []
        for label_given, alt_session in session.alternatives.items():
            alt_str = (
                f"(Label: {label_given.label}, Session: {session_into_message(alt_session)[9:]})"
            )
            alternatives.append(alt_str)
        return (
            f"Session: Choice, Dir: {session.dir}, Alternatives: [{', '.join(alternatives)}]"
        )
    
    elif isinstance(session, End):
        return "Session: End"
    
    else:
        raise ValueError("Unknown session type")


#-- Create payload string easier --------------------------------------------------------

# Literals for allowed parameter strings
BasicTypes = Literal["boolean", "string", "none", "number"] # does it have to be all upper case? 
AllTypes = Literal["boolean", "string", "none", "number", "array", "tuple", "union", "def", "record"]
PayloadTypes = Union[AllTypes, list[AllTypes], None]

def payload_to_string_v1(type_str:AllTypes, payload:PayloadTypes=None) -> str:
    # separate parameters of array, tuple, etc.??
    match type_str:
        case "boolean":
            return '{ type: "bool" }'
        case "string":
            return '{ type: "string" }'
        case "none":
            return '{ type: "null" }'
        case "number":
            return '{ type: "number" }'
        case "array":
            if isinstance(payload, str): # checking array only accepts ONE payload type
                return f'{{ type: "array", payload: {payload_to_string_v1(type_str=payload)} }}'
            else:
                return "Array payload can only be of one type" # make return exception or something
        case ("tuple" | "union" | "record"):
            # don't need a length because list of types gives us length alraedy
            if isinstance(payload, list):
                elements = [payload_to_string_v1(i) for i in payload]
                return f'{{ type: "{type}", payload: [ ' + ", ".join(elements) + ' ] }}'
            else:
                return "Payload has to be given as a list" # make return exception or something
        case "def":
            if isinstance(payload, str): # checking array only accepts ONE payload type
                return f'{{ type: "def", name: {{ type: "string" }}, payload: {payload_to_string_v1(type_str=payload)} }}'
            else:
                return "Def payload can only be of one type" # make return exception or something
        case _:
            return "" # make return exception or something


def json_payload_to_string(payload:Any) -> str | list[str]:
    # paylaod has to be of type JSON but that's difficult to describe
    # use json schemas??
    payload = json.loads(payload) # unpack payload from JSON
    if isinstance(payload, bool):
        return '{ type: "bool" }'
    elif isinstance(payload, str):
        return '{ type: "string" }'
    elif payload is None:
        return '{ type: "null" }'
    elif isinstance(payload, (int, float, complex)):
        return '{ type: "number" }'
    elif isinstance(payload, list):
        # case array
        if len({type(x) for x in payload}) == 1: # checking case array elements are of the same type
            return f'{{ type: "array", payload: {json_payload_to_string(payload=json.dumps(payload[0]))} }}'
        # case union or tuple? return list of both options?
        else:
            elements = [json_payload_to_string(json.dumps(i)) for i in payload]
            return [f'{{ type: "tuple", payload: [ ' + ", ".join(elements) + ' ] }}',
                    f'{{ type: "tuple", payload: [ ' + ", ".join(list(set(elements))) + ' ] }}']
    elif isinstance(payload, dict): # maybe check keys are strings ALWAYS?
        if all(isinstance(key, str) for key in payload):
            if len(payload) == 1: # if dict only has one element it could be def or record??
                return [f'{{ type: "def", name: {{ type: "string" }}, payload: {json_payload_to_string(json.dumps(payload))} }}',
                        f'{{ type: "def", payload: [{json_payload_to_string(json.dumps(payload))}] }}']
            # if 2+ elems then definitely record
            else:
                elements = [json_payload_to_string(json.dumps(i)) for i in list(payload.values())] # iterate through all values of keys
                return f'{{ type: "record", payload: [ ' + ", ".join(list(set(elements))) + ' ] }}'
        else:
            return "All keys in a def or record type have to be strings" # make return exception or something

    else:
        return "This is not a type that is handled as payload by the proxy" # make return exception or something