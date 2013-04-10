"""

Store class can read and write dictionaries

"""

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
        self.filteredRows = []
        
        # filtering
        self.filters = {}
        self.filterFnList = []

        #sorting
        self.cmpFn = lambda a, b: 0 if a[self.ATTR_STROKE] == b[self.ATTR_STROKE] else 1 if a[self.ATTR_STROKE] > b[self.ATTR_STROKE] else -1
        
        # subscribers
        self.subscribers = {"insert": [], "delete": [], "update": [], "progress": [], "dataChange": []}
        
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
        if index is None and item in self.rows:
            index = self.rows.index(item)
        if index is not None:
            self.fireEvent("delete", item, index)
            self.filteredRows.append(self.rows.pop(index))
    
    def showItem(self, item, currentIndex = None):
        if currentIndex is None:
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
        
    def _removeItem(self, index):
        item = self.rows[index]
        self.strokes.pop(self.getIdentifier(item[self.ATTR_STROKE], item[self.ATTR_TRANSLATION]), None)
        self.rows.pop(index)
        self.fireEvent("delete", item, index)
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
        if filters is None:
            filters = self.filterFnList
        return not (False in [f(row) for f in filters])
    
    def filter(self, newFilters):
        if len(self.filters.keys()) == len(newFilters.keys()) and not False in [True if c in self.filters and self.filters[c] == p else False for c, p in newFilters.iteritems()]:
            return;
        
        oldFilterFnList = self.filterFnList
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
        filtered = self.filteredRows[:]
        for index in range(len(self.rows)-1, -1, -1):
            item = self.rows[index]
            did = self.filterFn(item, oldFilterFnList)
            does = self.filterFn(item)
            if not does and did:
                self.hideItem(item, index)
            
        for index in range(len(filtered)-1, -1, -1):
            item = filtered[index]
            did = self.filterFn(item, oldFilterFnList)
            does = self.filterFn(item)
            if does and not did:
                self.showItem(item, index)
        
    def loadDictionary(self, filename):
        """ Load dictionary from file """
        
        loader = self.getLoader(filename)
        if loader is not None:
            dictionary = loader.load(filename)
            if dictionary is not None:
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
            if loader is not None:
                loader.write(filename, dictionary)
    
    def saveDictionary(self, index):
        """ Save dictionary to file """
        
        data = {}
        filename = self.dictionaryFilenames[index]
        for item in self.strokes.itervalues():
            if filename in item[self.ATTR_DICTIONARIES]:
                data[item[self.ATTR_STROKE]] = item[self.ATTR_TRANSLATION]
        loader = self.getLoader(filename)
        if loader is not None:
            loader.write(filename, data)
    
    def closeDictionary(self, index):
        """ Close dictionary """
        
        filename = self.dictionaryFilenames[index]
        for i in reversed(range(len(self.rows))):
            row = self.rows[i]
            if filename in row[self.ATTR_DICTIONARIES]:
                row[self.ATTR_DICTIONARIES].remove(filename)
                if len(row[self.ATTR_DICTIONARIES]) == 0:
                    self._removeItem(i)
                else:
                    # TODO: maybe here we should reposition the row
                    self.fireEvent("update", row, i)
        for i in reversed(range(len(self.filteredRows))):
            row = self.filteredRows[i]
            if filename in row[self.ATTR_DICTIONARIES]:
                row[self.ATTR_DICTIONARIES].remove(filename)
                if len(row[self.ATTR_DICTIONARIES]) == 0:
                    self.strokes.pop(self.getIdentifier(row[self.ATTR_STROKE], row[self.ATTR_TRANSLATION]), None)
                    self.filteredRows.pop(i)
        self.dictionaries.pop(filename, None)
        self.dictionaryFilenames.remove(filename)
        self.dictionaryNames.remove(self.getDictionaryShortName(filename))
        if self.ATTR_DICTIONARIES in self.filters and filename in self.filters[self.ATTR_DICTIONARIES]:
            self.filters[self.ATTR_DICTIONARIES].remove(filename)
    
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
    
    def findItem(self, column, pattern, index):
        """ Find next item which matches in the given attribute """
        
        if index is None or index < 0:
            index = 0
        for i in range(index, self.count):
            if pattern in self.rows[i][column]:
                return i
        return -1
    
    def changeStroke(self, row, stroke):
        """ Change Stroke in item """
        
        item = self.rows[row]
        item[self.ATTR_STROKE] = stroke
        for filename in item[self.ATTR_DICTIONARIES]:
            self.fireEvent("dataChange", self.getDictionaryIndexByName(filename))
        return self.repositionItem(item)
        
    def changeTranslation(self, row, translation):
        """ Change Translation in item """
        
        item = self.rows[row]
        item[self.ATTR_TRANSLATION] = translation
        for filename in item[self.ATTR_DICTIONARIES]:
            self.fireEvent("dataChange", self.getDictionaryIndexByName(filename))
        return self.repositionItem(item)
        
    def changeDictionaries(self, row, dictionaries):
        """ Change dictionary list for the item """
        
        item = self.rows[row]
        item[self.ATTR_DICTIONARIES] = dictionaries
        return self.repositionItem(item)
    
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
        changed = list(set(before) - set(dictionaries))
        changed.extend(list(set(dictionaries) - set(before)))
        for filename in changed:
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
        