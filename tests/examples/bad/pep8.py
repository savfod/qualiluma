from math import *

MyVariable = "hello"
ANOTHER_var = "world"


def normalFunction(a, b, c, d, e, f):
    x = 0
    if a > b:
        x = a + b
    else:
        x = b - a
    return x


class myclass:
    def __init__(self, value):
        self.Value = value

    def getValue(self):
        return self.Value

    def setValue(self, newValue):
        self.Value = newValue


normal_variable = "This is some text, i don't know about what, but it exists and it's existance makes it valuable"


def normal_function(param):
    """
    This is a function.
    """
    return param * 2
