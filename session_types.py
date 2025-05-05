from typing import Optional, Dict
from dataclasses import dataclass # so that @dataclass(frozen=true) can be used

# -- define session components "dir" and "label" --------------------------------------------------------------------------
class Dir:
    def __init__(self, dir: str):
        self.dir = dir # only send or recv

@dataclass(frozen=True)
class Label:
    label: str

# -- define session and session types ---------------------------------------------------------------------------------
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


# --- define session dictionary --------------------------------------------------------------------------------------
        
# global dictionary to keep info about protocols and sessions
class GlobalDict:
    def __init__(self, records: Dict[Label, Session]):
        self.dir = dir
        self.records = records
    
    def add(self, def_ses:Def) -> None:
        '''
        Adds a new protocol to the global dicitonary of protocols.

            Args:
                def_ses (Def): def session that works as protocol
            
        Doesn't return anything.
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
                name (Label): name of the protocol

            Returns:
                A protocol's session if found in the global dictionary or nothing otherwise
        '''
        # print(f"Looking for label: {name} in dictionary...") # comment out to debug
        if not name in self.records:
            print(f"The session {name.label} does not exist.") # not handled as exception but could be
        else:
            return self.records[name]

# --- define errors --------------------------------------------------------------------------------------

# define schema validation fail error
class SchemaValidationError(Exception):
    """Exception raised for errors in schema validation."""
    def __init__(self, message="Schema validation failed"):
        self.message = message
        super().__init__(self.message)