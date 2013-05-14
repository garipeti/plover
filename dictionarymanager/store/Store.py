"""

Store class can read and write dictionaries

"""

from dictionarymanager.store.Dictionary import Dictionary
from dictionarymanager.store.JsonLoader import JsonLoader
from dictionarymanager.store.RtfLoader import RtfLoader
from plover.steno import normalize_steno
from plover.steno_dictionary import StenoDictionary
import collections
import os
import plover.config as conf

class Store():
    
    ATTR_STROKE = "stroke"
    ATTR_TRANSLATION = "translation"
    ATTR_DICTIONARIES = "dictionaries"
    
    def __init__(self, config):
        self.config = config
        self.loaders = {
                        "json": JsonLoader(),
                        "rtf": RtfLoader()
                        }
        self.dictionaries = collections.OrderedDict()
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
        self.sortColumn = None
        
        # custom events
        self.subscribers = {
                            "insert": [], 
                            "delete": [], 
                            "update": [], 
                            "progress": [], 
                            "dataChange": [], 
                            "tableChange": [],
                            "dictionaryChange": [],
                            "dictionaryLoaded": [],
                            "dictionaryClosed": []
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
            
    def sort(self, column = None, reverse = None):
        """ Sort rows based on the given column and direction. """
        
        self.sortColumn = column
        if column is not None:
            if reverse:
                self.cmpFn = lambda a, b: 0 if a[column] == b[column] else 1 if a[column] > b[column] else -1
            else:
                self.cmpFn = lambda a, b: 0 if a[column] == b[column] else 1 if a[column] < b[column] else -1
        self._sort()
    
    def reSort(self):
        if self.cmpFn is not None:
            self._sort()
    
    def sortByFilter(self):
        """ Sort rows when there is an active filter. """
        
        # if there are filters defined it sorts by the weight of the match
        if self.sortColumn is None:
            if len(self.filterFnList) > 0:
                # calculate the weight of the match
                f = lambda pattern, column: (
                        lambda a: (
                            5 if pattern == a[column] else
                                0 if pattern not in a[column] else
                                    4 if a[column].index(pattern) == 0 else 
                                        1
                        )
                    )
                t = []
                for c, p in self.filters.iteritems():
                    if len(p) > 0:
                        if c != self.ATTR_DICTIONARIES:
                            t.append(f(p, c))
                if len(t) > 0:
                    self.cmpFn = (lambda l: lambda a, b: cmp(sum([x(b) for x in l]), sum([x(a) for x in l])))(t)
                
    def _resetOrder(self):
        """ Remove any sorting and set back the default order. """
        self.sortColumn = None
        identifiers = {}
        self.rows = []
        for filename in self.dictionaryFilenames:
            for stroke, translation in self.dictionaries[filename].iteritems():
                identifier = self.getIdentifier(stroke, translation)
                row = self.strokes.get(identifier)
                if identifier not in identifiers and self.filterFn(row):
                    identifiers[identifier] = True
                    self.rows.append(row)
        self.fireEvent("tableChange", self)
    
    def _sort(self):
        """ Call the proper sorting method """
        if self.sortColumn is not None:
            self.rows.sort(cmp=self.cmpFn)
        elif len(self.filterFnList) > 0:
            self.sortByFilter()
            self.rows.sort(cmp=self.cmpFn)
        else:
            self._resetOrder()
        self.fireEvent("tableChange", self)
        
    def _insertItem(self, item):
        """ Insert a new item. """
        
        self.strokes[self.getIdentifier(item[self.ATTR_STROKE], item[self.ATTR_TRANSLATION])] = item
        self.rows.insert(0, item)
        self.data.append(item)
        self.fireEvent("tableChange", self)
        return 0
        
    def _removeItem(self, index):
        """ Remove an item """
        
        item = self.rows[index]
        self.strokes.pop(self.getIdentifier(item[self.ATTR_STROKE], item[self.ATTR_TRANSLATION]), None)
        self.rows.pop(index)
        self.fireEvent("tableChange", self)
        return index
        
    def findPlaceForNewItem(self, item, start, end):
        """ Deprecated - Find place for a new row based on the current sorting. """
        
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
        """ Filter row """
        
        if filters is None:
            filters = self.filterFnList
        return not (False in [f(row) for f in filters])
    
    def filter(self, newFilters, force = False):
        """ Change filter """
        
        if not force and len(self.filters.keys()) == len(newFilters.keys()) and not False in [True if c in self.filters and self.filters[c] == p else False for c, p in newFilters.iteritems()]:
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
        """ Iterate through all the rows and collect the matching items in rows list. """
        
        self.rows = []
        for index in range(len(self.data)):
            item = self.data[index]
            if self.filterFn(item):
                self.rows.append(item)
        
        self._sort()
        
    def addDictionaryToRecents(self, filename):
        """ Add dictionary filename to recent list if it is not yet there. """
        
        files = conf.get_option_as_set(self.config, conf.DICTIONARY_CONFIG_SECTION, conf.DICTIONARY_LIST_OPTION)
        
        for item in files:
            path = item.split(";")
            shortcut = ""
            if len(path) > 1:
                shortcut = path.pop(-1)
            name = ";".join(path).strip()
            
            if filename == name:
                break
        else:
            files.add(filename)
            conf.set_list_as_option(self.config, conf.DICTIONARY_CONFIG_SECTION, conf.DICTIONARY_LIST_OPTION, files)
            conf.save_config(self.config)
    
    def addDictionaryToActives(self, filename):
        """ Add dictionary filename to active and recent list if necessary. """
        
        # put it to active list
        files = conf.get_option_as_list(self.config, conf.DICTIONARY_CONFIG_SECTION, conf.DICTIONARY_FILE_OPTION)
        if filename not in files:
            files.append(filename)
        conf.set_list_as_option(self.config, conf.DICTIONARY_CONFIG_SECTION, conf.DICTIONARY_FILE_OPTION, files)
        # also put in recent list
        self.addDictionaryToRecents(filename)
    
    def removeDictionaryFromActives(self, filename):
        """ Remove a dictionary filename from active list. """
        
        # remove from loaded list
        files = conf.get_option_as_list(self.config, conf.DICTIONARY_CONFIG_SECTION, conf.DICTIONARY_FILE_OPTION)
        if filename in files:
            files.remove(filename)
            conf.set_list_as_option(self.config, conf.DICTIONARY_CONFIG_SECTION, conf.DICTIONARY_FILE_OPTION, files)
            conf.save_config(self.config)
    
    def toggleDictionary(self, filename):
        """ Load/close a dictionary """
        
        if filename in self.dictionaryFilenames:
            self.closeDictionary(self.dictionaryFilenames.index(filename))
        else:
            self.loadDictionary(filename)
    
    def loadDictionaries(self):
        """ Load all the dictionaries from config """
        
        dict_files = conf.get_option_as_list(self.config, conf.DICTIONARY_CONFIG_SECTION, conf.DICTIONARY_FILE_OPTION)
        for dict_file in dict_files:
            self.loadDictionary(dict_file)
    
    def loadDictionary(self, filename):
        """ Load dictionary from file """
        
        path = os.path.join(conf.CONFIG_DIR, filename) if filename[0] != os.pathsep else filename 
        
        # we already loaded this dictionary
        if filename in self.dictionaryFilenames or path in self.dictionaryFilenames:
            raise ValueError('Dictionary %s already loaded.' % filename)
        
        loader = self.getLoader(path)
        if loader is not None:
            dictionary = Dictionary()
            if dictionary.load(path, loader):
                self.addDictionaryToActives(filename)
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
                self.fireEvent("dictionaryLoaded", filename)
                return True
        else:
            raise ValueError('Unknown dictionary format %s.' % filename)
        
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
                self.fireEvent("dictionaryChange")
    
    def closeDictionary(self, index):
        """ Close dictionary """
        
        filename = self.dictionaryFilenames[index]
        for i in reversed(range(len(self.data))):
            row = self.data[i]
            if filename in row[self.ATTR_DICTIONARIES]:
                row[self.ATTR_DICTIONARIES].remove(filename)
                if len(row[self.ATTR_DICTIONARIES]) == 0:
                    self.data.pop(i)
                    self.strokes.pop(self.getIdentifier(row[self.ATTR_STROKE], row[self.ATTR_TRANSLATION]), None)
        # doing this in a separate loop because rows are not in the same order as data
        for i in reversed(range(len(self.rows))):
            if len(self.rows[i][self.ATTR_DICTIONARIES]) == 0:
                self.rows.pop(i)
        self.dictionaries.pop(filename, None)
        self.dictionaryFilenames.remove(filename)
        self.dictionaryNames.remove(self.getDictionaryShortName(filename))
        if self.ATTR_DICTIONARIES in self.filters and filename in self.filters[self.ATTR_DICTIONARIES]:
            self.filters[self.ATTR_DICTIONARIES].remove(filename)
            self.filter(self.filters, True)
        self.removeDictionaryFromActives(filename)
        self.fireEvent("tableChange", self)
        self.fireEvent("dictionaryClosed", filename, index)
    
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
        """ Change the stroke value in row """
        
        item = self.rows[row]
        orig = item[self.ATTR_STROKE]
        item[self.ATTR_STROKE] = stroke
        # update strokes cache
        self.strokes[self.getIdentifier(stroke, item[self.ATTR_TRANSLATION])] = self.strokes.pop(self.getIdentifier(orig, item[self.ATTR_TRANSLATION]))
        for filename in item[self.ATTR_DICTIONARIES]:
            self.dictionaries[filename].change(orig, item[self.ATTR_TRANSLATION], item[self.ATTR_STROKE], item[self.ATTR_TRANSLATION])
            self.fireEvent("dataChange", self.getDictionaryIndexByName(filename), self.dictionaries[filename].hasChanges())
        
    def changeTranslation(self, row, translation):
        """ Change the translation in row """
        
        item = self.rows[row]
        orig = item[self.ATTR_TRANSLATION]
        item[self.ATTR_TRANSLATION] = translation
        # update strokes cache
        self.strokes[self.getIdentifier(item[self.ATTR_STROKE], translation)] = self.strokes.pop(self.getIdentifier(item[self.ATTR_STROKE], orig))
        for filename in item[self.ATTR_DICTIONARIES]:
            self.dictionaries[filename].change(item[self.ATTR_STROKE], orig, item[self.ATTR_STROKE], item[self.ATTR_TRANSLATION])
            self.fireEvent("dataChange", self.getDictionaryIndexByName(filename), self.dictionaries[filename].hasChanges())
        
    def changeDictionaries(self, row, dictionaries):
        """ Change dictionary list for the item """
        
        item = self.rows[row]
        item[self.ATTR_DICTIONARIES] = dictionaries
        # dataChange event already fired
    
    def insertItem(self, item = None):
        """ Insert an empty row """
        if item is None:
            item = {self.ATTR_STROKE: "", self.ATTR_TRANSLATION: "", self.ATTR_DICTIONARIES: []}
        return self._insertItem(item)
    
    def getDictionaryNames(self):
        return self.dictionaryNames
    
    def getDictionaryFilenames(self):
        return self.dictionaryFilenames
    
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
            self.fireEvent("dataChange", self.getDictionaryIndexByName(filename), self.dictionaries[filename].hasChanges())
        added = list(set(dictionaries) - set(before))
        for filename in added:
            self.dictionaries[filename].insert(item[self.ATTR_STROKE], item[self.ATTR_TRANSLATION])
            self.fireEvent("dataChange", self.getDictionaryIndexByName(filename), self.dictionaries[filename].hasChanges())
        
    def getDictionaryIndexByName(self, name):
        if name in self.dictionaryFilenames:
            return self.dictionaryFilenames.index(name)
        return None
    
    def getDictionaryNameByIndex(self, index):
        if index < len(self.dictionaryFilenames):
            return self.dictionaryFilenames[index]
        return None
    
    def getMerged(self):
        """ Merge dictionaries into one """
        merged = StenoDictionary()
        items = self.dictionaries.values()
        for i in range(len(items)-1, -1, -1):
            merged.update((normalize_steno(k), items[i][k]) for k in items[i])
        return merged
