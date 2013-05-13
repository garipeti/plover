"""Unit tests for DictionaryLoader.py ."""

from dictionarymanager.store.Dictionary import Dictionary
from dictionarymanager.store.JsonLoader import JsonLoader
import os
import plover.config as conf
import unittest

class LoaderTestCase(unittest.TestCase):
    
    def test_simple(self):
        filename = os.path.join(conf.ASSETS_DIR, "test.json")
        loader = JsonLoader()
        a = Dictionary()
        a.load(filename, loader)
        
        a.insert("stroke", "translation")
        self.assertEqual(a.get("stroke"), "translation")
        
        origStroke = a.keys()[0]
        origTranslation = a.get(origStroke)
        a.remove(origStroke, origTranslation)
        self.assertEqual(a.get(origStroke), None)
        
        a.change(origStroke, origTranslation, "stroke", "translation")
        self.assertEqual(a.get("stroke"), "translation")
        self.assertEqual(a.get(origStroke), None)
        
    def test_revert(self):
        filename = os.path.join(conf.ASSETS_DIR, "test.json")
        loader = JsonLoader()
        a = Dictionary()
        a.load(filename, loader)
        b = Dictionary()
        b.load(filename, loader)
        
        a.insert("stroke", "translation")
        a.remove("stroke", "translation")
        self.assertEqual(a, b)
        
        origStroke = a.keys()[0]
        origTranslation = a.get(origStroke)
        a.change(origStroke, origTranslation, "stroke", "translation")
        a.change("stroke", "translation", origStroke, origTranslation)
        self.assertEqual(a, b)
        
        a.remove(origStroke, origTranslation)
        a.insert(origStroke, origTranslation)
        self.assertEqual(a, b)
        
    def test_multiple(self):
        filename = os.path.join(conf.ASSETS_DIR, "test.json")
        loader = JsonLoader()
        a = Dictionary()
        a.load(filename, loader)
        b = Dictionary()
        b.load(filename, loader)
        
        a.insert("stroke", "translation")
        a.change("stroke", "translation", "stroke2", "translation2")
        a.remove("stroke2", "translation2")
        self.assertEqual(a, b)
        
if __name__ == '__main__':
    unittest.main()