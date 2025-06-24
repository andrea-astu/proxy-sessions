# to be able to use modules from other files
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

import websockets
import asyncio
import argparse

# in order to write sessions and convert them to or from strings
from session_logic.session_types import *
from session_logic.parsers import session_into_message, payload_to_string, message_into_session # to convert session to str

from websockets.legacy.server import WebSocketServerProtocol, serve # for websockets

# for sending/receiving with proxy + proxy error exceptions
from session_logic.helpers import *


# Server defines sessions, gives session ID and actors info to proxy
# example: flight scenario
# actors:
#   * control tower: receives READY from plane and their location, checks location is free for takeoff
#                    (by checking other planes' location status) and gives OK back to plane
#   * plane: asks for takeoff to control tower, when it's gone, receives messages from other parties to know flight can start
#   * luggage: sends ok to plane when plane has all luggage it's supposed to have
#   * passport control: sends ok to plane when all people that needed to board are in, receive info from plane
#                       when gates close and no one is allowed

# -- Define Sessions ----------------------------------------------------------------------------------------

# define kinds of payload for sessions
# strPayload = payload_to_string("string")
boolPayload = payload_to_string("bool")
numPayload = payload_to_string("number")

# sessions as session-types
planeSes = Def(
            name="Plane",
            cont=Choice(
                dir=Dir("send"),
                alternatives={ # probably should be the case that per session if you send/recv to/from actor, send/recv back should be with same one -> how to enforce this?
                    Label("Takeoff"): Single( # takeoff asks for ok and if ok it starts takeoff
                        dir=Dir("send"),
                        actor="Control Tower",
                        payload=numPayload, # Send runway from where they want to takeoff
                        cont=Single(
                            dir=Dir("recv"),
                            actor="Control Tower",
                            payload=boolPayload, # True if takeoff ok, false if not (wait)
                            cont=Ref("Plane")
                        )
                    ),
                    Label("Flying"): Single( # takeoff asks for ok and if ok it starts takeoff
                        dir=Dir("send"),
                        actor="Control Tower",
                        payload=boolPayload, # True if plane is now flying -> don't need answer
                        cont=Ref("Plane")
                    ),
                    Label("SuitcasesIn"): Single( # takeoff asks for ok and if ok it starts takeoff
                        dir=Dir("recv"),
                        actor="Cargo Control",
                        payload=boolPayload, # True if bags are now all in plane
                        cont=Ref("Plane")
                    ),
                    Label("PassengersIn"): Single( # takeoff asks for ok and if ok it starts takeoff
                        dir=Dir("recv"),
                        actor="Passport Control",
                        payload=boolPayload, # True if bags are now all in plane
                        cont=Ref("Plane")
                    ),
                    Label("Quit"): End() # -> valid? but more for proxy than for server, no? Like "disconnect"?
                }
                )
            )

controlTowerSes = Def(
            name="Control Tower",
            cont=Choice(
                dir=Dir("send"),
                alternatives={ # probably should be the case that per session if you send/recv to/from actor, send/recv back should be with same one -> how to enforce this?
                    Label("Takeoff"): Single( # takeoff asks for ok and if ok it starts takeoff
                        dir=Dir("recv"),
                        actor="Plane",
                        payload=numPayload, # True if asking for takeoff permission -> maybe not needed
                        cont=Single(
                            dir=Dir("send"),
                            actor="Plane",
                            payload=boolPayload, # True if takeoff ok, false if not -> maybe make int so it gives back number of runway
                            cont=Ref("Control Tower")
                        )
                    ),
                    Label("Flying"): Single( # takeoff asks for ok and if ok it starts takeoff
                        dir=Dir("recv"),
                        actor="Plane",
                        payload=boolPayload, # True if plane is now flying -> don't need answer
                        cont=Ref("Control Tower")
                    ),
                    Label("Quit"): End()
                }
                )
            )

cargoControlSes = Def(
            name="Cargo Control",
            cont=Choice(
                dir=Dir("send"),
                alternatives={ # probably should be the case that per session if you send/recv to/from actor, send/recv back should be with same one -> how to enforce this?
                    Label("SuitcasesIn"): Single( # takeoff asks for ok and if ok it starts takeoff
                        dir=Dir("send"),
                        actor="Plane",
                        payload=boolPayload, # True if bags are now all in plane
                        cont=Ref("Cargo Control")
                    ),
                    Label("Quit"): End()
                }
                )
            )


passportControlSes = Def(
            name="Passport Control",
            cont=Choice(
                dir=Dir("send"),
                alternatives={ # probably should be the case that per session if you send/recv to/from actor, send/recv back should be with same one -> how to enforce this?
                    Label("PassengersIn"): Single( # takeoff asks for ok and if ok it starts takeoff
                        dir=Dir("send"),
                        actor="Plane",
                        payload=boolPayload, # True if all passengers are in plane
                        cont=Ref("Passport Control")
                    ),
                    Label("Quit"): End()
                }
                )
            )

# sessions as strings
planeSes_str = session_into_message(planeSes)
controlTowerSes_str = session_into_message(controlTowerSes)
cargoControlSes_str = session_into_message(cargoControlSes)
passportControlSes_str = session_into_message(passportControlSes)


# -- Proxy interactions -----------------------------------------------------------------------------------------------

async def ws_server(websocket:WebSocketServerProtocol):
    '''
    Main function of server where protocols are defined and information is sent back and forth.

    Args:
        websocket: Server's websocket (will receive and send information) provided by websockets.serve function.
    '''
    try:
        # send protocols to proxy
        print("Sending protocols to proxy...")
        await send(websocket, planeSes_str)
        await send(websocket, controlTowerSes_str)
        await send(websocket, cargoControlSes_str)
        await send(websocket, passportControlSes_str)
        await send(websocket, "Session: End") # signals we are done sending protocols
        print("Protcols sent.")

    # handle ok and unexpected connections and errors -> check which is ok end of connection :)
    except ProxyError as e:
        print(e)
    except websockets.exceptions.ConnectionClosed:
        print(f"Connection lost, most likely due to a timeout")
    except websockets.ConnectionClosedOK:
        print("Connection finished.")
    except websockets.ConnectionClosedError:
        print("Error: Connection lost unexpectedly.")
    except Exception as e:
        print(f"Unexpected error {e}")
    finally:
        await websocket.close()

# -- [Description] -----------------------------------------------------------------------------------------
async def main(port:int):
    '''
    Creates a WebSocket server that listens on localhost:7890.
    Whenever a client connects to the server, websockets.serve automatically calls ws_server, 
    passing in a new websocket object (which represents the connection with that client).

    Args:
        port: The port from which server is reachable.
    '''
    print(f"Using port {port}")
    async with serve(ws_server, "localhost", port): # the port can be changed depending on preference
        await asyncio.Future()  # run forever because servers must always be active
 
if __name__ == "__main__":
    # take port as flag
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--port", default = "7890", help="Port number")
    args = parser.parse_args()

    # start code
    print("Server started ...")
    asyncio.run(main(args.port))



