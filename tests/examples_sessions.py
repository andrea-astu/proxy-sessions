from session_logic.session_types import *
from session_logic.parsers import session_into_message

protocol_a_str = (
                'Session: Def, Name: A, Cont: Session: Choice, Dir: send, Alternatives: '
                '[(Label: Add, Session: Single, Dir: recv, Payload: { type: "number" }, Cont: '
                'Session: Single, Dir: recv, Payload: { type: "number" }, Cont: '
                'Session: Single, Dir: send, Payload: { type: "number" }, Cont: '
                'Session: Ref, Name: A), '
                '(Label: Neg, Session: Single, Dir: recv, Payload: { type: "number" }, Cont: '
                'Session: Single, Dir: send, Payload: { type: "number" }, Cont: '
                'Session: Ref, Name: A), '
                '(Label: Greeting, Session: Single, Dir: recv, Payload: { type: "string" }, Cont: '
                'Session: Single, Dir: send, Payload: { type: "string" }, Cont: '
                'Session: Ref, Name: A), '
                '(Label: Goodbye, Session: Single, Dir: send, Payload: { type: "string" }, Cont: '
                'Session: Ref, Name: A), '
                '(Label: Quit, Session: End)]'
            )

protocol_a_session = Def(
    name="A",
    cont=Choice(
        dir=Dir("send"),
        alternatives={
            Label("Add"): Single(
                dir=Dir("recv"),
                payload='{ type: "number" }',
                cont=Single(
                    dir=Dir("recv"),
                    payload='{ type: "number" }',
                    cont=Single(
                        dir=Dir("send"),
                        payload='{ type: "number" }',
                        cont=Ref("A")
                    )
                )
            ),
            Label("Neg"): Single(
                dir=Dir("recv"),
                payload='{ type: "number" }',
                cont=Single(
                    dir=Dir("send"),
                    payload='{ type: "number" }',
                    cont=Ref("A")
                )
            ),
            Label("Greeting"): Single(
                dir=Dir("recv"),
                payload='{ type: "string" }',
                cont=Single(
                    dir=Dir("send"),
                    payload='{ type: "string" }',
                    cont=Ref("A")
                )
            ),
            Label("Goodbye"): Single(
                dir=Dir("send"),
                payload='{ type: "string" }',
                cont=Ref("A")
            ),
            Label("Quit"): End()
        }
    )
)

print(session_into_message(protocol_a_session))

protocol_b_str = (
    'Session: Def, Name: B, Cont: Session: Choice, Dir: send, Alternatives: ['
    '(Label: Divide, Session: Single, Dir: recv, Payload: { type: "number" }, Cont: '
    'Session: Single, Dir: recv, Payload: { type: "number" }, Cont: '
    'Session: Single, Dir: send, Payload: { type: "number" }, Cont: '
    'Session: Ref, Name: B), '
    '(Label: List, Session: Single, Dir: recv, Payload: { type: "string" }, Cont: '
    'Session: Single, Dir: send, Payload: { type: "array", payload: { type: "number" } }, Cont: '
    'Session: Ref, Name: B), '
    '(Label: Quit, Session: End)]'
)

protocol_b_session = protocol_b = Def(
    name="B",
    cont=Choice(
        dir=Dir("send"),
        alternatives={
            Label("Divide"): Single(
                dir=Dir("recv"),
                payload='{ type: "number" }',
                cont=Single(
                    dir=Dir("recv"),
                    payload='{ type: "number" }',
                    cont=Single(
                        dir=Dir("send"),
                        payload='{ type: "number" }',
                        cont=Ref("B")
                    )
                )
            ),
            Label("List"): Single(
                dir=Dir("recv"),
                payload='{ type: "string" }',
                cont=Single(
                    dir=Dir("send"),
                    payload='{ type: "array", payload: { type: "number" } }',
                    cont=Ref("B")
                )
            ),
            Label("Quit"): End()
        }
    )
)

print(session_into_message(protocol_b_session))