import pytest
from flask_dance.utils import FakeCache, first, getattrd

def test_first():
    assert first([1, 2, 3]) == 1
    assert first([None, 2, 3]) == 2
    assert first([None, 0, False, [], {}]) == None
    assert first([None, 0, False, [], {}], default=42) == 42
    first([1, 1, 3, 4, 5], key=lambda x: x % 2 == 0) == 4

class C(object):
    d = "foo"

class B(object):
    C = C

class A(object):
    B = B

def test_getattrd():
    assert A.B.C.d == "foo"
    assert getattrd(A, "B.C.d") == "foo"
    assert getattrd(A, "B") == B
    assert getattrd(A, "B", default=42) == B
    assert getattrd(A, "Q", default=42) == 42
    with pytest.raises(AttributeError):
        assert getattrd(A, "Q")
