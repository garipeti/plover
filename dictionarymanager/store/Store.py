"""

Store class can read and write dictionaries

"""

from dictionarymanager.store import JsonLoader
import os

class Store():
    
    def __init__(self):
        self.loaders = {
                        "json": JsonLoader.JsonLoader()
                        }
        self.dictionaries = {}
        self.dictionaryNames = []
        self.dictionaryFilenames = []
        self.strokes = {}
        self.count = 0
        self.rows = []
        self.filteredRows = []
        
        # filtering
        self.filters = []

        #sorting
        self.cmpFn = lambda a, b: 0 if a["stroke"] == b["stroke"] else 1 if a["stroke"] > b["stroke"] else -1
        
        # subscribers
        self.subscribers = {"insert": [], "delete": [], "update": [], "progress": []}
        
    def getCount(self):
        return self.count
        
    def subscribe(self, event, callback):
        self.subscribers[event].append(callback)
    
    def unsubscribe(self, event, callback):
        if callback in self.subscribers[event]:
            self.subscribers[event].remove(callback)
    
    def fireEvent(self, event, *args, **kwargs):
        for callback in self.subscribers[event]:
            callback(*args, **kwargs)
            
    def sort(self, column, reverse):
        if reverse:
            self.cmpFn = lambda a, b: 0 if a["stroke"] == b["stroke"] else 1 if a["stroke"] > b["stroke"] else -1
        else:
            self.cmpFn = lambda a, b: 0 if a["stroke"] == b["stroke"] else 1 if a["stroke"] < b["stroke"] else -1
        self._sort()
    
    def _sort(self):
        index = 0
        for row in self.rows:
            if self.filterFn(row):
                self.fireEvent("delete", row, index)
                index += 1
        self.rows.sort(cmp=self.cmpFn)
        index = 0
        for row in self.rows:
            if self.filterFn(row):
                self.fireEvent("insert", row, index)
                index += 1
        
    def hideItem(self, item, index = None):
        if index == None and item in self.rows:
            index = self.rows.index(item)
        if index != None:
            self.fireEvent("delete", item, index)
            self.filteredRows.append(self.rows.pop(index))
    
    def showItem(self, item, currentIndex = None):
        if currentIndex == None:
            currentIndex = self.filteredRows.index(item)
        pos = self.findPlaceForNewItem(item, 0, len(self.rows)-1)
        self.rows.insert(pos, self.filteredRows.pop(currentIndex))
        self.fireEvent("insert", item, pos)
        
    def repositionItem(self, item):
        self.hideItem(item)
        self.showItem(item)
    
    def findPlaceForNewItem(self, item, start, end):
        if start > end:
            return start
        middle = (start + end) / 2
        cmpd = self.cmpFn(self.rows[middle], item)
        if cmpd > 0:
            return self.findPlaceForNewItem(item, start, middle-1)
        elif cmpd < 0:
            return self.findPlaceForNewItem(item, middle+1, end)
        else:
            return self.findPlaceForNewItem(item, middle+1, end)
    
    def filterFn(self, row, filters = None):
        if filters == None:
            filters = self.filters
        return not (False in [(filter["pattern"] in row[filter["column"]]) for filter in filters])
    
    def filter(self, newFilters):
        oldFilters = self.filters
        self.filters = newFilters
        
        progress = Progress(len(self.rows) + len(self.filteredRows))
        
        # apply new filter
        for index in range(len(self.rows)-1, -1, -1):
            item = self.rows[index]
            did = self.filterFn(item, oldFilters)
            does = self.filterFn(item, self.filters)
            if not does and did:
                self.hideItem(item, index)
            
            current = progress.next()
            if current != None:
                self.fireEvent("progress", current)
                
        for index in range(len(self.filteredRows)-1, -1, -1):
            item = self.filteredRows[index]
            did = self.filterFn(item, oldFilters)
            does = self.filterFn(item, self.filters)
            if does and not did:
                self.showItem(item, index)
            
            current = progress.next()
            if current != None:
                self.fireEvent("progress", current)
        
    def loadDictionary(self, filename):
        """ Load dictionary from file """
        
        loader = self.getLoader(filename)
        if loader != None:
            dictionary = loader.load(filename)
            if dictionary != None:
                self.dictionaries[filename] = dictionary
                self.dictionaryFilenames.append(filename)
                self.dictionaryNames.append(self.getDictionaryShortName(filename))
                
                # precache indexes for identifiers
                indexes = {}
                for index, row in enumerate(self.rows):
                    indexes[self.getIdentifier(row["stroke"], row["translation"])] = index
                
                newItems = []
                progress = Progress(len(dictionary))
                current = None
                for stroke, translation in dictionary.iteritems():
                    identifier = self.getIdentifier(stroke, translation)
                    isNew = identifier not in self.strokes
                    if isNew:
                        item = {"stroke": stroke, "translation": translation, "dictionaries": []}
                        self.strokes[identifier] = item
                    else:
                        item = self.strokes[identifier]
                        
                    item["dictionaries"].append(filename)
                    
                    # we don't handle the situation when this is an update 
                    # and the row is filtered out with its new value
                    if self.filterFn(item):
                        if isNew:
                            newItems.append(item)
                        else:
                            current = progress.next()
                            self.fireEvent("update", item, indexes[identifier])
                    elif isNew:
                            current = progress.next()
                            self.filteredRows.append(item)
                    
                    if current != None:
                        self.fireEvent("progress", current)
                        current = None
                    
                for item in newItems:
                    index = self.findPlaceForNewItem(item, 0, len(self.rows)-1)
                    self.rows.insert(index, item)
                    self.fireEvent("insert", item, index)
                    current = progress.next()
                    if current != None:
                        self.fireEvent("progress", current)
                        current = None

    def saveDictionaries(self):
        """ Save dictionaries to files """
        
        files = {}
        for filename in self.dictionaries.iterkeys():
            files[filename] = {}
        for item in self.strokes.itervalues():
            for filename in item["dictionaries"]:
                files[filename][item["stroke"]] = item["translation"]
        for filename, dictionary in files.iteritems():
            loader = self.getLoader(filename)
            if loader != None:
                loader.write(filename, dictionary)
    
    def getLoader(self, filename):
        """ Get the loader based on the file extension """
        
        extension = os.path.splitext(filename)[1][1:]
        if extension in self.loaders:
            return self.loaders[extension]
        return None
    
    def getIdentifier(self, stroke, translation):
        """ Generate a unique identifier """
        return "__ID__" + stroke + "___SEP___" + translation
    
    def setFilter(self, filterFn):
        self.filterFn = filterFn
    
    def findItem(self, column, pattern, index):
        """ Find next item which matches in the given attribute """
        
        if index == None or index < 0:
            index = 0
        for i in range(index, self.count):
            if pattern in self.rows[i][column]:
                return i
        return -1
    
    def changeStroke(self, row, stroke):
        """ Change Stroke in item """
        
        item = self.rows[row]
        item["stroke"] = stroke
        self.repositionItem(item)
        
    def changeTranslation(self, row, translation):
        """ Change Translation in item """
        
        item = self.rows[row]
        item["translation"] = translation
        self.repositionItem(item)
        
    def changeDictionaries(self, row, dictionaries):
        """ Change dictionary list for the item """
        
        item = self.rows[row]
        item["dictionaries"] = self.indexStringToDictionaryList(dictionaries)
        self.repositionItem(item)
    
    def getDictionaryNames(self):
        return self.dictionaryNames
    
    def getDictionaryShortName(self, path):
        return path.split("/")[-1]
        
    def dictionaryFilenameListToIndexString(self, filenames):
        return self.indexListToIndexString(map(self.getDictionaryIndexByName, filenames))
        
    def indexStringToDictionaryFilenameString(self, indexes):
        return ", ".join(map(self.getDictionaryShortNameByIndex, self.indexStringToIndexList(indexes)))
        
    def indexStringToDictionaryList(self, indexes):
        return map(self.getDictionaryNameByIndex, self.indexStringToIndexList(indexes))
        
    def indexStringToIndexList(self, indexes):
        if len(indexes) > 7:
            return map(int, indexes[7:].split(","))
        return []
        
    def indexListToIndexString(self, indexes):
        return "__dic__" + (",".join(map(str, indexes)))
    
    def getDictionaryShortNameByIndex(self, index):
        if index < len(self.dictionaryNames):
            return self.dictionaryNames[index]
        return ""
    
    def getDictionaryNameByIndex(self, index):
        if index < len(self.dictionaryFilenames):
            return self.dictionaryFilenames[index]
        return None
    
    def getDictionaryIndexByName(self, name):
        if name in self.dictionaryFilenames:
            return str(self.dictionaryFilenames.index(name))
        return None
    
    def getDictionaryIndexByShortName(self, name):
        if self.getDictionaryShortName(name) in self.dictionaryNames:
            return self.dictionaryNames.index(name)
        return None
    
class Progress():
    def __init__(self, length):
        self.length = length
        self.loaded = 0
        self.onePercent = length / 100
        self.nextPercent = self.onePercent
        self.progress = 0
        
    def next(self):
        self.loaded += 1
        if self.loaded > self.nextPercent:
            self.nextPercent += self.onePercent
            self.progress += 1
            return self.progress
        return None
        