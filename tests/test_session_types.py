# to be able to use modules from other files
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

# for testing
import pytest

from session_logic.session_types import *

def test_label_equality():
    l1 = Label("Hello")
    l2 = Label("Hello")
    assert l1 == l2

def test_choice_add_and_lookup():
    c = Choice(dir=Dir("send"), alternatives={})
    label = Label("Test")
    session = End()
    c.add(label, session)
    
    assert c.lookup(label) == session

def test_choice_add_and_lookup_fail():
    c = Choice(dir=Dir("send"), alternatives={})
    label = Label("Test")
    session = End()
    c.add(label, session)
    
    with pytest.raises(ErrorInSessionDicts) as excinfo:
        c.lookup(Label("Smart"))
    assert "lookup" in str(excinfo.value).lower()

def test_choice_add_existing_label():
    c = Choice(dir=Dir("send"), alternatives={})
    label = Label("Test")
    session = End()
    c.add(label, session)

    with pytest.raises(ErrorInSessionDicts) as excinfo:
        c.add(label, session)
    assert "defining existing session" in str(excinfo.value).lower()

def test_global_dict_add_and_lookup():
    gdict = GlobalDict(records={})
    session = End()
    def_ses = Def(name="MyProto", cont=session)
    gdict.add(def_ses)
    
    assert gdict.lookup("MyProto") == session

def test_global_dict_duplicate_add():
    gdict = GlobalDict(records={})
    session = End()
    def_ses = Def(name="MyProto", cont=session)
    gdict.add(def_ses)

    with pytest.raises(ErrorInSessionDicts) as excinfo:
        gdict.add(def_ses)
    assert "add protcol" in str(excinfo.value).lower()

def test_global_dict_lookup_fail():
    gdict = GlobalDict(records={})

    with pytest.raises(ErrorInSessionDicts) as excinfo:
        gdict.lookup("NonExistentProto")
    assert "lookup" in str(excinfo.value).lower()

