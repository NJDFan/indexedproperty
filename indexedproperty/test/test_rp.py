"""Test RangeProperty and rangeproperty."""

import indexedproperty as ix
import unittest

class RPTarget:
    def __init__(self, cbtarget):
        self._cb = cbtarget
        
    @ix.RangeProperty(1, 11)
    def topten(self, key):
        """key get blah blah blah"""
        
        self._cb.gets += 1
        return 11 - key
        
    @topten.setter
    def topten(self, key, value):
        """key set blah blah blah"""
        
        if value != key * 2:
            raise ValueError('topten[{}] == {}'.format(key, key*2))
        self._cb.sets.append(key)
        
    @topten.deleter
    def topten(self, key):
        """key del blah blah blah"""
        
        self._cb.dels.append(key)

class RPTest(unittest.TestCase):
    
    def setUp(self):
        self.gets = 0
        self.sets = []
        self.dels = []
        self.tgt = RPTarget(self)
    
    def assertStats(self, gets, sets, dels):
        self.assertTupleEqual((gets, sets, dels), (self.gets, len(self.sets), len(self.dels)))
    
    def test_topTenList(self):
        self.assertEqual(len(self.tgt.topten), 10)
        self.assertEqual(self.tgt.topten.range, range(1, 11))
        for n, (k, v) in enumerate(self.tgt.topten.items()):
            self.assertEqual(n+1, k)
            self.assertEqual(k+v, 11)
        self.assertStats(10, 0, 0)
        
    def test_Reversed(self):
        rvalues = list(range(1, 11))
        values = list(reversed(rvalues))
        
        self.assertListEqual(list(self.tgt.topten), values)
        self.assertListEqual(list(reversed(self.tgt.topten)), rvalues)
        self.assertStats(20, 0, 0)
    
    def test_SetBroadcast(self):
        vals = [x*2 for x in range(1,11)]
        self.tgt.topten[:] = vals
        
        vals = [x*2 for x in range(5,8)]
        self.tgt.topten[5:8] = vals
        
        self.tgt.topten[-1] = 20
        with self.assertRaises(ValueError, msg='topten[2] == 4'):
            self.tgt.topten[:] = 2
        
        self.assertStats(0, 15, 0)
        self.assertListEqual(self.sets,
            [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 5, 6, 7, 10, 1]
        )
        
    def test_Del(self):
        del self.tgt.topten[-3:]
        del self.tgt.topten[:4]
        del self.tgt.topten[5]
        del self.tgt.topten[-2]
        
        self.assertListEqual(self.dels,
            [8, 9, 10, 1, 2, 3, 5, 9]
        )
        self.assertStats(0, 0, 8)
        
    def test_slicing(self):
        self.assertListEqual(self.tgt.topten[:4], [10, 9, 8])
        self.assertListEqual(self.tgt.topten[1:4], [10, 9, 8])
        self.assertListEqual(self.tgt.topten[2:4], [9, 8])
        self.assertListEqual(self.tgt.topten[-1:4], [])
        
        self.assertListEqual(self.tgt.topten[-5:], [5, 4, 3, 2, 1])
        self.assertListEqual(self.tgt.topten[-5:-1], [5, 4, 3, 2])
        self.assertListEqual(self.tgt.topten[-5:9], [5, 4, 3])
        
        self.assertListEqual(self.tgt.topten[2:10], [9, 8, 7, 6, 5, 4, 3, 2])
        self.assertListEqual(self.tgt.topten[2:10:3], [9, 6, 3])
        
    def test_Doc(self):
        self.assertEqual(
            self.tgt.topten.__doc__,
            "key get blah blah blah\nIndex range is 1:11"
        )

if __name__ == '__main__':
    unittest.main()
