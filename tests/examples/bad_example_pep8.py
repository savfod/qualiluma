# This code intentionally violates PEP 8 guidelines

import json
import os  # Multiple imports on one line (violation)
import sys
from math import *  # Wildcard import (violation)

# Poor variable naming (violations)
x = 5  # No spaces around operator
Y = 10  # Inconsistent spacing
MyVariable = "hello"  # CamelCase for variable (should be snake_case)
ANOTHER_var = "world"  # Mixed case styles


def badFunction(a, b, c, d, e, f):  # Poor function name, too many parameters
    if a > b:
        x = a + b  # Multiple statements, no spaces around operators
    else:
        x = b - a  # Excessive spacing
    return x


class myclass:  # Class name should be PascalCase
    def __init__(self, value):
        self.Value = value  # Attribute should be lowercase

    def getValue(self):  # Method should be snake_case
        return self.Value

    def setValue(self, newValue):
        self.Value = newValue


# Lines too long (over 79 characters)
very_long_line = "This is an extremely long line that definitely exceeds the PEP 8 recommended maximum line length of 79 characters and should be broken up"

# Poor spacing and formatting
result = badFunction(1, 2, 3, 4, 5, 6)
my_list = [1, 2, 3, 4, 5]  # No spaces after commas
my_dict = {"key1": "value1", "key2": "value2"}  # No spaces in dictionary


# Trailing whitespace and blank lines issues
def another_function():
    pass


# Mixed indentation (tabs and spaces - this would cause actual Python errors)
# Using inconsistent indentation
if True:
    print("Inconsistent indentation")
if False:
    print("Different indentation level")

# Comments not following PEP 8
x = 5  # inline comment without spaces
# comment without proper capitalization and ending period


# No space after hash
def poorly_documented_function(param):
    """
    This docstring doesn't follow PEP 257 either
    """
    return param * 2  # No spaces around operator
