""" Useful functions """

import numpy as np

def matprint(mat, fmt="g"):
    """
    Pretty print a matrix.
    """

    col_maxes = [max([len(("{:"+fmt+"}").format(x)) for x in col]) for col in mat.T]
    for x in mat:
        for i, y in enumerate(x):
            print(("{:"+str(col_maxes[i])+fmt+"}").format(y), end="  ")
        print("")

def str_to_bool(string, true_options=("yes", "y", "true"),
                false_options=("no",  "n", "false")):
    """
    Convert string to bool
    parameters
    ----------
    string : str or bool
        string to convert to bool (case insensitive)
    true_options : [str]
        (lowercase) strings which evaluate to True
    false_options : [str]
        (lowercase) strings which evaluate to False
    """
    if str(string).lower() in true_options:
        return True
    elif str(string).lower() in false_options:
        return False
    else:
        raise Exception(f'Undefined string for boolean conversion: {string}')

def printv(string, verbose, **kwargs):
    """
    Print string if verbose is True
    parameters
    ----------
    string : str
    verbose : bool
    """
    if verbose:
        print(string, **kwargs)