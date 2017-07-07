"""Test ContainerProperty and containerproperty."""

import indexedproperty as ix
import unittest
import re

# This is the most punk unittest ever.  🤘
timfest_bands = {"Allweather","Ash Williams","Avenues",
"Captain 9’s & The Knickerbocker Trio","Caskitt","Civil War Rust","CUT UP",
"Dead Frets","Eastern Span","False Positives","Four Lights","Greg Rekus",
"Heartsounds","KICKER","Reunions","Secondaries","Sic Waiting","Squarecrow",
"Success","The Copyrights","The Lucky Eejits","The Stupid Daikini","Tiltwheel",
"Toosie","toyGuitar","UNDER 15 SECONDS (acoustic)","Verbal Abuse",
"Year Of The Fist"}

timfest_dates = ['Sept 28', 'Sept 29', 'Sept 30', 'Oct 1']

class CPTarget:
    def __init__(self, cbtarget):
        self._cb = cbtarget
        self._dict = {k:1 for k in timfest_bands}
        
    @ix.ContainerProperty(timfest_bands)
    def appearances(self, key):
        """key get blah blah blah"""
        
        self._cb.gets += 1
        return self._dict[key]
        
    @appearances.setter
    def appearances(self, key, value):
        """key set blah blah blah"""
        
        self._cb.sets += 1
        self._dict[key] = value
        
    @appearances.deleter
    def appearances(self, key):
        """key del blah blah blah"""
        
        self._cb.dels += 1
        self._dict[key] = 0

    @ix.containerproperty(timfest_dates)
    def date(self, key):
        
        self._cb.gets += 1
        return int(key.split()[1])
    
class CPTest(unittest.TestCase):
    
    def setUp(self):
        self.gets = self.sets = self.dels = 0
        self.tgt = CPTarget(self)
    
    def assertStats(self, gets, sets, dels):
        self.assertTupleEqual((gets, sets, dels), (self.gets, self.sets, self.dels))
        
    def test_appearances(self):
        self.assertEqual(len(self.tgt.appearances), len(timfest_bands))
        
        self.assertEqual(self.tgt.appearances['Year Of The Fist'], 1)
        self.tgt.appearances['Year Of The Fist'] = 3
        self.assertEqual(self.tgt.appearances['Year Of The Fist'], 3)
        
        self.assertEqual(self.tgt.appearances['Ash Williams'], 1)
        del self.tgt.appearances['Ash Williams']
        self.assertEqual(self.tgt.appearances['Ash Williams'], 0)
        
        self.assertStats(4, 1, 1)
        
    def test_notAppearing(self):
        with self.assertRaises(KeyError):
            x = self.tgt.appearances['Kenny G']
        with self.assertRaises(KeyError):
            self.tgt.appearances['Nickelback'] = 100
        with self.assertRaises(KeyError):
            del self.tgt.appearances['Taylor Swift']
            
        self.assertStats(0, 0, 0)
        
    def test_items(self):
        expecting = [('Sept 28', 28), ('Sept 29', 29), ('Sept 30', 30), ('Oct 1', 1)]
        actual = list(self.tgt.date.items())
        
        self.assertListEqual(expecting, actual)
        self.assertStats(4, 0, 0)
        
    def test_iteration(self):
        self.assertListEqual(list(self.tgt.date), timfest_dates)
        self.assertSetEqual(set(self.tgt.appearances), timfest_bands)
        # This should have caused 0 gets.
        self.assertStats(0, 0, 0)

    def test_EllipseDoc(self):
        doc = self.tgt.appearances.__doc__
        self.assertTrue(doc.endswith('...'))
        self.assertTrue(doc.startswith("key get blah blah blah\nIndices are from"))
        
        bands = re.findall(r"'(.+?)'", doc)
        self.assertEqual(len(bands), 7)
        for b in bands:
            self.assertIn(b, timfest_bands)
        
    def test_FiniteDoc(self):
        self.assertEqual(
            self.tgt.date.__doc__,
            "Indices are from 'Sept 28', 'Sept 29', 'Sept 30', 'Oct 1'"
        )

if __name__ == '__main__':
    unittest.main()
