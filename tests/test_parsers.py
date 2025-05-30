# to be able to use modules from other files
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

import pytest
from session_logic.parsers import * 
from session_logic.session_types import *

import json

# -- Define protcol examples for testing ------------------------------------------------------------------------
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

# -- Define JSON test data for payload parsing -----------------------------------------------------------

example_string = json.dumps("hello")
example_bool = json.dumps(True)
example_null = json.dumps(None)
example_number = json.dumps(42)
example_array1 = json.dumps([1, 2, 3])
# example_union = json.dumps(["a", 5, True, False])
example_tuple = json.dumps([1, 2, "and", False])
example_def = json.dumps({"name": 7})
example_record = json.dumps({"age": 25, "name": "Alice", "isAdmin": True})

# -- Valid protocol parsing tests ---------------------------------------------------------------------------

def test_message_into_session_protocol_a():
    parsed = message_into_session(protocol_a_str)
    assert parsed == protocol_a_session

def test_session_into_message_protocol_a():
    as_string = session_into_message(protocol_a_session)
    assert as_string == protocol_a_str

def test_message_into_session_protocol_b():
    parsed = message_into_session(protocol_b_str)
    assert parsed == protocol_b_session

def test_session_into_message_protocol_b():
    as_string = session_into_message(protocol_b_session)
    assert as_string == protocol_b_str

# -- Failing protocol parsing tests -----------------------------------------------------------------------------------

def test_invalid_prefix():
    with pytest.raises(SessionError, match="Error parsing session"):
        message_into_session('InvalidPrefix: Single, Dir: send, Payload: { type: "number" }, Cont: End')

def test_invalid_single_format():
    with pytest.raises(SessionError, match="Error parsing message into session: wrong syntax"):
        message_into_session('Session: Single, Dir: send Payload: { type: "number" }, Cont: End')  # Missing commas

def test_invalid_def_format():
    with pytest.raises(SessionError, match="Error parsing message into session: wrong syntax"):
        message_into_session('Session: Def, Name: ProtocolOnly')  # Missing cont

def test_invalid_ref_format():
    with pytest.raises(SessionError, match="Error parsing message into session: wrong syntax"):
        message_into_session('Session: Ref ProtocolName')  # Wrong format

def test_invalid_choice_format():
    with pytest.raises(SessionError, match="Error parsing message into session: wrong syntax"):
        message_into_session('Session: Choice, Dir: send, Alts: [wrong]')  # Misspelled "Alternatives"

def test_missing_session_prefix():
    with pytest.raises(SessionError, match="Error parsing session"):
        message_into_session('Choice, Dir: send, Alternatives: []')  # Missing "Session: " prefix

# -- Valid payload parsing/creation tests -----------------------------------------------------------------------------------

# take json object and convert it to payload string
def test_json_string():
    assert json_payload_to_string(example_string) == '{ type: "string" }'

def test_json_bool():
    assert json_payload_to_string(example_bool) == '{ type: "bool" }'

def test_json_null():
    assert json_payload_to_string(example_null) == '{ type: "null" }'

def test_json_number():
    assert json_payload_to_string(example_number) == '{ type: "number" }'

def test_json_array():
    assert json_payload_to_string(example_array1) == '{ type: "array", payload: { type: "number" } }'

def test_json_tuple():
    assert json_payload_to_string(example_tuple) == '{ type: "tuple", payload: [{ type: "number" }, { type: "number" }, { type: "string" }, { type: "bool" }] }'

def test_json_def():
    assert json_payload_to_string(example_def) == '{ type: "def", name: { type: "string" }, payload: { type: "number" } }'

def test_json_record():
    assert json_payload_to_string(example_record) == '{ type: "record", payload: [{ type: "number" }, { type: "string" }, { type: "bool" }] }'

# define your payload
def test_payload_str():
    assert payload_to_string('string') == '{ type: "string" }'

def test_payload_bool():
    assert payload_to_string('bool') == '{ type: "bool" }'

def test_payload_null():
    assert payload_to_string('none') == '{ type: "null" }'

def test_payload_number():
    assert payload_to_string('number') == '{ type: "number" }'

def test_payload_array():
    assert payload_to_string('array', 'number') == '{ type: "array", payload: { type: "number" } }'

def test_payload_tuple():
    assert payload_to_string('tuple', ['number', 'number', 'string', 'bool']) == '{ type: "tuple", payload: [{ type: "number" }, { type: "number" }, { type: "string" }, { type: "bool" }] }'

def test_paylaod_def():
    assert payload_to_string('def', 'number') == '{ type: "def", name: { type: "string" }, payload: { type: "number" } }'

def test_payload_record():
    assert payload_to_string('record', ['number', 'string', 'bool']) == '{ type: "record", payload: [{ type: "number" }, { type: "string" }, { type: "bool" }] }'

def test_payload_union():
    assert payload_to_string('union', ['number', 'string', 'bool']) == '{ type: "union", payload: [{ type: "number" }, { type: "string" }, { type: "bool" }] }'

def test_payload_union_unique():
    assert payload_to_string('union', ['number', 'bool', 'bool']) == '{ type: "union", payload: [{ type: "number" }, { type: "bool" }] }'


# -- Failing payload parsing/creation tests ----------------------------------------------------------------------------------

# define your payload
def test_types_array_list():
    with pytest.raises(ParsingError, match="Array payload can only be of one type"):
        payload_to_string('array', ['number', 'string'])

def test_types_not_as_list():
    with pytest.raises(ParsingError, match="Payload has to be given as a list"):
        payload_to_string('tuple', 'number')

def test_types_not_as_str():
    with pytest.raises(ParsingError, match="Def payload has to be given as a string"):
        payload_to_string('def', ['number'])