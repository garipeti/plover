"""Unit tests for DictionaryLoader.py ."""

from dictionarymanager.store.Store import Store
import os
import plover.config as conf
import unittest

class LoaderTestCase(unittest.TestCase):
    
    def test_filter(self):
        filename = os.path.join(conf.ASSETS_DIR, "test.json")
        store = Store(conf.get_config())
        store.loadDictionary(filename)
        
        # test filter by stroke
        stroke = store.data[0].get(Store.ATTR_STROKE)
        store.filter({Store.ATTR_STROKE: stroke})
        self.assertEqual(len(store.rows), 1)
        
        # test filter by translation
        translation = store.data[0].get(Store.ATTR_TRANSLATION)
        store.filter({Store.ATTR_TRANSLATION: translation})
        self.assertEqual(len(store.rows), 1)

    def test_sort(self):
        filename = os.path.join(conf.ASSETS_DIR, "test.json")
        store = Store(conf.get_config())
        store.loadDictionary(filename)
        
        # test if order by stroke is correct
        rows = list(store.data)
        rows.sort(lambda a, b: cmp(b[Store.ATTR_STROKE], a[Store.ATTR_STROKE]), reverse=True)
        store.sort(Store.ATTR_STROKE, True)
        self.assertEqual(store.rows, rows)
        
        # test if reset order is equal to original
        rows = list(store.data)
        store.sort(Store.ATTR_STROKE, True)
        store.sort()
        self.assertEqual(store.rows, rows)
    
    def test_sort_with_filter(self):
        filename = os.path.join(conf.ASSETS_DIR, "test.json")
        store = Store(conf.get_config())
        store.loadDictionary(filename)
        
        store.filter({Store.ATTR_TRANSLATION: "c"})
        self.assertTrue(len(store.rows) > 0)
        self.assertEqual(store.rows[0].get(Store.ATTR_TRANSLATION)[0], "c")
        
if __name__ == '__main__':
    unittest.main()