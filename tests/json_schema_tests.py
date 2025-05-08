import json
import pytest
from session_logic.schema_validation import checkPayload

# Define JSON test data
example_string = json.dumps("hello")
example_bool = json.dumps(True)
example_null = json.dumps(None)
example_number = json.dumps(42)
example_array1 = json.dumps([1, 2, 3])
example_array2 = json.dumps(["a", 5, True])
example_tuple = json.dumps([1, 2, "and", False])
example_def = json.dumps({"name": 7})
example_record = json.dumps({"age": 25, "name": "Alice", "isAdmin": True})

# ---------------------- Valid tests ----------------------

def test_string():
    assert checkPayload(example_string, '{ type: "string" }', '{ type: "string" }') == "Valid payload type"

def test_bool():
    assert checkPayload(example_bool, '{ type: "bool" }', '{ type: "bool" }') == "Valid payload type"

def test_null():
    assert checkPayload(example_null, '{ type: "null" }', '{ type: "null" }') == "Valid payload type"

def test_number():
    assert checkPayload(example_number, '{ type: "number" }', '{ type: "number" }') == "Valid payload type"

def test_valid_array():
    assert checkPayload(example_array1, '{ type: "array", payload: { type: "number" } }',
                        '{ type: "array", payload: { type: "number" } }') == "Valid payload type"

def test_valid_tuple():
    assert checkPayload(example_tuple,
        '{ type: "tuple", payload: [{ type: "number" }, { type: "number" }, { type: "string" }, { type: "bool" }] }',
        '{ type: "tuple", payload: [{ type: "number" }, { type: "number" }, { type: "string" }, { type: "bool" }] }') == "Valid payload type"

def test_valid_union():
    assert checkPayload(example_tuple,
        '{ type: "union", payload: [{ type: "number" }, { type: "bool" }, { type: "string" }] }',
        '{ type: "union", payload: [{ type: "number" }, { type: "bool" }, { type: "string" }] }') == "Valid payload type"

def test_valid_def():
    assert checkPayload(example_def,
        '{ type: "def", name: { type: "string" }, payload: { type: "number" } }',
        '{ type: "def", name: { type: "string" }, payload: { type: "number" } }') == "Valid payload type"

def test_valid_record():
    assert checkPayload(example_record,
        '{ type: "record", payload: [{ type: "number" }, { type: "string" }, { type: "bool" }] }',
        '{ type: "record", payload: [{ type: "number" }, { type: "string" }, { type: "bool" }] }') == "Valid payload type"

# ---------------------- Failing tests ----------------------

def test_invalid_array():
    with pytest.raises(Exception):
        checkPayload(example_array2, '{ type: "array", payload: { type: "string" } }',
                                  '{ type: "array", payload: { type: "string" } }')

def test_tuple_length_mismatch():
    with pytest.raises(Exception):
        checkPayload(example_tuple,
            '{ type: "tuple", payload: [{ type: "number" }, { type: "number" }, { type: "string" }] }',
            '{ type: "tuple", payload: [{ type: "number" }, { type: "number" }, { type: "string" }] }')

def test_tuple_type_mismatch():
    with pytest.raises(Exception):
        checkPayload(example_tuple,
            '{ type: "tuple", payload: [{ type: "number" }, { type: "bool" }, { type: "string" }, { type: "bool" }] }',
            '{ type: "tuple", payload: [{ type: "number" }, { type: "bool" }, { type: "string" }, { type: "bool" }] }')

def test_invalid_union():
    with pytest.raises(Exception):
        checkPayload(example_tuple,
            '{ type: "union", payload: [{ type: "number" }, { type: "string" }] }',
            '{ type: "union", payload: [{ type: "number" }, { type: "string" }] }')