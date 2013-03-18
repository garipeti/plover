from dictionarymanager.store.DictionaryLoader import DictionaryLoader
import json

class JsonLoader(DictionaryLoader):
    """JSON file format loader."""
    
    def __init__(self):
        DictionaryLoader.__init__(self)
        
    def load(self, filename):
        """Decode JSON to dictionary."""
        s = DictionaryLoader.load(self, filename)
        if s != None:
            try:
                return json.loads(s)
            except UnicodeDecodeError:
                return json.loads(s, "latin-1")
        return s
    
    def write(self, filename, dictionary):
        """Encode dictionary to JSON."""
        DictionaryLoader.write(self, filename, json.dumps(dictionary))
        