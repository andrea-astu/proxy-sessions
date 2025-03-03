import json
import jsonschema
# combines schemas and manual checking to see if it is payload type


# ---------------- define schemas -------------------------------------------------------------------
# num schema
schema_number = {
"type": "number"
}

# string schema
schema_string = {"type": "string"}

# bool schema
schema_bool = {
"type": "boolean"
}

# null schema
schema_null = {
"type": "null"
}

# array schema
schema_array = {
"type": "array"
}

# it works with [True, ]
interesting_schema = {
  "type": "array",
  "prefixItems": [
    { "type": "boolean" },
    { "type": "string" },
    { "type": "boolean" }
  ],
  "items": { "type": "integer" }
}



# version one

# payload_sender is payload that was sent (actual object)
# payload_in_ses is the payload type the sender is supposed to send according to session
# expected_payload is the payload type the receiver is expecting according to session
# any is considered any of the other types
def checkPayload(payload_sender, payload_in_ses, expected_payload) -> str:
    if payload_in_ses != expected_payload:
        return("Error! The session payload types are different!")
    else:
        data = json.loads(payload_sender) # Convert JSON string to Python data
        if payload_in_ses == '{ type: "number" }' or payload_in_ses == '{ type: "any" }': 
            return try_schema(data, schema_number, payload_in_ses)
        elif payload_in_ses == '{ type: "string" }' or payload_in_ses == '{ type: "any" }':
            return try_schema(data, schema_string, payload_in_ses)
        elif payload_in_ses == '{ type: "null" }' or payload_in_ses == '{ type: "any" }':
            return try_schema(data, schema_null, payload_in_ses)
        elif payload_in_ses == '{ type: "bool" }' or payload_in_ses == '{ type: "any" }':
            return try_schema(data, schema_bool, payload_in_ses)
        # array
        elif ('{ type: "array"' in payload_in_ses) or payload_in_ses == '{ type: "any" }':
            check_structure = try_schema(data, schema_array, payload_in_ses) # check that it IS an array
            # if try succedes
            if (not ("Error!" in check_structure)): # check all elements in array are same type
                # structure: { type: "array", payload: Type } where Type is what we want ->
                supposed_type = payload_in_ses[28:-2] # supposed to read payload type, but idk
                for a in data: # recursively check type and see if they are accepted and are the same for all
                    check_type = checkPayload(json.dumps(a), supposed_type, supposed_type)
                    if "Error!" in check_type:
                        return ("Error! Not all elements in the array have the same or expected type")
                return('Received valid payload type: { type: "array" }')
        # tuple
        # { type: "tuple", payload: Array<Type> } ; so check payload list
        elif ('{ type: "tuple"' in payload_in_ses) or payload_in_ses == '{ type: "any" }':
            check_structure = try_schema(data, schema_array, payload_in_ses) # check that it IS an array
            # if try succedes
            if (not ("Error!" in check_structure)): # check all elements in array are same type
                supposed_types = payload_in_ses[29:-3].split(", ") # gives a list of payload types
                if (len(supposed_types) != len(data)): return "Error! The list is not of the given fixed length"
                for a in range (0, (len(data) - 1)): # recursively check type and see if they are accepted and are the same for all # including a?
                  check_type = checkPayload(json.dumps(data[a]), supposed_types[a], supposed_types[a])
                  if "Error!" in check_type:
                      return (f"Error! Tuple element {a} does not correspond to the given type")
                return('Received valid payload type: { type: "tuple" }')
        # union
        # { type: "union", components: Array<Type> } |
        elif ('{ type: "union"' in payload_in_ses) or payload_in_ses == '{ type: "any" }':
          check_structure = try_schema(data, schema_array, payload_in_ses) # check that it IS an array
          # if try succedes
          if (not ("Error!" in check_structure)): # check all elements in array are same type
              supposed_types = payload_in_ses[29:-3].split(", ") # gives a list of payload types
              for a in range(len(data)): # recursively check type and see if they are accepted and are the same for all # including a?
                for b in range(len(supposed_types)):
                  check_type = checkPayload(json.dumps(data[a]), supposed_types[b], supposed_types[b])
                  if ("Error!" in check_type) and (b == len(supposed_types) -1): # if already looked through all possible types for that element
                    return (f"Error! Union element {data[a]} is not of a valid type")
                  elif (not "Error!" in check_type):
                    break
              return ('Received valid payload type: { type: "union" }')

        else:
            return("Error! payload is not of a recognized type")



def try_schema(data, schema_to_check, expected) -> str:
    try:
        jsonschema.validate(instance=data, schema=schema_to_check)  # Validate against schema
        return(f"Received valid payload type: {expected}")
    except jsonschema.ValidationError:
        return(f"Error! Invalid data type! Expected type {expected} for {data}")
    except json.JSONDecodeError:
        return("Error! Invalid JSON format!")

    

# specific syntax
# type "union" can be specified in session as for example "Payload: union [number, string]""
# type "record "


# version 2

general_schema = {
  # "$schema": "http://json-schema.org/draft-07/schema#",
  # "title": "Type Validation Schema",
  "oneOf": [
    { "type": "any", "properties": { "type": { "const": "any" } }, "required": ["type"] },
    { "type": "number", "properties": { "type": { "const": "number" } }, "required": ["type"] },
    { "type": "string", "properties": { "type": { "const": "string" } }, "required": ["type"] },
    { "type": "bool", "properties": { "type": { "const": "bool" } }, "required": ["type"] },
    { "type": "null", "properties": { "type": { "const": "null" } }, "required": ["type"] },
    { 
      "type": "object",
      "properties": {
        "type": { "const": "union" },
        "components": { 
          "type": "array",
          "items": { "$ref": "#" },
          "minItems": 1
        }
      },
      "required": ["type", "components"]
    },
    { 
      "type": "object",
      "properties": {
        "type": { "const": "record" },
        "payload": { 
          "type": "object",
          "additionalProperties": { "$ref": "#" }
        },
        "name": { "type": "string" }
      },
      "required": ["type", "payload"]
    },
    { 
      "type": "object",
      "properties": {
        "type": { "const": "ref" },
        "name": { "type": "string" }
      },
      "required": ["type", "name"]
    },
    { 
      "type": "object",
      "properties": {
        "type": { "const": "tuple" },
        "payload": { 
          "type": "array",
          "items": { "$ref": "#" },
          "minItems": 1
        }
      },
      "required": ["type", "payload"]
    },
    { 
      "type": "object",
      "properties": {
        "type": { "const": "array" },
        "payload": { "$ref": "#" }
      },
      "required": ["type", "payload"]
    }
  ]
}

basic_types_joined = {
    "oneOf": [
    { "type": "string" },
    { "type": "boolean" },
    { "type": "null" },
    { "type": "number" }
    ]
}
    

if __name__ == "__main__":
    example_string = json.dumps("hello")
    example_bool = json.dumps(True)
    example_null = json.dumps(None) # None is supposed to be null but we'll see
    example_number = json.dumps(42)
    example_array1 = json.dumps([1, 2, 3]) # should be ok
    example_array2 = json.dumps(["a", 5, True]) # should give error
    example_tuple = json.dumps([1, 2, "and", False])
    # print(try_schema(json.loads(example_string), basic_types_joined, "string"))
    # example_array = json.dumps([True, "a", False])
    # print(try_schema(json.loads(example_array), interesting_schema, "array"))
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
    print(checkPayload(example_tuple, '{ type: "tuple" }, payload: [{ type: "number" }, { type: "bool" }, { type: "string" }, { type: "bool" }] }',
                                      '{ type: "tuple" }, payload: [{ type: "number" }, { type: "bool" }, { type: "string" }, { type: "bool" }] }'))# sould fail ebcause of type
    print(checkPayload(example_tuple, '{ type: "union" }, payload: [{ type: "number" }, { type: "string" }] }',
                                      '{ type: "union" }, payload: [{ type: "number" }, { type: "string" }] }')) # should fail because of type missing in components
    print(checkPayload(example_tuple, '{ type: "union" }, payload: [{ type: "number" }, { type: "bool" }, { type: "string" }] }',
                                      '{ type: "union" }, payload: [{ type: "number" }, { type: "bool" }, { type: "string" }] }')) # sould succeed