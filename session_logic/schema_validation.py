import json
import jsonschema
import re # to parse payload types for tuple and union
from typing import Any, Dict

# ---------------- define json schemas ----------------------------------------------------------------
# these schemas are like the "templates" the payload types are compared against

# define type of a JSON Schema
JsonSchema = Dict[str, Any]

# num schema
schema_number:JsonSchema = {
"type": "number"
}

# string schema
schema_string:JsonSchema = {"type": "string"}

# bool schema
schema_bool:JsonSchema = {
"type": "boolean"
}

# null schema
schema_null:JsonSchema = {
"type": "null"
}

# any schema
schema_any:JsonSchema = {
    "oneOf": [
        {"type": "null"},
        {"type": "string"},
        {"type": "boolean"},
        {"type": "number"},
        {"type": "array"}
    ]
}

# dynamically create the following schemas:

# def schema
def schema_def(name: str, payload_type:str) -> JsonSchema:
    '''
    Function that returns a JSONSchema based on a a payload of type def.

        Args:
            name (str): how it will be defined
            payload_type (str): payload that comes with definition

        Returns:
            A JSON schema that matches payload type def.
    '''
    return {
        "type": "object",
        "properties": {
            name: {"type": payload_type}
        },
        "required": [name],  # Ensure the name field is required
        "additionalProperties": False  # Prevent extra fields
    }

# array schema
def schema_array(type_array:str) -> JsonSchema:
   '''
    Function that returns a JSONSchema based on a a payload of type array.
    An array has a variable length but all elements should be of same type.

        Args:
            type_array (str): str to define type of payload inside array so it can later be checked by a schema.

        Returns:
            A JSON schema that matches payload type array.
    '''
   return {
        "type": "array",
        "items": {"type": type_array}
    }

# tuple schema
def schema_tuple(type_list: list[str], supposed_length: int) -> JsonSchema:
    '''
    Function that returns a JSONSchema based on a a payload of type tuple.
    A tuple is of a fixed length but its elements can be of different types

        Args:
            type_list (list[str]): list (in order) of what type ach element in tuple is.
            suppsoed_length (int): fixed length of tuple

        Returns:
            A JSON schema that matches payload type tuple.
    '''
    return {
        "type": "array",
        "prefixItems": [{"type": t} for t in type_list],  # should be at the top level
        "minItems": supposed_length,
        "maxItems": supposed_length
    }

# union schema
def schema_union(type_array:list[str]) -> JsonSchema:
    '''
    Function that returns a JSONSchema based on a a payload of type union.
    A union is an array but it's elements can be of any type listed beforehand.

        Args:
            type_array (list[str]): all possible types of elements in union.

        Returns:
            A JSON schema that matches payload type union.
    '''
    return {
        "type": "array",
        "items": {
            "oneOf": [{"type": t} for t in type_array]  # Each item can be one of these types
        }
    }

# record schema
def schema_record(field_names: list[str], type_list: list[str]) -> JsonSchema:
    '''
    Function that returns a JSONSchema based on a a payload of type record.
    A record is kind of like a python dictionary that keeps payloads and gives them a name as "key".

        Args:
            field_names (list[str]): names of each element in dictionary, in order
            type_list (list[str]): payload type of each element in dictionary, in order

        Returns:
            A JSON schema that matches payload type record.
    '''
    return {
        "type": "object",
        "properties": {
            field: {"type": type_list[i]}  # Match field to type by order
            for i, field in enumerate(field_names)
        },
        "required": field_names,  # All fields are required
        "additionalProperties": False  # No extra fields allowed
    }

# --- functions for checking -----------------------------------------------------------------------------------

# any is considered any of the other types
def checkPayload(payload_sender:Any, payload_in_ses: str, expected_payload: str) -> str | Exception:
    '''
    Checks the actual payload is of the type expected by both the server and the client.

    Args:
        payload_sender (Any): payload that was sent (actual object); it can be anything as a JSON object
        payload_in_ses (str): the payload type the sender is supposed to send according to the session
        expected_payload (str): is the payload type the receiver is expecting according to session

    Returns:
        A string if it worked and an exception otherwise
    '''
    if payload_in_ses != expected_payload:
        raise TypeError("The session payload types are different!")
    else:
        data = json.loads(payload_sender) # Convert JSON string to Python data
        if payload_in_ses == '{ type: "any" }': 
            return try_schema(data, schema_any, payload_in_ses)
        if payload_in_ses == '{ type: "number" }': 
            return try_schema(data, schema_number, payload_in_ses)
        elif payload_in_ses == '{ type: "string" }':
            return try_schema(data, schema_string, payload_in_ses)
        elif payload_in_ses == '{ type: "null" }':
            return try_schema(data, schema_null, payload_in_ses)
        elif payload_in_ses == '{ type: "bool" }':
            return try_schema(data, schema_bool, payload_in_ses)
        # array
        elif ('{ type: "array"' in payload_in_ses):
            type = extract_types(payload_in_ses[26:-2])[0] # get the type in array according to session description
            return try_schema(data, schema_array(type), payload_in_ses) # create array schema dynamically
        # tuple
        elif ('{ type: "tuple"' in payload_in_ses):
            types = extract_types(payload_in_ses[26:].replace("[", "").replace("]", "")) # get the types in array according to session description
            supposed_length = len(types) # how many items there should be in tuple
            return try_schema(data, schema_tuple(types, supposed_length), payload_in_ses) # create tuple schema dynamically
        # union
        elif ('{ type: "union"' in payload_in_ses):
            types = extract_types(payload_in_ses[26:].replace("[", "").replace("]", "")) # get the types in array according to session description
            return try_schema(data, schema_union(types), payload_in_ses) # create union schema dynamically
        # def
        elif ('{ type: "def"' in payload_in_ses):
            # extract payload type with the usual format to check it in schema
            payload_type = payload_in_ses.split(", ")[2]
            payload_type = payload_type.replace('payload: { type: "', '')
            payload_type = payload_type.replace('" } }', '')

            # checking actual_name and passing it on to the dynamic schema
            actual_name = list(data.items())[0][0]  # def object is like dict!

            return try_schema(data, schema_def(actual_name, payload_type), payload_in_ses)
        # record
        elif ('{ type: "record"' in payload_in_ses):
            field_names = list(data.keys())  # Extracts keys in order
            types = extract_types(payload_in_ses[27:].replace("[", "").replace("]", "")) # get the types in record according to session description
            return try_schema(data, schema_record(field_names, types), payload_in_ses) # create union schema dynamically
        else:
            raise TypeError("Error! payload is not of a recognized type")

def try_schema(data: Any, schema_to_check: JsonSchema, expected: str) -> str | Exception:
    '''
    Compares the payload against a json schema to see if it matches it's supposed type.

    Args:
        data: actual payload to be checked
        schema_to_check: json schema of the payload type; one of the ones defined at the start of the code
        expected: name of the expected type of payload

    Returns:
        A string if it worked and a json schema exception otherwise
    '''
    try:
        jsonschema.validate(instance=data, schema=schema_to_check)  # Validate against schema
        return(f"Valid payload type")
    except jsonschema.ValidationError:
        raise jsonschema.ValidationError(f"Invalid data type! Expected type {expected} for {data}")
    except json.JSONDecodeError:
        raise ValueError("Invalid JSON format!")
    
# -- helper functions ---------------------------------------------------------------------------------
def extract_types(payload_str:str) -> list[str]:
    '''
    Parses the string that describes a session of type tuple in order to extract the types of the tuple elements.

    Args:
        tuple_types (str): string of tuple session

    Returns:
        A list of JSON types as strings.
    '''
    # Extract types inside payload
    type_pattern = r'\{ type:\s*"(\w+)" \}'
    types = re.findall(type_pattern, payload_str)

    # Replace "bool" with "boolean"
    types = ["boolean" if t == "bool" else t for t in types]

    return types