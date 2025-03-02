import json
import jsonschema
# combines schemas and manual checking to see if it is payload type


# ---------------- define schemas -------------------------------------------------------------------
# num schema
schema_num = {
"type": "number"
}

# string schema
schema_str = {
"type": "string"
}

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
"type:" "array"
}


# payload_sender is payload that was sent (actual object)
# payload_in_ses is the payload type the sender is supposed to send according to session
# expected_payload is the payload type the receiver is expecting according to session
# any is considered any of the other types
def checkPayload(payload_sender, payload_in_ses, expected_payload) -> str:
    if payload_in_ses != expected_payload:
        print("Error! The session payload types are different!")
    else:
        data = json.loads(payload_sender) # Convert JSON string to Python data
        if payload_in_ses == "number" or payload_in_ses == "any": 
            return try_schema(data, schema_num, payload_in_ses)
        elif payload_in_ses == "string" or payload_in_ses == "any":
            return try_schema(data, schema_str, payload_in_ses)
        elif payload_in_ses == "null" or payload_in_ses == "any":
            return try_schema(data, schema_null)
        elif payload_in_ses == "bool" or payload_in_ses == "any":
            return try_schema(data, schema_bool, payload_in_ses)
        elif payload_in_ses == "array" or payload_in_ses == "any":
            check_structure = try_schema(data, schema_array)
            # if try succedes
            if (not check_structure.contains("Error!")) and (all(type(x) == type(data[0]) for x in data)): # check all elements in array are same type
                return(f"Received valid payload: {data}")
            else:
                return("Error! Not all elements in the array have the same type")
        # for tuple we don't have to check all elements are same but idk how to check for fixed length
        elif payload_in_ses == "tuple" or payload_in_ses == "any":
            try_schema(data, schema_array)
        # union means it could be any of the types mentioned in components
        elif payload_in_ses.contains("union") or payload_in_ses == "any":
            components = payload_in_ses[7:-1].split(", ") # still to do: check union is written correctly in session
            print(f"components list elements: {components}") # DEBUG
            for a in components:
                try_type = try_schema(data, a)
                if not try_type.contains("Error!"):
                    return try_type
            # this only happens if none match
            return ("Error! No expected types match given type in a union")

        else:
            return("Error! payload is not of a recognized type")


def try_schema(data, schema_to_check, expected) -> str:
    try:
        jsonschema.validate(instance=data, schema=schema_to_check)  # Validate against schema
        return(f"Received valid payload: {data}")
    except jsonschema.ValidationError:
        return(f"Error:!Invalid data type! Expected type {expected}")
    except json.JSONDecodeError:
        return("Error! Invalid JSON format!")





# specific syntax
# type "union" can be specified in session as for example "Payload: union [number, string]""
# type "record "