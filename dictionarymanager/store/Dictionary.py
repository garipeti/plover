import collections

class Dictionary():
    """Dictionary class"""
    
    def __init__(self):
        self.filename = None
        self.data = {}
        self.conf = None
        self.inserted = []
        self.changed = collections.OrderedDict()
        self.removed = collections.OrderedDict()
        
    def load(self, filename, loader):
        data, conf = loader.load(filename)
        if data is not None:
            self.data = data
            self.conf = conf
            return True
        return False
    
    def write(self, dest, loader):
        loader.write(dest, self.applyChanges(), self.conf)
    
    def applyChanges(self):
        data = collections.OrderedDict()
        for stroke, translation in self.data.iteritems():
            if self.createIdentifier(stroke, translation) in self.removed:
                continue
            # apply changes
            while self.createIdentifier(stroke, translation) in self.changed:
                change = self.changed[self.createIdentifier(stroke, translation)]
                stroke = change[0]
                translation = change[1]
            data[stroke] = translation
        for item in self.inserted:
            data[item[0]] = item[1]
        return data
            
    def iteritems(self):
        data = self.applyChanges()
        return data.iteritems()
    
    # do not remove items from dict to keep order
    def remove(self, stroke, translation):
        # if this is in inserted list then just remove from it
        for index in range(len(self.inserted)):
            item = self.inserted[index]
            if item[0] == stroke and item[1] == translation:
                self.inserted.pop(index)
                break
        else:
            self.removed[self.createIdentifier(stroke, translation)] = [stroke, translation]
    
    def insert(self, stroke, translation):
        # if this is in removed list then just remove from it
        if self.createIdentifier(stroke, translation) in self.removed:
            self.removed.pop(self.createIdentifier(stroke, translation))
        else:
            self.inserted.append([stroke, translation])
        
    def change(self, originalStroke, originalTranslation, stroke, translation):
        self.changed[self.createIdentifier(originalStroke, originalTranslation)] = [stroke, translation]

    def createIdentifier(self, stroke, translation):
        return "__" + stroke + "__" + translation + "__"
        