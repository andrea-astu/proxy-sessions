# to be able to use modules from other files
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from session_logic.session_types import *
import re # for parsing sessions
from typing import Any # for type definition

# Messages and Session Parsers

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


# DEFINE FUNCTIONS HERE!
# For now they're meant to not change the messages at all
def server_parser_func(message:Any):
    return message

def client_parser_func(message:Any):
    return message