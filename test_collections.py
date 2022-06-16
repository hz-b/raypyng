import RayPyNG.collections as rc
from copy import copy
lx = ['good_value', 'bad value']
ml = rc.MappedList(rc.protectName,lx)
ml1 = copy(ml)
ml1


kvx = {'bad key':'bad value','good_key':'good_value'}
md = rc.MappedDict(rc.protectName,kvx)
md1 = copy(md)