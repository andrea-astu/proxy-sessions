import json
import jsonschema

# ---------------- define schemas -------------------------------------------------------------------
# num schema
schema_num = {
"type": "number"
}

# string schema
schema_str = {
"type": "string"
}

# string schema
schema_bool = {
"type": "bool"
}

# string schema
schema_null = {
"type": "null"
}

# payload_sender is payload that was sent (actual object)
# payload_in_ses is the payload type the sender is supposed to send according to session
# expected_payload is the payload type the receiver is expecting according to session
def checkPayload(payload_sender, payload_in_ses, expected_payload):
    if payload_in_ses != expected_payload:
        print("Error! The session payload types are different!")
    else:
        data = json.loads(payload_sender) # Convert JSON string to Python data
        if payload_in_ses == "number" or payload_in_ses == "any": 
            try:
                jsonschema.validate(instance=data, schema=schema_num)  # Validate against schema
                print(f"Received valid number: {data}")
            except jsonschema.ValidationError:
                print("Error:!Invalid data type! Expected a number.")
            except json.JSONDecodeError:
                print("Error! Invalid JSON format!")
        elif payload_in_ses == "string" or payload_in_ses == "any":
            try:
                jsonschema.validate(instance=data, schema=schema_str)  # Validate against schema
                print(f"Received valid string: {data}")
            except jsonschema.ValidationError:
                print("Error! Invalid data type! Expected a string.")
            except json.JSONDecodeError:
                print("Error! Invalid JSON format!")
        else:
            print("Error! payload is not of a recognized type")


