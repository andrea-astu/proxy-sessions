# A proxy for session-typed communication.

## Files and folders:
- **proxy_with_middle:** python code with all proxy functionalities
- **example_server and example_client in example_client_server folder:** to try out the proxy with previously created client and server
- **schema_validation in session logic:** python code that checks the json payload the client/server sends and compares it with type defined in client and server protocols
- **session_types in session_logic:** models the Session types and their functionalities as well as exceptions.
- **parsers in session_logic:** to transform a session into a string or vice-versa and to alter message sent from server to client or client to server.
- **tests:** all files in this folder can be carried out with pytest to make sure certain functions are working as they should.

## How to use
1. Start your server.
2. **Start proxy**  
    Open a command prompt in the project folder and run

   ```
   python proxy.py -s=SERVER_PORT -pr=PROXY_PORT
   ```
   
   and replace SERVER_PORT and PROXY_PORT with the desired port numbers.
4. Start your client and make sure it's connecting to the given proxy port.
5. Should your client code end, you can keep the server and proxy open and connect a new client; just keep in mind the server and proxy ports will remain the same.

Note: you can also run the proxy without flags and the default ports will be used, which are 7890 for a server and 7891 for the proxy.

## Use example to test out proxy
1. **Start server**  
   Open a command prompt in the example_client_server folder and run
   
   ```
   python example_server.py
   ```
   
3. **Start proxy**  
    Open a command prompt in the project folder and run
   
   ```
   python proxy.py
   ```
   
5. **Start client**  
   Open a command prompt in the example_client_server folder and run
    ```
   python example_client.py
    ```

7. Follow the client instructions in the console.
8. Once the client code is finished, you can repeat step 3 to carry it put again without closing the server or proxy if you so wish.

**NOTE:** you can see what proxy and server are handling by looking at the corresponding terminals.

## Session syntax and payloads


### Payload types descriptions examples

Payload descriptions in sessions always start with '{ type:'  and end with ' }'. Some payload types have more information in their descriptions, such as the payload types they contain (in case they are an array, tuple or union). Make sure to respect the spaces between words in order to get the right syntax.

**Booleans**: '{ type: "bool" }'

**String**: '{ type: "string" }'

**None**: '{ type: "null" }'

**Number**: '{ type: "number" }'

**Array** (can have any length but elements may only be of one payload type):  
'{ type: "array", payload: { type: "number" } }'  
*(the example payload here is number, but it accepts other payload types, such as bool, string, etc.)*

**Tuple** (elements may be of different payload types, has a fixed length):  
'{ type: "tuple", payload: [{ type: "number" }, { type: "number" }, { type: "string" }] }'  
*(payload is a list that describes the type of each element in tuple)*  

**Union** (an array of any length; its elements can be of any type described in the payload list):  
'{ type: "union", payload: [{ type: "number" }, { type: "bool" }, { type: "string" }] }'

**Def** (gives a payload and its name):  
'{ type: "def", name: { type: "string" }, payload: { type: "number" } }'  
*the name type must always be a string*

**Record** (the equivalent to a python dictionary):  
'{ type: "record", payload: [{ type: "number" }, { type: "string" }, { type: "bool" }] }'  
*payload describes the payload types of the dictionary elements*

For more examples and counterexamples, see the example_schema_validation file.

### Session types and examples

The elements in [] describe the required information to create the session. Def sessions are used to describe protocols. Choice sessions are used to describe possible actions in these protocols. All sessions start with the keyword "Session:":

**Single** [Session, Dir, Payload, Cont] (describes a message sent(*send*) or received(*recv*)):  
'Session: Single, Dir: recv, Payload: { type: "number" }, Cont:...'  
*(Cont describes the session that happens after this one)*  

**Choice** [Session, Dir, Alternatives] (like a dictionary to define possible sessions to be chosen, which are described in "alternatives"):  
'Session: Choice, Dir: recv, Alternatives: [(Label: Add, Session: Single, Dir: send, Payload: { type: "number" }, Cont: Session: Single, Dir: send, Payload: { type: "number" }, Cont: ...'  

**Def** (define a session) [Session, Name, Cont]:  
'Session: Def, Name: A, Cont: ...'  
*(Cont describes the session that happens after this one)* 

**Ref** (references a session, usually a Def one) [Session, Name]: 'Session: Ref, Name: A'

**End** (indicates the end of a session) [Session]: 'Session: End'

**Example of their use when defining a session:**  
'Session: Def, Name: A, Cont: Session: Choice, Dir: recv, Alternatives: [(Label: Add, Session: Single, Dir: send, Payload: { type: "number" }, Cont: Session: Single, Dir: send, Payload: { type: "number" }, Cont: Session: Single, Dir: recv, Payload: { type: "number" }, Cont: Session: Ref, Name: A), (Label: Neg, Session: Single, Dir: send, Payload: { type: "number" }, Cont: Session: Single, Dir: recv, Payload: { type: "number" }, Cont: Session: Ref, Name: A), (Label: Quit, Session: End)]'


The client and server sessions have to be mirrored if they are describing the same protocol (Def session); with mirrored Single sessions, the client has to receive and the server sends, or viceversa, but both can't have the same direction at the same time.

For more examples, see the server and client example codes to see how sessions are described, specially as the *cont* parts were not included in some of these examples to make them mor readable.


## Parser

In session_logic/parsers.py, there are two empty functions that can alter the payload sent from server to client (server_parser_func) and from client to server (client_parser_func). Feel free to write some code inside these functions if you want the proxy to regulate the messages sent between client and server.

**Note**: the functions accept a parameter ("message") that represents the payload; make sure they return the same type of payload as the received message.
