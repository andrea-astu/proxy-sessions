# to be able to use modules from other files
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

import pytest
from session_logic.parsers import message_into_session, session_into_message
from session_logic.session_types import *

import difflib

# -- Define examples for testing ------------------------------------------------------------------------
protocol_a_str = (
                'Session: Def, Name: A, Cont: Session: Choice, Dir: send, Alternatives: '
                '[(Label: Add, Session: Single, Dir: recv, Payload: { type: "number" }, Cont: '
                'Session: Single, Dir: recv, Payload: { type: "number" }, Cont: '
                'Session: Single, Dir: send, Payload: { type: "number" }, Cont: '
                'Session: Ref, Name: A), '
                '(Label: Neg, Session: Single, Dir: recv, Payload: { type: "number" }, Cont: '
                'Session: Single, Dir: send, Payload: { type: "number" }, Cont: '
                'Session: Ref, Name: A), '
                '(Label: Greeting, Session: Single, Dir: recv, Payload: { type: "string" }, Cont: '
                'Session: Single, Dir: send, Payload: { type: "string" }, Cont: '
                'Session: Ref, Name: A), '
                '(Label: Goodbye, Session: Single, Dir: send, Payload: { type: "string" }, Cont: '
                'Session: Ref, Name: A), '
                '(Label: Quit, Session: End)]'
            )

protocol_a_session = Def(
    name="A",
    cont=Choice(
        dir=Dir("send"),
        alternatives={
            Label("Add"): Single(
                dir=Dir("recv"),
                payload='{ type: "number" }',
                cont=Single(
                    dir=Dir("recv"),
                    payload='{ type: "number" }',
                    cont=Single(
                        dir=Dir("send"),
                        payload='{ type: "number" }',
                        cont=Ref("A")
                    )
                )
            ),
            Label("Neg"): Single(
                dir=Dir("recv"),
                payload='{ type: "number" }',
                cont=Single(
                    dir=Dir("send"),
                    payload='{ type: "number" }',
                    cont=Ref("A")
                )
            ),
            Label("Greeting"): Single(
                dir=Dir("recv"),
                payload='{ type: "string" }',
                cont=Single(
                    dir=Dir("send"),
                    payload='{ type: "string" }',
                    cont=Ref("A")
                )
            ),
            Label("Goodbye"): Single(
                dir=Dir("send"),
                payload='{ type: "string" }',
                cont=Ref("A")
            ),
            Label("Quit"): End()
        }
    )
)

protocol_b_str = (
    'Session: Def, Name: B, Cont: Session: Choice, Dir: send, Alternatives: ['
    '(Label: Divide, Session: Single, Dir: recv, Payload: { type: "number" }, Cont: '
    'Session: Single, Dir: recv, Payload: { type: "number" }, Cont: '
    'Session: Single, Dir: send, Payload: { type: "number" }, Cont: '
    'Session: Ref, Name: B), '
    '(Label: List, Session: Single, Dir: recv, Payload: { type: "string" }, Cont: '
    'Session: Single, Dir: send, Payload: { type: "array", payload: { type: "number" } }, Cont: '
    'Session: Ref, Name: B), '
    '(Label: Quit, Session: End)]'
)

protocol_b_session = Def(
    name="B",
    cont=Choice(
        dir=Dir("send"),
        alternatives={
            Label("Divide"): Single(
                dir=Dir("recv"),
                payload='{ type: "number" }',
                cont=Single(
                    dir=Dir("recv"),
                    payload='{ type: "number" }',
                    cont=Single(
                        dir=Dir("send"),
                        payload='{ type: "number" }',
                        cont=Ref("B")
                    )
                )
            ),
            Label("List"): Single(
                dir=Dir("recv"),
                payload='{ type: "string" }',
                cont=Single(
                    dir=Dir("send"),
                    payload='{ type: "array", payload: { type: "number" } }',
                    cont=Ref("B")
                )
            ),
            Label("Quit"): End()
        }
    )
)

# -- Valid tests ---------------------------------------------------------------------------

def test_message_into_session_protocol_a():
    parsed = message_into_session(protocol_a_str)
    assert parsed == protocol_a_session

def test_session_into_message_protocol_a():
    serialized = session_into_message(protocol_a_session)
    assert serialized == protocol_a_str

def test_message_into_session_protocol_b():
    parsed = message_into_session(protocol_b_str)
    assert parsed == protocol_b_session

def test_session_into_message_protocol_b():
    serialized = session_into_message(protocol_b_session)
    assert serialized == protocol_b_str

# -- Failing tests -----------------------------------------------------------------------------------

def test_invalid_prefix():
    with pytest.raises(SessionError, match="Error parsing session"):
        message_into_session("InvalidPrefix: Single, Dir: send, Payload: ..., Cont: End")

def test_invalid_single_format():
    with pytest.raises(SessionError, match="Error parsing message into session: wrong syntax"):
        message_into_session("Session: Single, Dir: send Payload: ..., Cont: End")  # Missing commas

def test_invalid_def_format():
    with pytest.raises(SessionError, match="Error parsing message into session: wrong syntax"):
        message_into_session("Session: Def, Name: ProtocolOnly")  # Missing cont

def test_invalid_ref_format():
    with pytest.raises(SessionError, match="Error parsing message into session: wrong syntax"):
        message_into_session("Session: Ref ProtocolName")  # Wrong format

def test_invalid_choice_format():
    with pytest.raises(SessionError, match="Error parsing message into session: wrong syntax"):
        message_into_session("Session: Choice, Dir: send, Alts: [wrong]")  # Misspelled "Alternatives"

def test_missing_session_prefix():
    with pytest.raises(SessionError, match="Error parsing session"):
        message_into_session("Choice, Dir: send, Alternatives: []")  # Missing "Session: " prefix

# print(session_into_message(protocol_a_session))
# print(session_into_message(protocol_b_session))

def show_string_diff(expected: str, actual: str):
    print("=== STRING DIFFERENCE ===")
    diff = difflib.ndiff(expected.splitlines(), actual.splitlines())
    for line in diff:
        if line.startswith("- ") or line.startswith("+ ") or line.startswith("? "):
            print(line)

# Example usage
show_string_diff(protocol_a_str, session_into_message(protocol_a_session))