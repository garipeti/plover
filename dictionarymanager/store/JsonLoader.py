from dictionarymanager.store.DictionaryLoader import DictionaryLoader
import collections
import json
import re

class JsonLoader(DictionaryLoader):
    """JSON file format loader."""
    
    FORMAT_PATTERN = re.compile("^([\\s\\t]*)\"[^\"]*\"([\\s\\t]*):([\\s\\t]*)\"[^\"]*\"([\\s\\t]*),([\\s\\t]*)$")
    
    def __init__(self):
        DictionaryLoader.__init__(self)
        
    def load(self, filename):
        """Decode JSON into dictionary."""
        (s, conf) = DictionaryLoader.load(self, filename)
        if s is not None:
            conf = self.getFormat(s, conf)
            try:
                l = self.parse(s)
            except UnicodeDecodeError:
                l = self.parse(s, "latin-1")
        return (l, conf)
    
    def parse(self, s, encoding = None):
        return json.loads(s, encoding, object_pairs_hook=collections.OrderedDict)
    
    def write(self, filename, dictionary, conf = None):
        """Encode dictionary to JSON."""
        conf = conf if type(conf) is dict else {}
        DictionaryLoader.write(self, 
                               filename, 
                               json.dumps(dictionary, indent = conf.get("indent"), separators = conf.get("separators")),
                               conf
                               )
        
    def getFormat(self, s, conf):
        """ Get specific file format. """
        if s is not None:
            i = 0
            for line in s.splitlines():
                match = self.FORMAT_PATTERN.match(line)
                if match:
                    conf = conf if conf is not None else {}
                    conf["indent"] = len(match.group(1))
                    conf["separators"] = (match.group(4) + "," + match.group(5),  match.group(2) + ":" + match.group(3))
                    break
                i += 1
                if i > 10:
                    break
        return conf