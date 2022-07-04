import numpy as np # needed for params3 generation, not for the internal processing
import math

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
            {'grazingIncAngle':[1,2], 'longRadius':[100,180], 'photonEnergy':[1000,2000]}, 
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

def LDL2LLD(l):
    """convert list of dicts of lists to list of lists of dicts

    Args:
        l (_type_): _description_

    Returns:
        _type_: _description_
    """
    final = [DL2LD(d) for d in l]
    return final



# based on the code from  here: https://stackoverflow.com/questions/5558418/list-of-dicts-to-from-dict-of-lists
def DL2LD (dl) :
    """
    convert dict of lists to list of dicts
    """
    if not dl: return []
    #reserve as much *distinct* dicts as the longest sequence
    result = [{} for i in range(max(map (len, dl.values())))]
    #fill each dict, one key at a time
    for k, seq in dl.items() :
        for oneDict, oneValue in zip(result, seq) :
            oneDict[k] = oneValue
    return result

