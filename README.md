# A proxy for session-typed communication.

*Summary here*

## Files

- **proxy_with_middle:** python code with all proxy functionalities
- **example_server and example_client**
- **schema_validation:** python code that checks the json payload the client/server sends and compares it with type defined in client and server protocols
- **example_schema_validation:** tests that show examples of sessions against python payloads changed to JSON formats


## Use example to test out proxy

1. First open the server, then the proxy.

2. In the proxy terminal, type "default" if you want to use the default ports for the proxy (7891) and the server (7890, which is translated into the ws://127.0.0.1:7890 URI). If not, type the desired ports/uris for them.

3. Open the client.

4. The example server and client will run through the proxy. Interact with the client to test it out.

Note: you can see what proxy and server are handling by looking at the corresponding terminals.

## Session syntax and payloads

For more ..., see the example_schema_validation examples for sessions.

## Notes

In proxy_with_middle, there are two functions that ..., namely ... You can write the function inside its definition so the proxy will change the message. Note: the changed payload has to be of the same type.
