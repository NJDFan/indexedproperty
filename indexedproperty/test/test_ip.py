"""Test IndexedProperty and indexedproperty."""

import indexedproperty as ix
import unittest

class IPTarget:
    def __init__(self, cbtarget):
        self._cb = cbtarget
        self._dict = {}
        
    @ix.IndexedProperty()
    def key(self, key):
        """key get blah blah blah"""
        self._cb.gets += 1
        return key
        
    @key.setter
    def key(self, key, value):
        """key set blah blah blah"""
        
        self._cb.sets += 1
        raise AttributeError('key not settable')
        
    @key.deleter
    def key(self, key):
        """key del blah blah blah"""
        
        self._cb.dels += 1
        raise AttributeError('key not deletable')

    @ix.indexedproperty
    def upperkey(self, key):
        """uk get etc"""
        
        val = self._dict[key]
        self._cb.gets += 1
        return val
        
    @upperkey.setter
    def upperkey(self, key, value):
        """uk set etc"""
        
        self._dict[key] = value.upper()
        self._cb.sets += 1
    
class IPTest(unittest.TestCase):
    key = 'bananaBANANAbanana'
    data = 'appleAPPLE'
    
    def setUp(self):
        self.gets = self.sets = self.dels = 0
        self.tgt = IPTarget(self)
    
    def assertStats(self, gets, sets, dels):
        self.assertTupleEqual((gets, sets, dels), (self.gets, self.sets, self.dels))
        
    def test_get(self):
        self.assertEqual(self.key, self.tgt.key[self.key])
        self.assertStats(1, 0, 0)
        
    def test_set(self):
        with self.assertRaises(AttributeError, msg='key not settable'):
            self.tgt.key[self.key] = None
        self.assertStats(0, 1, 0)
        
    def test_del(self):
        with self.assertRaises(AttributeError, msg='key not deletable'):
            del self.tgt.key[self.key]
        self.assertStats(0, 0, 1)        

    def test_upperGetSet(self):
        self.tgt.upperkey[self.key] = self.data
        self.assertEqual(self.tgt.upperkey[self.key], self.data.upper())
        with self.assertRaises(KeyError):
            self.tgt.upperkey[self.key.upper()]
        self.assertStats(1, 1, 0)
        
    def test_upperDel(self):
        with self.assertRaises(NotImplementedError):
            del self.tgt.upperkey[self.key]
        self.assertStats(0, 0, 0)

    def test_Doc(self):
        """Confirm that __doc__ members are unaltered."""
        self.assertEqual(self.tgt.key.__doc__, 'key get blah blah blah')
        self.assertEqual(self.tgt.upperkey.__doc__, 'uk get etc')

if __name__ == '__main__':
    unittest.main()
