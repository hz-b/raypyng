import src.raypyng.collections as rc
from copy import copy
lx = ['good_value', 'bad value']
ml = rc.MappedList(rc.sanitizeName,lx)
ml1 = copy(ml)
ml1


kvx = {'bad key':'bad value','good_key':'good_value'}
md = rc.MappedDict(rc.sanitizeName,kvx)
md1 = copy(md)