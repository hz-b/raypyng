import numpy as np # needed for params3 generation, not for the internal processing
import math

from collections.abc import Iterable

# Example:
# In [5]: convert_params(params3)
# Out[5]: 
# [{'grazingIncAngle': 2,
#   'longRadius': 180,
#   'photonEnergy': 2000,
#   'exitArmLengthMer': 19500,
#   'exitArmLengthSag': 100},
#  {'grazingIncAngle': 2,
#   'longRadius': 180,
#   'photonEnergy': 2000,
#   'exitArmLengthMer': 19500,
#   'exitArmLengthSag': 100},
#  {'grazingIncAngle': 2,
#   'longRadius': 180,
#   'photonEnergy': 2000,
#   'exitArmLengthMer': 19500,
#   'exitArmLengthSag': 100},
#  {'grazingIncAngle': 2,
#   'longRadius': 180,
#   'photonEnergy': 2000,
#   'exitArmLengthMer': 19500,
#   'exitArmLengthSag': 100}]


params3 = [  
            # set two parameters: "alpha" and "beta" in a dependent way. 
            {'grazingIncAngle':np.array([1,2]), 'longRadius':[100,180], 'photonEnergy':[1000,2000]}, 
            # set a range of  values - in independed way
            {'exitArmLengthMer':range(19400,19501, 100)},
            # set a value - in independed way
            {'exitArmLengthSag':[100]}
        ]

def convert_params(p):
    return LLD2LD(LDL2LLD(p))

def LLD2LD(lld):
    """Convert list of lists of dictionaries into list of dictionaries

    Args:
        lld (_type_): _description_

    Returns:
        _type_: _description_
    """

    # this is explanation for the one-liner code below:
    # sizes = [s for s in map(len, lld)] # create list of sizes of dictinaries
    # final_size = math.prod(sizes) # final size of a product of those values
    # out_ld = [{} for i in range(final_size)] # create list of empty dict with final_size elements

    # prepare list of dicts
    out_ld = [{} for i in range(math.prod(map(len, lld)))]
    # populate dictionaries
    for ld in lld:
        for out_ld_d in out_ld:
            for d in ld:
                for k,v in d.items():
                    out_ld_d[k]=v
    return  out_ld

def LDL2LLD(ldl):
    """convert list of dicts of lists to list of lists of dicts

    Args:
        ldl (_type_): input list of dicts of lists

    Returns:
        _type_: _description_
    """
    #final = [DL2LD(a_dict) for a_dict in ldl]
    return [DL2LD(a_dict) for a_dict in ldl]

# based on the code from  here: https://stackoverflow.com/questions/5558418/list-of-dicts-to-from-dict-of-lists
def DL2LD(dl) :
    """
    convert dict of lists to list of dicts
    """
    if not dl: return []
    # prepare resulting output list of dicts based on longest input
    result = [{} for i in range(max(map(xlen, dl.values())))]
    #fill each dict, one key at a time
    for key, list_or_value in dl.items(): # iterate over input dict
        if isinstance(list_or_value,Iterable): 
            for out_dict,current_value in zip(result, list_or_value) :  # iterate over output dictinaries in parallel
                out_dict[key] = current_value
        else:
            for out_dict in result:  # iterate over output dictinaries in parallel
                out_dict[key] = list_or_value
    return result

def xlen(x):
    """return number of elements in sequence or 1

    Args:
        x (Any): any value

    Returns:
        int: number of elements
    """
    return len(x) if isinstance(x,Iterable) else 1


# examples for the coding:

dl = {'key1':[1,2], 'key2': [3,4]}
dlv2 = {'key1':[1,2], 'key2': [3,4], 'key3':5}