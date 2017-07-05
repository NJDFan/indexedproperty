==================
Indexed Properties
==================

Overview
========

This package supports indexed properties on class instances.  Whereas the
builtin property function allows you create functions for single-valued 
properties, the indexedproperty package allows you to create properties that
accept an index argument like the __getitem__/__setitem__/__delitem__
set::

	>>> from indexedproperty import indexedproperty
	>>> class PropertyTest:
	... 	def __init__(self):
	... 		self._singleprop = None
	... 		self._dict = {}
	... 	
	... 	# Standard builtin property
	... 	@property
	... 	def sprop(self):
	... 		return self._singleprop
	... 		
	... 	@sprop.setter
	... 	def sprop(self, value):
	... 		print('Setting sprop', value)
	... 		self._singleprop = value
	... 	
	... 	# Fancy new indexed property
	... 	@indexedproperty
	... 	def iprop(self, key):
	... 		return self._dict[key]
	... 		
	... 	@iprop.setter
	... 	def iprop(self, key, value):
	... 		print('Setting iprop {0}={1}'.format(key, value))
	... 		self._dict[key] = value
	...
	>>> x = PropertyTest()
	>>> x.sprop = 5
	Setting sprop 5
	>>> x.sprop
	5
	>>> x.iprop['Gilliam'] = 'Terry'
	Setting iprop Gilliam=Terry
	>>> x.iprop['Gilliam']
	'Terry'
	
Decorator Functions
===================

The most convenient use for this library is through the decorator functions.

	indexedproperty
		Marks a function as the getter (__getitem__) for an IndexedProperty. 
		The .setter (__setitem__) and .deleter(__delitem__) methods may be 
		called on the returned IndexedProperty to add additional functionality 
		for the property
		
	containerproperty(base)
		Marks a function as the getter (__getitem__) for a ContainerProperty. A 
		ContainerProperty is indexed on the container provided by base and 
		raises a KeyError if the users's key is not "in" the base.
		
		If the base supports iter() and len(), the ContainerProperty does as 
		well, and adds an items() iterator similar to the one provided by dict.  
		Broadcasting is supported on list and tuple keys.
		
	rangeproperty([start=0], stop)
		Marks a function as the getter (__getitem__) for an RangeProperty. This 
		property is indexed on the half-open numeric range defined by 
		range(start, stop), and behaves like a Sequence, though with a 
		potentially non-zero lower bound.
		
		RangeProperty elements support iteration, negative index wraparound (if 
		start >= 0), and broadcasting on list, tuple, range, and slice keys.
		
Decorating Methods
==================

Akin to *property*, the basic operations are to define the setter, getter, and
deleter for an IndexedProperty.  The functional form of the decorator assumes
the getter, and further assignments are made by the .setter and .deleter
methods of the property.

Unlike a property, however, decorators can be created to provide any function
including "magic" methods like *__iter__* and *__contains__*, which will work
as expected.  In all cases, the first argument to the function (typically `self`)
will point to an instance of the class that the property is defined in.

Or to say it another way, when you have::

	@x.__iter__
	def fancyproperty(self):
		...
		
	def unfancymethod(self):
		...
		
both of those get the same self.

On the base IndexedProperty, you can assign to .iterable_indices with a tuple
of classes that should be given special treatment.  If the key in the brackets
is an instance of one of then, then rather than pass the key on to the
getter/setter/deleter functions directly, it will be iterated into successive
calls.  So if x.iterable_indices = (list, tuple)

+--------------------------+---------------------------------+
|Doing                     | Does                            |
+==========================+=================================+
| x[5]                     | return x.getter(self, 5)        |
+--------------------------+---------------------------------+
| x[5,10,15]               | return [x.getter(self, 5),      |
|                          | x.getter(self, 10),             |
|                          | x.getter(self, 15)]             |
+--------------------------+---------------------------------+
| x[5] = 'Larry'           | x.setter(self, 5, 'Larry')      |
+--------------------------+---------------------------------+
| x[5,10,15] = 'Larry'     | x.setter(self, 5, 'Larry')      |
|                          | x.setter(self, 10, 'Larry')     |
|                          | x.setter(self, 15, 'Larry')     |
+--------------------------+---------------------------------+
| x[5,10,15] = ("Larry"    | x.setter(self, 5, "Larry")      |
|               "can't",   | x.setter(self, 10, "can't")     |
|               "spel")    | x.setter(self, 15, "spel")      |
+--------------------------+---------------------------------+

The setter broadcasting concept is taken from numpy; you can assign either a
single value or an iterable of values that is the same length as the list of keys.
Strings are treated as single values, and non-string iterables of a different
length than the key list raise ValueError.

You can also assign the .moduserindex and .modindex functions.

	* moduserindex(self, index) is called on the original index, i.e. (5, 10, 
	  15).  It must return a modified (or unmodified) index or raise an
	  exception.  This is how RangeProperty turns a slice index into an iterable
	  range.
	  
	* modindex(self, index) is called on each index as it will go to the getter/setter/deleter
	  functions.  It must return a modified (or unmodified) index or raise an 
	  exception.  This is how ContainerProperty raises a KeyError if the index is 
	  not found in the base list.

Simply assigning these functions is fine for the base IndexedProperty, as the
default versions return the index unaltered so their loss is no big deal.
Assigning to them on ContainerProperty or RangeProperty will break things; these
should be formally subclassed rather than just patched.

__getitem__, __setitem__, and __delitem__ cannot be patched, as it would
break the magic.

Some Use Cases
==============

Here we have both *rangeproperty* in it's natural habitat, and an utterly
gratuitious use of assigning additional functions to the property::

	>>> import indexedproperty as ix
	>>> class Uint32:
	... 	def __init__(self, val=0):
	... 		self.word = val
	... 		
	... 	def __repr__(self):
	... 		return "{0}(0x{1:x})".format(type(self).__name__, self.word)
	... 
	... 	@ix.RangeProperty(32)
	... 	def bit(self, b):
	... 		return self.word & (1 << b)
	... 		
	... 	@bit.setter
	... 	def bit(self, b, val):
	... 		v = 1 << b
	... 		self.word |= v
	... 		if not val:
	... 			self.word ^= v
	... 			
	... 	@bit.count
	... 	def bit(self):
	... 		return sum(bool(b) for b in self.bit)
	... 
	... 	@bit.lowest
	... 	def bit(self):
	... 		for idx, b in self.bit.items():
	... 			if b:
	... 				return idx
	... 		return None
	...
	... 	@bit.highest
	... 	def bit(self):
	... 		for idx in reversed(self.bit.range):
	... 			if self.bit[idx]:
	... 				return idx
	... 		return None
	... 
	... 	def clear(self):
	... 		self.word = 0
	... 	
	>>> x = Uint32()
	>>> x.bit[1::4] = True
	>>> x
	Uint32(0x22222222)
	>>> x.bit[:8]
	[0, 2, 0, 0, 0, 32, 0, 0]
	>>> x.bit[15:7:-1]
	[0, 0, 8192, 0, 0, 0, 512, 0]
	>>> x.bit.count()
	8
	>>> x.bit.lowest()
	1
	>>> x.bit.highest()
	29
	>>> (list(x.bit))[::-1] == list(reversed(x.bit))
	True

Here is *containerproperty* providing both access restriction and broadcasting
functionality to an internal list of properties.

	>>> import indexedproperty as ix
	>>> class FoodRestrictions:
	... 	_foodlist = ['apples', 'bananas', 'pears']
	... 
	... 	def __init__(self):
	... 		self.fooddict = { k : [] for k in self._foodlist }
	... 
	... 	@ix.containerproperty(_foodlist)
	... 	def lunch(self, idx):
	... 		return self.fooddict[idx]
	... 
	... 	@lunch.setter
	... 	def lunch(self, idx, value):
	... 		self.fooddict[idx] = value
	... 
	>>> x = FoodRestrictions()
	>>> x.lunch['apples'] = 'I have an apple'
	>>> x.lunch['bread'] = 'But I want bread'
	Traceback (most recent call last):
	KeyError: 'bread'
	>>> x.lunch['pears'] = 5
	>>> x.lunch['apples', 'pears']
	['I have an apple', 5]
	>>> sorted(x.lunch)
	['apples', 'bananas', 'pears']
	
What's Under The Hood
=====================

When you get a class member defined as an IndexedProperty, what is returned is
a subclass of Trampoline.  The definition of that class is local to the 
specific IndexedProperty under discussion, and is updated every time a new
member is created by one of the IndexedProperty's decorators.  In the above
example, when @lunch.setter is executed it updates the class definition for
the lunch Trampoline to include a setter() method.

So when you ask for x.lunch, you get a new instance of that Trampoline subclass
that has that setter function, as well as getter, __iter__, __len__, and items,
and a .obj pointer to x.  The Trampoline the function calls against it back
against the functions originally decorated.

Extending IndexedProperty
=========================

New types of indexed properties (such as RangeProperty) can be created by 
subclassing IndexedProperty.  This can be a bit tricky, because the class 
does some of the work and the Trampoline subclass does the rest.

See the source code for ContainerProperty and RangeProperty for examples of how 
this is done.  Start with ContainerProperty, it's the more straightforward of 
the two.

The important logic to follow is

1) The IndexedProperty subclass has a ._Trampoline member, which is a subclass
of Trampoline.  Class methods for the trampoline that are not specific to a
given instance of the IndexedProperty can be defined here.  In these methods,
the object that the property is a member of is available as ``self.obj``.

2) For class methods (and properties) that **are** instance specific, the
IndexedProperty subclass has a .tdict member, which is the class dictionary
for the Trampoline.

3) Having modified the .tdict (probably in __init__), a call to updatetrampoline()
will recreate the **instance's** ._trampolinecls, which is a subclass of the
IndexedProperty ._Trampoline with overloading defined by .tdict.  This is what
puts the methods, such as the getter, setter, etc, into the _Trampoline.

Another very common usage is wanting a variant on ContainerProperty that 
performs some minor transformation on the key before checking it against the 
container. For example, if the key is a string it should be made uppercase::

	>>> from indexedproperty import ContainerProperty
	>>> class UCProperty(ContainerProperty):
	... 	"""A ContainerProperty that transforms string keys to uppercase."""
	... 	class _Trampoline(ContainerProperty._Trampoline):
	... 		def modindex(self, index):
	... 			index = index.upper()
	... 			return super().modindex(index)
	... 			
	>>> class TestClass:
	... 	_indices = {'PI':3.14, 'E':2.718, 'I':(0+1j), 'TAU':6.28}
	... 	
	... 	@UCProperty(_indices)
	... 	def constant(self, key):
	... 		return self._indices[key]
	
	>>> x = TestClass()
	>>> x.constant['pi']
	3.14
	>>> x.constant['PI']
	3.14
	>>> x.constant['PI'] = 5
	Traceback (most recent call last):
	NotImplementedError: no property setter defined
	>>> sorted(x.constant.items())
	[('E', 2.718), ('I', 1j), ('PI', 3.14), ('TAU', 6.28)]
	
:author: Rob Gaddi, Highland Technology
:date: 21-Mar-2016
:version: 0.1.1
