"""

Store class can read and write dictionaries

"""

from dictionarymanager.store import JsonLoader
import os

class Store():
    
    ATTR_STROKE = "stroke"
    ATTR_TRANSLATION = "translation"
    ATTR_DICTIONARIES = "dictionaries"
    
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
        self.cmpFn = lambda a, b: 0 if a[self.ATTR_STROKE] == b[self.ATTR_STROKE] else 1 if a[self.ATTR_STROKE] > b[self.ATTR_STROKE] else -1
        
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
            self.cmpFn = lambda a, b: 0 if a[column] == b[column] else 1 if a[column] > b[column] else -1
        else:
            self.cmpFn = lambda a, b: 0 if a[column] == b[column] else 1 if a[column] < b[column] else -1
        self._sort()
    
    def _sort(self):
        progress = Progress(len(self.rows)*2, self.fireEvent)
        for row in self.rows:
            progress.next()
            if self.filterFn(row):
                self.fireEvent("delete", row, 0)
        self.rows.sort(cmp=self.cmpFn)
        index = 0
        for row in self.rows:
            progress.next()
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
        return pos
    
    def _insertItem(self, item):
        index = self.findPlaceForNewItem(item, 0, len(self.rows)-1)
        self.strokes[self.getIdentifier(item[self.ATTR_STROKE], item[self.ATTR_TRANSLATION])] = item
        self.rows.insert(index, item)
        self.fireEvent("insert", item, index)
        return index
        
    def repositionItem(self, item):
        self.hideItem(item)
        if self.filterFn(item):
            return self.showItem(item)
        return None
    
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
        if not False in [True if f in self.filters else False for f in newFilters]:
            return;
        
        oldFilters = self.filters
        self.filters = newFilters
        
        #progress = Progress(len(self.rows) + len(self.filteredRows), self.fireEvent)
        
        # apply new filter
        filtered = self.filteredRows[:]
        for index in range(len(self.rows)-1, -1, -1):
            item = self.rows[index]
            did = self.filterFn(item, oldFilters)
            does = self.filterFn(item, self.filters)
            if not does and did:
                self.hideItem(item, index)
            
            #progress.next()
            
        for index in range(len(filtered)-1, -1, -1):
            item = filtered[index]
            did = self.filterFn(item, oldFilters)
            does = self.filterFn(item, self.filters)
            if does and not did:
                self.showItem(item, index)
            
            #progress.next()
        
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
                    indexes[self.getIdentifier(row[self.ATTR_STROKE], row[self.ATTR_TRANSLATION])] = index
                
                newItems = []
                progress = Progress(len(dictionary), self.fireEvent)
                for stroke, translation in dictionary.iteritems():
                    identifier = self.getIdentifier(stroke, translation)
                    isNew = identifier not in self.strokes
                    if isNew:
                        item = {self.ATTR_STROKE: stroke, self.ATTR_TRANSLATION: translation, self.ATTR_DICTIONARIES: []}
                        self.strokes[identifier] = item
                    else:
                        item = self.strokes[identifier]
                        
                    item[self.ATTR_DICTIONARIES].append(filename)
                    
                    # we don't handle the situation when this is an update 
                    # and the row is filtered out with its new value
                    if self.filterFn(item):
                        if isNew:
                            newItems.append(item)
                        else:
                            progress.next()
                            self.fireEvent("update", item, indexes[identifier])
                    elif isNew:
                            progress.next()
                            self.filteredRows.append(item)
                    
                for item in newItems:
                    self._insertItem(item)
                    progress.next()

    def saveDictionaries(self):
        """ Save dictionaries to files """
        
        files = {}
        for filename in self.dictionaries.iterkeys():
            files[filename] = {}
        for item in self.strokes.itervalues():
            for filename in item[self.ATTR_DICTIONARIES]:
                files[filename][item[self.ATTR_STROKE]] = item[self.ATTR_TRANSLATION]
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
        item[self.ATTR_STROKE] = stroke
        return self.repositionItem(item)
        
    def changeTranslation(self, row, translation):
        """ Change Translation in item """
        
        item = self.rows[row]
        item[self.ATTR_TRANSLATION] = translation
        return self.repositionItem(item)
        
    def changeDictionaries(self, row, dictionaries):
        """ Change dictionary list for the item """
        
        item = self.rows[row]
        item[self.ATTR_DICTIONARIES] = self.indexStringToDictionaryList(dictionaries)
        return self.repositionItem(item)
    
    def insertItem(self, item = None):
        if item == None:
            item = {self.ATTR_STROKE: "", self.ATTR_TRANSLATION: "", self.ATTR_DICTIONARIES: []}
        return self._insertItem(item)
    
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
    def __init__(self, length, fireEvent):
        self.length = length
        self.loaded = 0
        self.onePercent = length / 100
        self.nextPercent = self.onePercent
        self.progress = 0
        self.fireEvent = fireEvent
        
    def next(self):
        self.loaded += 1
        if self.loaded > self.nextPercent:
            self.nextPercent += self.onePercent
            self.progress += 1
            self.fireEvent("progress", self.progress)
            return self.progress
        return None
        