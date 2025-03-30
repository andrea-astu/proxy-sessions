import json
import jsonschema

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

# dynamically create the following schemas:

# def schema
# Define a function to create a schema dynamically
def schema_def(name: str, payload_type):
    return {
        "type": "object",
        "properties": {
            name: {"type": payload_type}
        },
        "required": [name],  # Ensure the name field is required
        "additionalProperties": False  # Prevent extra fields
    }
    
    return schema


# ref schema
def schema_ref(name: str):
    return {"$ref": f"#/$defs/{name}"}

# tuple schema
schema_tuple = {

}

# missing: record schema

# --- functions for checking -----------------------------------------------------------------------------------

# any is considered any of the other types
def checkPayload(payload_sender, payload_in_ses: str, expected_payload: str) -> str | Exception:
    '''
    Compares the actual payload against the expected one.

    Args:
        payload_sender: payload that was sent (actual object)
        payload_in_ses (str): the payload type the sender is supposed to send according to the session
        expected_payload (str): is the payload type the receiver is expecting according to session

    Returns:
        A string if it worked and an exception otherwise
    '''
    if payload_in_ses != expected_payload:
        raise TypeError("The session payload types are different!")
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
            if (not ("Error!" in check_structure)): # check all elements in array are same type -> change to "try"
                # structure: { type: "array", payload: Type } where Type is what we want
                supposed_type = payload_in_ses[28:-2] # supposed to read payload type, but idk
                for a in data: # recursively check type and see if they are accepted and are the same for all
                    check_type = checkPayload(json.dumps(a), supposed_type, supposed_type)
                    if "Error!" in check_type: # change to try
                        raise TypeError("Error! Not all elements in the array have the same or expected type")
                return('Received valid payload type: { type: "array" }')
        # tuple
        # { type: "tuple", payload: Array<Type> } ; to check payload list
        #elif ('{ type: "tuple"' in payload_in_ses) or payload_in_ses == '{ type: "any" }':
            
        # union
        # { type: "union", components: Array<Type> }
        elif ('{ type: "union"' in payload_in_ses) or payload_in_ses == '{ type: "any" }':
          check_structure = try_schema(data, schema_array, payload_in_ses) # check that it IS an array
          # if try succedes
          if (not ("Error!" in check_structure)): # check all elements in array are same type -> change to try
              supposed_types = payload_in_ses[29:-3].split(", ") # gives a list of payload types
              for a in range(len(data)): # recursively check type and see if they are accepted and are the same for all # including a?
                for b in range(len(supposed_types)):
                  check_type = checkPayload(json.dumps(data[a]), supposed_types[b], supposed_types[b])
                  if ("Error!" in check_type) and (b == len(supposed_types) -1): # if already looked through all possible types for that element -> change to try
                    raise TypeError(f"Error! Union element {data[a]} is not of a valid type")
                  elif (not "Error!" in check_type): # change to try
                    break
              return ('Received valid payload type: { type: "union" }')
        # def
        elif ('{ type: "def"' in payload_in_ses) or payload_in_ses == '{ type: "any" }':
            # extract payload type with the usual format to check it in schema
            def_part, name_part, payload_type = payload_in_ses.split(", ")
            payload_type = payload_type.replace('payload: { type: "', '')
            payload_type = payload_type.replace('" } }', '')

            # checking actual_name and passing it on to the dynamic schema makes sure it's a string** 
            actual_name, actual_payload = list(data.items())[0]  # def object is like dict!

            return try_schema(data, schema_def(actual_name, payload_type), payload_in_ses)

        else:
            raise TypeError("Error! payload is not of a recognized type")


def try_schema(data, schema_to_check, expected) -> str | Exception:
    try:
        jsonschema.validate(instance=data, schema=schema_to_check)  # Validate against schema
        return(f"Valid payload type")
    except jsonschema.ValidationError:
        raise jsonschema.ValidationError(f"Invalid data type! Expected type {expected} for {data}")
    except json.JSONDecodeError:
        raise json.JSONDecodeError("Invalid JSON format!")
    
if __name__ == "__main__":
    example_def = {
    "name": 7
    }

    example_def = json.dumps(example_def)

    print(checkPayload(example_def, '{ type: "def", name: { type: "string" }, payload: { type: "number" } }',
                                    '{ type: "def", name: { type: "string" }, payload: { type: "number" } }')) # basic def; usually should be in another structure
    
    """
    # json example of ref
    example_ref = {
    "$ref": "#/$defs/Trial"
    }

    print(checkPayload(example_ref, '{ type: "ref", name: { type: "string" }',
                                    '{ type: "ref", name: { type: "string" }')) # basic ref; usually should be in another structure
    """