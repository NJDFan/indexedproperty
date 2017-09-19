"""
Support itemproperty and smarter subclasses thereof.

IndexedProperty allows for the following extension of the basic property concept.

>>> class C:
...     def __init__(self):
...         self._dict = {}
...
...     @indexedproperty
...     def dval(self, key):
...         return self._dict[key]
...         
...     @dval.setter
...     def dval(self, key, value):
...         self._dict[key] = value
...
...     @dval.__iter__
...     def dval(self):
...         return iter(self._dict.items())
...
...     @dval.__len__
...     def dval(self):
...         return len(self._dict)
... 
>>> x = C()
>>> x.dval['bob'] = 'susie'
>>> x.dval['bob']
'susie'
>>> len(x.dval)
1
>>> list(x.dval)
[('bob', 'susie')]

The classes defined here are mostly useful for subclassing new IndexedProperty
style objects.  For actual use you will almost certainly just want to use
the factory function forms as decorators, the same as you would with `property`.

:Author: Rob Gaddi, Highland Technology
:Date: 19-Sep-2017
"""

__version__ = '0.1.4'

import collections
from functools import wraps

#######################################################################
# Trampolines
#######################################################################

class Trampoline:
    """
    Trampolines are thin layers that are returned by the descriptor 
    classes. They are the items that actually receive all the method calls to 
    the property, such as __getitem__.  Creating new property classes will in 
    large part be a function of upgrading their Trampoline classes.
    
    A new trampoline is created each time an IndexProperty is gotten.  They're 
    pretty disposable.
    
    The base Trampoline supports only the [] operations of __getitem__, 
    __setitem__, and __delitem__, which it does by calling the getter, setter, 
    and deleter functions respectively.  These are provided by the user.
    
    It is very likely that subclasses should overload modindex or moduserindex. 
    It is very unlikely that they should overload any of the __*item__ methods.
    
    Attributes:
        iterable_indices (tuple): Base classes that, if the index is a member
        of, the [] operations will attempt to iterate over rather than just
        pass along.
    
        obj (object): The class instance that the property was bound to.
        This is the ``self`` reference for the functions.
    """
    
    iterable_indices = ()
    
    def __init__(self, obj):
        self.obj = obj
    
    def moduserindex(self, index):
        """Modify or validate the user index.
        
        Overload this to modify the index before we attempt to iterate on it.
        
        Arguments:
            index: The thing that was between the ``[]`` markers with no
                modification or ``iterable_indices`` checking.
        
        Returns:
            A modified index.  The base version performs no modification or
            validation on index.
        """
        return index
    
    def modindex(self, index):
        """Modify or validate the single index.
        
        Overload this to modify index values that have already been deemed
        non-iterable, or that are one of the values from an iterable index.
        
        Arguments:
            index: One index that will be passed to the getter, setter, or
                deleter functions.
                
        Returns:
            A modified index.  The base version performs no modification or
            validation on index.
        """
        return index
    
    def __getitem__(self, index):
        """Call the registered getter function.
        
        Arguments:
            index: The user index from [].  May be iterable.
            
        Returns:
            getter(self.obj, index) if index was not in self.iterable_indices,
            or a list of one value per index if it was.
            
        Raises:
            NotImplementedError: No getter was defined for the property
        """
        
        try:
            fget = self.getter
        except AttributeError:
            raise NotImplementedError('no property getter defined')
        
        index = self.moduserindex(index)
        if isinstance(index, self.iterable_indices):
            return [fget(self.modindex(i)) for i in index]
        return fget(self.modindex(index))
        
    def __setitem__(self, index, value):
        """Call the registered setter function.
        
        Arguments:
            index: The user index from [].  May be iterable.
            value: The value to set.  If index is iterable, value may also be
                a non-string iterable.  In this case, calls are paired off as
                setter(self.obj, index[0], value[0]), 
                setter(self.obj, index[1], value[1])...
                
                Doing this requires that the value iterable be the same length
                as the index iterable.
                
                If the index is iterable and the value is not, then the
                calls are setter(self.obj, index[0], value), 
                setter(self.obj, index[1], value)...
                
        Raises:
            ValueError: An iterable index was provided, with an iterable value
                of different length.
            NotImplementedError: No getter was defined for the property

        """
        try:
            fset = self.setter
        except AttributeError:
            raise NotImplementedError('no property setter defined')
        
        index = self.moduserindex(index)
        if isinstance(index, self.iterable_indices):
            # If the value is a sized collection (and not a str), it must be of
            # the same size as the index in order to correlate it.
            try:
                if isinstance(value, str):
                    raise TypeError()
                if len(value) != len(index):
                    raise ValueError("length mismatch; can't broadcast to index")
                for i, v in zip(index, value):
                    fset(self.modindex(i), v)
            except TypeError:
                # We're here on a non-iterable; broadcast it.
                for i in index:
                    fset(self.modindex(i), value)
        else:
            # Non-iterable index; just do the one.
            fset(self.modindex(index), value)
        
    def __delitem__(self, index):
        """Call the registered deleter function.
        
        Arguments:
            index: The user index from [].  May be iterable.
            value: The value to set.  If index is iterable, value may also be
                a non-string iterable.  In this case, calls are paired off as
                setter(self.obj, index[0], value[0]), 
                setter(self.obj, index[1], value[1])...
                
                Doing this requires that the value iterable be the same length
                as the index iterable.
                
                If the index is iterable and the value is not, then the
                calls are setter(self.obj, index[0], value), 
                setter(self.obj, index[1], value)...
                
        Raises:
            NotImplementedError: No getter was defined for the property
        """
        try:
            fdel = self.deleter
        except AttributeError:
            raise NotImplementedError('no property deleter defined')
            
        index = self.moduserindex(index)
        if isinstance(index, self.iterable_indices):
            for i in index:
                fdel(self.modindex(i))
        else:
            fdel(self.modindex(index))
        
#######################################################################
# Property classes
#######################################################################

class IndexedProperty:
    """The basic IndexedProperty.
    
    This does nothing to iterate or modify the key, so it's useful if you just
    want the basic functionality.
    
    The class itself can be used as a decorator as:
        @IndexedProperty()
    or the somewhat more convenient functional decorator is
        @indexedproperty
    """
    
    # This is the class-wide base class for the Trampoline.  Each instance of
    # IndexedProperty will wind up holding it's own local subclass of this
    # base class.
    _Trampoline = Trampoline
    
    # addmethod will not allow you to create a method from illegalmethods.
    illegalmethods = ('__getitem__', '__setitem__', '__delitem__')
    
    def __init__(self, getter=None, name=None, doc=None, *, tdict=None, **kwargs):
        """
        Create a new IndexedProperty.
        
        This will most often be called with no arguments as IndexedProperty(),
        allowing the returned object to be used as a decorator.
        
        Arguments:
            getter (function): getter(self, idx) -> value
            name (str): Name of the descriptor and the trampoline class.
            doc (str): Docstring for the descriptor and trampoline class.
            tdict (dict): Elements for the class dictionary of trampoline
                classes.  This tends to be used only by subclasses calling
                super().__init__()
            kwargs (dict): { method_name: function } dict to be passed to
                addmethod.
        """
        
        # The tdict is the dictionary that will form the class dictionary for
        # _Trampoline objects.
        self.tdict = {}
        if tdict is not None:
            self.tdict.update(tdict)
        self.__doc__ = doc
        self.__name__ = name
        if getter is not None:
            self.addmethod('getter', getter)
        for k, v in kwargs.items():
            self.addmethod(k, v)
        self.updatetrampoline()
        
    def __repr__(self):
        return type(self).__name__ + '()'
        
    def __call__(self, getter):
        """Functional form allows the class itself to be used as a decorator."""
        self.addmethod('getter', getter)
        self.updatetrampoline()
        return self
    
    def updatetrampoline(self):
        """Update the internal class definition for the trampoline."""
        self.tdict['__doc__'] = self.__doc__
        if self.__name__ is None:
            self._trampolinecls = None
        else:
            self._trampolinecls = type(
                self.__name__,
                (self._Trampoline,),
                self.tdict
            )
        
    def __get__(self, obj, objtype=None):
        """Return a Trampoline as a read-only data descriptor."""
        if obj is None:
            return self
        return self._trampolinecls(obj)
        
    def __set__(self, obj, value):
        raise AttributeError("can't assign to " + type(self).__name__)
        
    def addmethod(self, name, fn):
        """Add a method to the trampoline dictionary.
        
        Arguments:
            name (str): Name of the new method.
            fn (function): Code of the new method.
        """
        if name in self.illegalmethods:
            raise AttributeError("can't define " + name + " on " + type(self).__name__)
        
        @wraps(fn)
        def wrapper(trampoline, *args, **kwargs):
            return fn(trampoline.obj, *args, **kwargs)
        self.tdict[name] = wrapper
        
        # First function to define these things wins.
        for attr in ('__module__', '__name__', '__qualname__', '__annotations__', '__doc__'):
            try:
                self._updatedoc(attr, getattr(fn, attr))
            except AttributeError:
                pass
                
    def _updatedoc(self, attr, value):
        """Update documentation properties of the instance.
        
        Subclasses may choose to modify the value en route, but should still
        call this method eventually.
        
        Arguments:
            attr (str): An attribute name such as '__name__' or '__doc__'
            value: The value for the attribute.
        """
        current = self.__dict__.get(attr, None)
        if current is None:
            setattr(self, attr, value)
    
    def __getattr__(self, attr):
        """Return a method decorator that adds an arbitrarily named function
        into the Trampoline class dictionary.
        
        Because an instance of IndexedProperty, will generally only be asked 
        for attributes in the context of class definitions.  That means that we 
        can take any undefined attribute request to be a request for a 
        decorator function that will push the decorated function up into the 
        Trampoline's class dictionary, allowing usages such as::
        
            >>> class C:
            ...     _letters = 'abcdefgh'
            ...
            ...     @indexedproperty
            ...     def letter(self, key):
            ...         return self._letters[key]
            ...
            ...     @letter.upper
            ...     def letter(self, key):
            ...         return self._letters[key].upper()
            ...
            >>> x = C()
            >>> x.letter[3]
            'd'
            >>> x.letter.upper(3)
            'D'
        """
        
        def decorator(fn):
            self.addmethod(attr, fn)
            self.updatetrampoline()
            return self
        return decorator
        
    # Getter, setter, and deleter are important and outside the standard
    # data model, so they get a special callout primarily so they show up
    # better in the documentation.
    def getter(self, fn):
        """Add a getter function: __getitem__ plus index processing."""
        self.addmethod('getter', fn)
        self.updatetrampoline()
        return self
        
    def setter(self, fn):
        """Add a setter function: __setitem__ plus index processing."""
        self.addmethod('setter', fn)
        self.updatetrampoline()
        return self
        
    def deleter(self, fn):
        """Add a deleter function: __delitem__ plus index processing."""
        self.addmethod('deleter', fn)
        self.updatetrampoline()
        return self

class ContainerProperty(IndexedProperty):
    """An IndexedProperty whose indices must be inside a Container, such as
    a list or a dict's keys.  So long as it implements __contains__, we can
    use it.
    
    A KeyError will be raised if any key is not in the base container.
    
    Iteration and length are attempted off the base container, but may fail if 
    the base container doesn't support them.  If iteration is supported, items 
    will be an iterator over (key, getter(key)) pairs.
    
    ContainerProperty objects can be created with the @containerproperty
    decorator, or by invoking the class itself as a decorator as:
        
        @ContainerProperty(_stuff)
        def getterfunction...
    
    """
    
    illegalmethods = ('__getitem__', '__setitem__', '__delitem__', '__iter__', '__len__')
    
    # The _Trampoline is overloaded to provide all of the functionality that
    # should be available when you actually use the property in a class, 
    # in this case the __len__, __iter__, and items methods.
    #
    # We also provide iterable_indices to turn broadcasting on, and use
    # modindex (which gets called for each key that will go to the
    # item methods) to validate the keys without modification.
    
    class _Trampoline(Trampoline):
        iterable_indices = (list, tuple)

        def modindex(self, index):
            """Validate against the base collection."""
            if index not in self.base:
                raise KeyError(index)
            return index
        
        def __len__(self):
            return len(self.base)
            
        def __iter__(self):
            return iter(self.base)
            
        def items(self):
            """Return (idx, value) pairs."""
            for key in self:
                yield (key, self[key])
    
    # When we __init__ the descriptor, we have to add the base to the tdict.
    # and call updatetrampoline() when we're done modifying the tdict.
    
    def __init__(self, base, getter=None, document_indices=True, **kwargs):
        """Create the ContainerProperty
        
        Arguments:
            base (collection): An object supporting __contains__, such as a
                list, dict, set, etc.
                
            document_indices (bool): If True (the default) add information
                about the available indices to the docstring.
        """
        self.document_indices = document_indices
        
        # The trampoline needs access to the base object, so we put it into
        # the class dictionary.
        super().__init__(getter=getter, tdict={'base': base}, **kwargs)
        
    def _updatedoc(self, attr, value):
        """Try to append the keys to __doc__"""
        
        if attr == '__doc__' and self.document_indices:
            MAXLEN = 8
            
            try:
                # Try to pull one too many items off the base collection.
                items = [repr(x) for _, x in zip(range(MAXLEN+1), self.tdict['base'])]
                
                # If we have too many, we need to truncate the list.  The
                # ellipsis itself counts as an item.
                if len(items) > MAXLEN:
                    del items[MAXLEN-1:]
                    items.append('...')
                itemstr = 'Indices are from ' + ', '.join(items)
                if value:
                    value = value + '\n' + itemstr
                else:
                    value = itemstr
            except TypeError:
                # No __iter__ on the base.
                pass
    
        super()._updatedoc(attr, value)

class RangeProperty(IndexedProperty):
    """An IndexedProperty whose indices are a finite range of integers.
    
    This allows indices to be integers, lists of integers, or slices.
    
    For integer indices, negative numbers will wrap around if the defined
    range is entirely non-negative.  Otherwise, out of range indices will
    raise IndexError.
    
    For slice indices, the standard slice behavior regarding out-of-range and
    negative numbers applies.
    
    For list or slice indices, broadcasting rules apply.
    
        # Set a[3] = a[4] = a[5] = 'X'
        a.b[3:6] = 'X'
        
        # Set a[3] = 'X', a[4] = 'Y', a[5] = 'Z'
        a.b[3:6] = ['X', 'Y', 'Z']
        
        # Get ['X', 'Y', 'Z']
        lst = a.b[3:6]
    
    The constructor demands both start and stop arguments, defining a half-open
    range that includes start and does not include stop, just like the range()
    builtin.  The descriptor form makes start optional, setting it to 0 if not
    provided.  The RangeProperty will have .start and .stop data members.
    
    Standard iteration over a RangeProperty yields __getitem__ values, as it if 
    were a list. A RangeProperty also has an `items` iterator and a `range` 
    property, which returns a range object over the keys.
    
    RangeProperty instances can be created with the @rangeproperty decorator
    or using the class directly as either
    
        @RangeProperty(32)
        def getterfunction...
        
        @RangeProperty(0, 32):
        def getterfunction...
        
    """
    
    illegalmethods = ('__getitem__', '__setitem__', '__delitem__', '__iter__', '__len__')
    
    class _Trampoline(Trampoline):
        iterable_indices = (list, tuple, range)
        
        def _negativeindex(self, idx):
            """Flip negative indices as appropriate.
            
            If the range of this Trampoline is entirely positive, then negative
            indices are treated as they are for lists; they represent an offset
            from the end of the list.
            
            If the Trampoline range does legitimately include negative numbers
            then pass the negative index back unaltered.
            """
            
            # Don't need an explicit check for self.stop, as at initialization
            # time we enforce self.start <= self.stop
            if idx >= 0 or self.start < 0:
                return idx
            else:
                return self.stop + idx
        
        def _boundindex(self, idx):
            """For slices (but not for single indices), clip indices to the
            bounds of the range."""
            
            idx = self._negativeindex(idx)
            if idx < self.start:
                return self.start
            elif idx > self.stop:
                return self.stop
            else:
                return idx
        
        # By hooking moduserindex, we can intercept a slice (which will often
        # have lots of Nones in it) and turn it into a concrete range object,
        # which can be iterated.
        def moduserindex(self, index):
            """Turn slices into ranges, pass anything else along"""
            if isinstance(index, slice):
                start, stop, step = index.start, index.stop, index.step
                
                start = self.start if start is None else self._boundindex(start)
                stop = self.stop if stop is None else self._boundindex(stop)
                if step is None:
                    step = 1
                ret = range(start, stop, step)
                return ret
            return index
        
        # Now that we're down to single integer indices we can handle the
        # endaround logic that allows for things like [-1].  This both
        # validates and potentially modifies the index.
        def modindex(self, index):
            """Ensure proper handling of negative indices and validate.
            
            Negative indices should wrap around, unless the range itself 
            supports negative indices (can't imagine why it would).
            """
            index = self._boundindex(index)
            if not self.start <= index < self.stop:
                raise IndexError(type(self).__name__ + " index out of range")
            return index
        
        def __len__(self):
            return self.stop - self.start
            
        def __iter__(self):
            for i in self.range:
                yield self[i]
            
        def __reversed__(self):
            for i in reversed(self.range):
                yield self[i]
            
        def items(self):
            """Return (idx, value) pairs.
            
            Equivalent to enumerate(prop, prop.start)
            """
            for i in self.range:
                yield (i, self[i])
        
        @property
        def range(self):
            """Return a range object that covers the iterable range."""
            return range(self.start, self.stop)
    
    # Once again, the Trampoline requires the start and stop parameters,
    # so we need to pass them into the class dictionary and recreate the
    # internal Trampoline class.
    
    def __init__(self, start, stop=None, getter=None, document_indices=True, **kwargs):
        """Create the RangeProperty.
        
        Arguments:
            start (int): If stop is None, the range is 0:start.  Otherwise
                the range is start:stop.  This is the same as the built-in
                range function.
            stop (int): Stop point of the range
            
            document_indices (bool): If True (the default) add information
                about the available indices to the docstring.
        """
        
        self._document_indices = document_indices
        
        if stop is None:
            start, stop = 0, start
        if stop < start:
            raise ValueError("Start must be less than or equal to stop.")
        tdict = {'start' : start, 'stop' : stop}
            
        super().__init__(getter, tdict=tdict, **kwargs)
        self.updatetrampoline()
        
    def _updatedoc(self, attr, value):
        """Append the range to __doc__"""
        
        if attr == '__doc__' and self._document_indices:
            itemstr = 'Index range is {0[start]}:{0[stop]}'.format(self.tdict)
            if value:
                value += '\n' + itemstr
            else:
                value = itemstr
        super()._updatedoc(attr, value)

#######################################################################
# Descriptors
#######################################################################

def indexedproperty(fget=None):
    """Functional form to create ItemProperty objects.
    
    Usage:
    @indexedproperty
    def getterfunction(self, index):
        ...
    """
    return IndexedProperty(fget)

def containerproperty(base):
    """Functional form to create ContainerProperty objects.
    
    Usage (base is any object that supports "in"):
    @containerproperty(('Anna', 'Basil', 'Cesar'))
    """
    
    return ContainerProperty(base)

def rangeproperty(a, b=None):
    """Functional form to create RangeProperty objects.
    
    Usage (start and stop are integers):
    @rangeproperty(stop)            # start = 0
    @rangeproperty(start, stop)
    """
    
    if b is None:   start, stop = 0, a
    else:           start, stop = a, b
    
    return RangeProperty(start, stop)
