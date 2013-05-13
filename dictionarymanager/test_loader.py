"""Unit tests for DictionaryLoader.py ."""

from dictionarymanager.store.DictionaryLoader import DictionaryLoader
from dictionarymanager.store.JsonLoader import JsonLoader
from dictionarymanager.store.RtfLoader import RtfLoader
import os
import plover.config as conf
import unittest

class LoaderTestCase(unittest.TestCase):
    
    def test_jsonloader(self):
        filename = os.path.join(conf.ASSETS_DIR, "test.json")
        loader = JsonLoader()
        (dictionary, config) = loader.load(filename)
        loader.write(filename + "_", dictionary, config)
        
        a = DictionaryLoader().load(filename)
        b = DictionaryLoader().load(filename + "_")
        
        self.assertEqual(a, b)
        
        os.remove(filename + "_")
    
    def test_rtfloader(self):
        filename = os.path.join(conf.ASSETS_DIR, "test.rtf")
        loader = RtfLoader()
        (dictionary, config) = loader.load(filename)
        loader.write(filename + "_", dictionary, config)
        
        a = DictionaryLoader().load(filename)
        b = DictionaryLoader().load(filename + "_")
        
        self.assertEqual(a, b)

        os.remove(filename + "_")
        
if __name__ == '__main__':
    unittest.main()