import json
from schema_validation import checkPayload

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
    

    # run through tests
    print(checkPayload(example_string, '{ type: "string" }', '{ type: "string" }'))
    print(checkPayload(example_bool, '{ type: "bool" }', '{ type: "bool" }'))
    print(checkPayload(example_null, '{ type: "null" }', '{ type: "null" }'))
    print(checkPayload(example_number, '{ type: "number" }', '{ type: "number" }'))
    print(checkPayload(example_array1, '{ type: "array" }, payload: { type: "number" } }', '{ type: "array" }, payload: { type: "number" } }'))
    print(checkPayload(example_array2, '{ type: "array" }, payload: { type: "string" } }', '{ type: "array" }, payload: { type: "string" } }'))
    print(checkPayload(example_tuple, '{ type: "tuple" }, payload: [{ type: "number" }, { type: "number" }, { type: "string" }, { type: "bool" }] }',
                                      '{ type: "tuple" }, payload: [{ type: "number" }, { type: "number" }, { type: "string" }, { type: "bool" }] }')) # should work
    print(checkPayload(example_tuple, '{ type: "tuple" }, payload: [{ type: "number" }, { type: "number" }, { type: "string" }] }',
                                      '{ type: "tuple" }, payload: [{ type: "number" }, { type: "number" }, { type: "string" }] }')) # should fail because of length
    print(checkPayload(example_tuple, '{ type: "tuple", payload: [{ type: "number" }, { type: "bool" }, { type: "string" }, { type: "bool" }] }',
                                      '{ type: "tuple", payload: [{ type: "number" }, { type: "bool" }, { type: "string" }, { type: "bool" }] }'))# sould fail ebcause of type
    print(checkPayload(example_tuple, '{ type: "union", payload: [{ type: "number" }, { type: "string" }] }',
                                      '{ type: "union", payload: [{ type: "number" }, { type: "string" }] }')) # should fail because of type missing in components
    print(checkPayload(example_tuple, '{ type: "union", payload: [{ type: "number" }, { type: "bool" }, { type: "string" }] }',
                                      '{ type: "union", payload: [{ type: "number" }, { type: "bool" }, { type: "string" }] }')) # sould succeed
    print(checkPayload(example_def, '{ type: "def", name: { type: "string" }, payload: { type: "number" } }',
                                    '{ type: "def", name: { type: "string" }, payload: { type: "number" } }')) # basic def; usually should be in another structure