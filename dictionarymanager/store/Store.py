"""

Store class can read and write dictionaries

"""

from dictionarymanager.store.Dictionary import Dictionary
from dictionarymanager.store.JsonLoader import JsonLoader
from dictionarymanager.store.RtfLoader import RtfLoader
import os

class Store():
    
    ATTR_STROKE = "stroke"
    ATTR_TRANSLATION = "translation"
    ATTR_DICTIONARIES = "dictionaries"
    
    def __init__(self):
        self.loaders = {
                        "json": JsonLoader(),
                        "rtf": RtfLoader()
                        }
        self.dictionaries = {}
        self.dictionaryNames = []
        self.dictionaryFilenames = []
        self.strokes = {}
        self.count = 0
        self.rows = []
        self.data = []
        self.filteredRows = []
        
        # filtering
        self.filters = {}
        self.filterFnList = []

        #sorting
        self.cmpFn = None
        
        # subscribers
        self.subscribers = {
                            "insert": [], 
                            "delete": [], 
                            "update": [], 
                            "progress": [], 
                            "dataChange": [], 
                            "tableChange": []
                            }
        
    def getCount(self):
        return len(self.rows)
        
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
    
    def reSort(self):
        if self.cmpFn is not None:
            self._sort()
    
    def resetOrder(self):
        self.cmpFn = None
        identifiers = {}
        rows = []
        for filename in self.dictionaryFilenames:
            for stroke, translation in self.dictionaries[filename].iteritems():
                identifier = self.getIdentifier(stroke, translation)
                if identifier not in identifiers:
                    identifiers[identifier] = True
                    rows.append(self.strokes.get(identifier))
        self.data = rows
        self._applyFilter()
    
    def _sort(self):
        if self.cmpFn is not None:
            self.data.sort(cmp=self.cmpFn)
            self._applyFilter()
        else:
            self.resetOrder()
        
    def _insertItem(self, item):
        self.strokes[self.getIdentifier(item[self.ATTR_STROKE], item[self.ATTR_TRANSLATION])] = item
        self.rows.insert(0, item)
        self.data.insert(0, item)
        self.fireEvent("tableChange", self)
        return 0
        
    def _removeItem(self, index):
        item = self.rows[index]
        self.strokes.pop(self.getIdentifier(item[self.ATTR_STROKE], item[self.ATTR_TRANSLATION]), None)
        self.rows.pop(index)
        self.fireEvent("tableChange", self)
        return index
        
    def findPlaceForNewItem(self, item, start, end):
        if self.cmpFn is None:
            return end + 1
        
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
        if filters is None:
            filters = self.filterFnList
        return not (False in [f(row) for f in filters])
    
    def filter(self, newFilters):
        if len(self.filters.keys()) == len(newFilters.keys()) and not False in [True if c in self.filters and self.filters[c] == p else False for c, p in newFilters.iteritems()]:
            return;
        
        self.filters = newFilters
        self.filterFnList = []
        for c, p in self.filters.iteritems():
            t = None
            if len(p) > 0:
                if c == self.ATTR_DICTIONARIES:
                    t = lambda pattern, column: (lambda value: (True in [False if i in pattern else True for i in value[column]]))
                else:
                    t = lambda pattern, column: (lambda value: (pattern in value[column]))
            if t is not None:
                self.filterFnList.append(t(p, c))
        
        # apply new filter
        self._applyFilter()
        
    def _applyFilter(self):
        self.rows = []
        for index in range(len(self.data)):
            item = self.data[index]
            if self.filterFn(item):
                self.rows.append(item)
            
        self.fireEvent("tableChange", self)
        
    def loadDictionary(self, filename):
        """ Load dictionary from file """
        
        loader = self.getLoader(filename)
        if loader is not None:
            dictionary = Dictionary()
            if dictionary.load(filename, loader):
                self.dictionaries[filename] = dictionary
                self.dictionaryFilenames.append(filename)
                self.dictionaryNames.append(self.getDictionaryShortName(filename))
                
                # precache indexes for identifiers
                indexes = {}
                for index, row in enumerate(self.rows):
                    indexes[self.getIdentifier(row[self.ATTR_STROKE], row[self.ATTR_TRANSLATION])] = index
                
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
                    if isNew:
                        if self.filterFn(item):
                            self.rows.append(item)
                        self.data.append(item)
                    
                self.fireEvent("tableChange", self)

    def saveDictionaries(self):
        """ Save dictionaries to files """
        
        for index in range(len(self.dictionaries.keys())):
            self.saveDictionary(index)
    
    def saveDictionary(self, index, dest = None):
        """ Save dictionary to file """
        
        if index < len(self.dictionaries):
            filename = self.dictionaryFilenames[index]
            if dest is None:
                dest = filename
            loader = self.getLoader(dest)
            if loader is not None:
                self.dictionaries[filename].write(dest, loader)
    
    def closeDictionary(self, index):
        """ Close dictionary """
        
        filename = self.dictionaryFilenames[index]
        for i in reversed(range(len(self.data))):
            row = self.data[i]
            if filename in row[self.ATTR_DICTIONARIES]:
                row[self.ATTR_DICTIONARIES].remove(filename)
                if len(row[self.ATTR_DICTIONARIES]) == 0:
                    self.data.pop(i)
                    if self.filterFn(row):
                        self.rows.remove(row)
                    self.strokes.pop(self.getIdentifier(row[self.ATTR_STROKE], row[self.ATTR_TRANSLATION]), None)
                #else:
                # TODO: maybe here we should reposition the row
        self.dictionaries.pop(filename, None)
        self.dictionaryFilenames.remove(filename)
        self.dictionaryNames.remove(self.getDictionaryShortName(filename))
        if self.ATTR_DICTIONARIES in self.filters and filename in self.filters[self.ATTR_DICTIONARIES]:
            self.filters[self.ATTR_DICTIONARIES].remove(filename)
        self.fireEvent("tableChange", self)
    
    def toggleDictionaryVisibility(self, index):
        """ Show/Hide dictionary (apply dictionary filter) """
        
        filters = {}
        dictFilter = []
        for c, p in self.filters.iteritems():
            if c == self.ATTR_DICTIONARIES:
                dictFilter.extend(p)
            filters[c] = p
        
        name = self.dictionaryFilenames[index]
        if name in dictFilter:
            dictFilter.remove(name)
        else:
            dictFilter.append(name)
        filters[self.ATTR_DICTIONARIES] = dictFilter
        self.filter(filters)
    
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
    
    def changeStroke(self, row, stroke):
        """ Change Stroke in item """
        
        item = self.rows[row]
        orig = item[self.ATTR_STROKE]
        item[self.ATTR_STROKE] = stroke
        # update strokes cache
        self.strokes[self.getIdentifier(stroke, item[self.ATTR_TRANSLATION])] = self.strokes.pop(self.getIdentifier(orig, item[self.ATTR_TRANSLATION]))
        for filename in item[self.ATTR_DICTIONARIES]:
            self.dictionaries[filename].change(orig, item[self.ATTR_TRANSLATION], item[self.ATTR_STROKE], item[self.ATTR_TRANSLATION])
            self.fireEvent("dataChange", self.getDictionaryIndexByName(filename))
        
    def changeTranslation(self, row, translation):
        """ Change Translation in item """
        
        item = self.rows[row]
        orig = item[self.ATTR_TRANSLATION]
        item[self.ATTR_TRANSLATION] = translation
        # update strokes cache
        self.strokes[self.getIdentifier(item[self.ATTR_STROKE], translation)] = self.strokes.pop(self.getIdentifier(item[self.ATTR_STROKE], orig))
        for filename in item[self.ATTR_DICTIONARIES]:
            self.dictionaries[filename].change(item[self.ATTR_STROKE], orig, item[self.ATTR_STROKE], item[self.ATTR_TRANSLATION])
            self.fireEvent("dataChange", self.getDictionaryIndexByName(filename))
        
    def changeDictionaries(self, row, dictionaries):
        """ Change dictionary list for the item """
        
        item = self.rows[row]
        item[self.ATTR_DICTIONARIES] = dictionaries
        # dataChange event already fired
    
    def insertItem(self, item = None):
        if item is None:
            item = {self.ATTR_STROKE: "", self.ATTR_TRANSLATION: "", self.ATTR_DICTIONARIES: []}
        return self._insertItem(item)
    
    def getDictionaryNames(self):
        return self.dictionaryNames
    
    def getDictionaryShortName(self, path):
        return path.split("/")[-1]
        
    def getDictionariesForRow(self, row):
        return self.rows[row][self.ATTR_DICTIONARIES]
    
    def getDictionaryShortNamesForRow(self, row):
        return map(self.getDictionaryShortName, self.rows[row][self.ATTR_DICTIONARIES])
    
    def renderDictionaries(self, item):
        return ", ".join(map(self.getDictionaryShortName, item[self.ATTR_DICTIONARIES]))
    
    def renderDictionariesForRow(self, row):
        return self.renderDictionaries(self.rows[row])
    
    def getDictionaryIndexesForRow(self, row):
        return map(self.getDictionaryIndexByName, self.rows[row][self.ATTR_DICTIONARIES])
    
    def setDictionariesForRow(self, row, indexes):
        item = self.rows[row]
        before = item[self.ATTR_DICTIONARIES]
        dictionaries = map(self.getDictionaryNameByIndex, indexes)
        item[self.ATTR_DICTIONARIES] = dictionaries
        removed = list(set(before) - set(dictionaries))
        for filename in removed:
            self.dictionaries[filename].remove(item[self.ATTR_STROKE], item[self.ATTR_TRANSLATION])
            self.fireEvent("dataChange", self.getDictionaryIndexByName(filename))
        added = list(set(dictionaries) - set(before))
        for filename in added:
            self.dictionaries[filename].insert(item[self.ATTR_STROKE], item[self.ATTR_TRANSLATION])
            self.fireEvent("dataChange", self.getDictionaryIndexByName(filename))
        
    def getDictionaryIndexByName(self, name):
        if name in self.dictionaryFilenames:
            return self.dictionaryFilenames.index(name)
        return None
    
    def getDictionaryNameByIndex(self, index):
        if index < len(self.dictionaryFilenames):
            return self.dictionaryFilenames[index]
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
        