
from _abcoll import Mapping
import collections

class Dictionary(Mapping):
    """Dictionary class"""
    
    def __init__(self):
        self.filename = None
        self.data = collections.OrderedDict()
        self.conf = None
        self.inserted = collections.OrderedDict()
        self.changed = collections.OrderedDict()
        self.removed = collections.OrderedDict()
        self.actual = collections.OrderedDict()
        
    def load(self, filename, loader):
        """ Loads a dictionary from the given file with the given loader. """
        
        data, conf = loader.load(filename)
        if data is not None:
            self.data = data
            self.conf = conf
            self.applyChanges()
            return True
        return False
    
    def write(self, dest, loader):
        """ Writes this dictionary to the given file with the given loader. """
        
        loader.write(dest, self.actual, self.conf)
    
    def applyChanges(self):
        """ Apply changes to the dictionary and return the generated dictionary. """
        
        data = collections.OrderedDict()
        for stroke, translation in self.data.iteritems():
            if self.createIdentifier(stroke, translation) in self.removed:
                continue
            # apply changes
            while self.createIdentifier(stroke, translation) in self.changed:
                stroke, translation = self.changed[self.createIdentifier(stroke, translation)]
            data[stroke] = translation
        for stroke, translation in self.inserted.values():
            data[stroke] = translation
        self.actual = data
        return self.actual
            
    def iteritems(self):
        return self.actual.iteritems()
    
    def __iter__(self):
        return self.actual.__iter__()
    
    def __len__(self):
        return self.actual.__len__()
        
    def __getitem__(self, key):
        return self.actual.__getitem__(key)

    def __setitem__(self, key, value):
        self.actual.__setitem__(key, value)

    def __delitem__(self, key):
        self.actual.__delitem__(key)
    
    def __contains__(self, key):
        return self.actual.__contains__(key)

    def iterkeys(self):
        return self.actual.iterkeys()

    def itervalues(self):
        return self.actual.itervalues()
        
    def keys(self):
        return self.actual.keys()

    # do not remove items from dict to keep order
    def remove(self, stroke, translation):
        """ Remove an entry from the dictionary. """
        
        # if this is in inserted list then just remove from it
        identifier = self.createIdentifier(stroke, translation)
        if identifier in self.inserted:
            self.inserted.pop(identifier)
        else:
            for key, value in self.changed.iteritems():
                if value == (stroke, translation):
                    self.changed.pop(key)
                    self.removed[key] = self.parseIdentifier(key)
                    break
            else:
                self.removed[identifier] = (stroke, translation)
                    
        self.applyChanges()
    
    def insert(self, stroke, translation):
        """ Insert a new entry to the dictionary. """
        
        # if this is in removed list then just remove from it
        identifier = self.createIdentifier(stroke, translation)
        if identifier in self.removed:
            self.removed.pop(identifier)
        else:
            self.inserted[identifier] = (stroke, translation)
        self.applyChanges()
        
    def change(self, originalStroke, originalTranslation, stroke, translation):
        """ Change an entry in the dictionary. """
        
        if self.inserted.pop(self.createIdentifier(originalStroke, originalTranslation), None) is not None:
            self.inserted[self.createIdentifier(stroke, translation)] = (stroke, translation)
        else:
            for key in self.changed.keys():
                if self.changed[key] == (originalStroke, originalTranslation):
                    if self.createIdentifier(stroke, translation) == key:
                        self.changed.pop(key)
                    else:
                        self.changed[key] = (stroke, translation)
                    break
            else:
                self.changed[self.createIdentifier(originalStroke, originalTranslation)] = (stroke, translation)
        self.applyChanges()
        
    def hasChanges(self):
        return len(self.inserted) > 0 or len(self.changed) > 0 or len(self.removed) > 0

    def createIdentifier(self, stroke, translation):
        return "__|__" + stroke + "__|__" + translation + "__|__"
        
    def parseIdentifier(self, identifier):
        values = identifier.split("__|__")
        if len(values) != 4:
            raise Exception
        return (values[1], values[2])
