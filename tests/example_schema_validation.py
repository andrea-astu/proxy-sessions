import json
from session_logic.schema_validation import checkPayload
from typing import Union, Any

def run_test(example:Union[str, bool, list[Any], dict[str, Any]], session_type:str, expected_type:str):
    '''Runs a test case to show better which cases fail ans which succeed.'''
    try:
        result = checkPayload(example, session_type, expected_type)
        print(f"[PASSED]: {result}")
    except Exception as e:
        print(f"[FAILED]: {str(e)}")


if __name__ == "__main__":
    # define examples as json obects
    example_string = json.dumps("hello")
    example_bool = json.dumps(True)
    example_null = json.dumps(None) # None is supposed to be null but we'll see
    example_number = json.dumps(42)
    example_array1 = json.dumps([1, 2, 3]) # should be ok
    example_array2 = json.dumps(["a", 5, True]) # should give error
    example_tuple = json.dumps([1, 2, "and", False])
    example_ref = json.dumps("reference: trial") # reference python object is of type str that starts with "reference: "
    example_not_ref = json.dumps("ref: trial") # if wrongly typed, it throws error when checked against ref schema
    example_def = {
    "name": 7
    }
    example_def = json.dumps(example_def)
    example_record = json.dumps({"age": 25, "name": "Alice", "isAdmin": True})

    # run through tests
    run_test(example_string, '{ type: "string" }', '{ type: "string" }')
    run_test(example_bool, '{ type: "bool" }', '{ type: "bool" }')
    run_test(example_null, '{ type: "null" }', '{ type: "null" }')
    run_test(example_number, '{ type: "number" }', '{ type: "number" }')
    run_test(example_array1, '{ type: "array", payload: { type: "number" } }', '{ type: "array", payload: { type: "number" } }')
    run_test(example_array2, '{ type: "array", payload: { type: "string" } }', '{ type: "array", payload: { type: "string" } }')
    run_test(example_tuple, '{ type: "tuple", payload: [{ type: "number" }, { type: "number" }, { type: "string" }, { type: "bool" }] }',
                            '{ type: "tuple", payload: [{ type: "number" }, { type: "number" }, { type: "string" }, { type: "bool" }] }') # should work
    run_test(example_tuple, '{ type: "tuple", payload: [{ type: "number" }, { type: "number" }, { type: "string" }] }',
                            '{ type: "tuple", payload: [{ type: "number" }, { type: "number" }, { type: "string" }] }') # should fail because of length
    run_test(example_tuple, '{ type: "tuple", payload: [{ type: "number" }, { type: "bool" }, { type: "string" }, { type: "bool" }] }',
                            '{ type: "tuple", payload: [{ type: "number" }, { type: "bool" }, { type: "string" }, { type: "bool" }] }') # sould fail ebcause of type
    run_test(example_tuple, '{ type: "union", payload: [{ type: "number" }, { type: "string" }] }',
                            '{ type: "union", payload: [{ type: "number" }, { type: "string" }] }') # should fail because of type missing in components
    run_test(example_tuple, '{ type: "union", payload: [{ type: "number" }, { type: "bool" }, { type: "string" }] }',
                            '{ type: "union", payload: [{ type: "number" }, { type: "bool" }, { type: "string" }] }') # sould succeed
    run_test(example_def, '{ type: "def", name: { type: "string" }, payload: { type: "number" } }',
                          '{ type: "def", name: { type: "string" }, payload: { type: "number" } }') # basic def; usually should be in another structure
    run_test(example_record, '{ type: "record", payload: [{ type: "number" }, { type: "string" }, { type: "bool" }] }',
                             '{ type: "record", payload: [{ type: "number" }, { type: "string" }, { type: "bool" }] }')