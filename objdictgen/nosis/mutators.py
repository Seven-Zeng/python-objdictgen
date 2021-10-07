from __future__ import absolute_import
from future import standard_library
standard_library.install_aliases()
from builtins import str
from builtins import map
from builtins import object

from .mutate import XMLP_Mutator, XMLP_Mutated
from . import mutate
from .introspect import isInstanceLike, attr_update, \
     data2attr, attr2data, getCoreData, setCoreData, isinstance_any
from .util import _klass, _module, obj_from_name
from .XtoY import aton

import sys
if sys.version_info[0] >= 3:
    unicode = str

class _EmptyClass(object): pass

class mutate_builtin_wrapper(XMLP_Mutator):

    def __init__(self):
        XMLP_Mutator.__init__(self,None,'builtin_wrapper')

    def mutate(self,obj):
        wrap = _EmptyClass()
        wrap.__toplevel__ = obj
        return XMLP_Mutated(wrap)

    def unmutate(self,mobj):
        return mobj.obj.__toplevel__

mutate.add_mutator(mutate_builtin_wrapper())

# We pickle array.array() as type "array" and Numeric.array as
# type "Numpy_array" (this is really what earlier xml_pickles did,
# except you had to use EITHER array.array() or Numeric.array() -
# you couldn't mix them (in fact, you couldn't pickle array.array()
# types if Numeric was installed).

import array

#-- array.array --
class mutate_array(XMLP_Mutator):

    def __init__(self):
        XMLP_Mutator.__init__(self,array.ArrayType,'array',0)

    def mutate(self,obj):
        list_ = []
        for item in obj:
            list_.append(item)
        return XMLP_Mutated(list_)

    def unmutate(self,mobj):
        obj = mobj.obj
        as_int = 1
        for item in obj:
            if type(item) == type(1.0):
                as_int = 0
        if as_int:
            return array.array('b',obj)
        else:
            return array.array('d',obj) # double precision

mutate.add_mutator(mutate_array())

#-- SREs --

# save the RE pattern in the element body

import re
SRE_Pattern_type = type(re.compile(''))

class mutate_sre(XMLP_Mutator):

    def __init__(self):
        XMLP_Mutator.__init__(self,SRE_Pattern_type,'SRE',paranoia=0,
                              in_body=1)

    def mutate(self,obj):
        return XMLP_Mutated(obj.pattern)

    def unmutate(self,mobj):
        return re.compile(mobj.obj)

mutate.add_mutator(mutate_sre())

#-- rawpickles --

# save the pickle in the element body

import pickle

class mutate_rawpickle(XMLP_Mutator):

    def __init__(self):
        XMLP_Mutator.__init__(self,None,'rawpickle',0)

    def mutate(self,obj): return XMLP_Mutated(pickle.dumps(obj))
    def unmutate(self,mobj): return pickle.loads(str(mobj.obj))

mutate.add_mutator(mutate_rawpickle())

#-- mx.DateTime --

# see test_mutators.py for an alternate way to pickle these

try:
    import mx.DateTime
    mxDateTime_type = type(mx.DateTime.localtime())
except:
    mxDateTime_type = None

class mutate_mxdatetime(XMLP_Mutator):

    def __init__(self):
        XMLP_Mutator.__init__(self,mxDateTime_type,'mxDateTime',
                              paranoia=0,in_body=1)

    def mutate(self,obj):
        # (I avoided using strftime(), for portability reasons.)
        # Pickle seconds as a float to save full precision.
        s = "YMD = %d/%d/%d, HMS = %d:%d:%.17g" % \
            (obj.year,obj.month,obj.day,\
             obj.hour,obj.minute,obj.second)
        return XMLP_Mutated(s)

    def unmutate(self,mobj):
        obj = mobj.obj
        # is this forgiving enough? :-)
        fmt = 'YMD\s*=\s*([0-9]+)\s*/\s*([0-9]+)\s*/\s*([0-9]+)\s*,\s*'
        fmt += 'HMS\s*=\s*([0-9]+)\s*:\s*([0-9]+)\s*:\s*([0-9\.]+)'
        m = re.match(fmt,obj)
        # this started giving a deprecation warning about passing a
        # float where an int was expected
        #return apply(mx.DateTime.DateTime,map(float,m.groups()))

        args = list(map(int,m.groups()[:5])) + [float(m.group(6))]
        return mx.DateTime.DateTime(*args)

if mxDateTime_type is not None:
    mutate.add_mutator(mutate_mxdatetime())

#-- mutator + support functions for handling objects subclassed
#-- from builtin types (Python >= 2.2)

def newdata_to_olddata(o):
    """Given o, an object subclassed from a builtin type with no attributes,
    return a tuple containing the raw data and a string containing
    a tag to save in the extra= field"""
    return (getCoreData(o),"%s %s"%(_module(o),_klass(o)))

def olddata_to_newdata(data,extra,paranoia):
    """Given raw data, the extra= tag, and paranoia setting,
    recreate the object that was passed to newdata_to_olddata."""
    (module,klass) = extra.split()
    o = obj_from_name(klass,module,paranoia)

    if isinstance_any(o,(int,float,complex)) and \
                      isinstance(data, (str, unicode)):
        data = aton(data)

    o = setCoreData(o,data)
    return o

# my semantic preferences, of the moment :-)
newinst_to_oldinst = data2attr
oldinst_to_newinst = attr2data

def hasPickleFuncs(obj):
    "Does obj define the special pickling functions?"
    return (hasattr(obj,'__getstate__') or \
            hasattr(obj,'__setstate__') or \
            hasattr(obj,'__getinitargs__'))

class mutate_bltin_instances(XMLP_Mutator):

    def __init__(self):
        XMLP_Mutator.__init__(self,None,'__compound__',0)

    def mutate(self,obj):

        if isinstance(obj, unicode):
            # unicode strings are required to be placed in the body
            # (by our encoding scheme)
            self.in_body = 1
        else:
            # XXX really should check getInBody(), but we'd have
            # to do isinstance() for each type ... maybe do later
            self.in_body = 0

        if isInstanceLike(obj) or hasPickleFuncs(obj):
            # obj has data items (list,dict,tuple) *AND* attributes.
            # mutate to an oldstyle object, turning the data items into
            # a special attribute (eg. __items__, __entries__).
            #
            # also, if obj defines the special pickling functions, we treat
            # it as an instance so we don't have to duplicate all the
            # protocol logic here.
            return XMLP_Mutated(newinst_to_oldinst(obj))
        else:
            # obj has only data items (list,dict,tuple,etc.)
            # convert to the raw datatype and remember the
            # module.class of obj for unpickling.
            (o,t) = newdata_to_olddata(obj)
            return XMLP_Mutated(o,t)

    def unmutate(self,mobj):
        obj = mobj.obj
        if not mobj.extra:
            # converting obj with __coredata__ + attrs
            return oldinst_to_newinst(obj)
        else:
            # converting obj with __coredata__ but no attrs
            return olddata_to_newdata(obj,mobj.extra,self.paranoia)

# add mutator for instances of builtin classes (int, dict, object, etc.)
mutate.add_mutator(mutate_bltin_instances())