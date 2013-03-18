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
    
    def loadDictionary(self, filename, onChange):
        """ Load dictionary from file """
        
        loader = self.getLoader(filename)
        if loader != None:
            dictionary = loader.load(filename)
            if dictionary != None:
                self.dictionaries[filename] = dictionary
                self.dictionaryFilenames.append(filename)
                self.dictionaryNames.append(self.getDictionaryShortName(filename))
                length = len(dictionary)
                progress = length / 100
                currentStep = progress
                currentProgress = 0
                for stroke, translation in dictionary.iteritems():
                    identifier = self.getIdentifier(stroke, translation)
                    if identifier not in self.strokes:
                        item = {"stroke": stroke, "translation": translation, "dictionaries": [], "index": self.count}
                        self.strokes[identifier] = item
                        self.rows.append(item)
                        self.count += 1
                    else:
                        item = self.strokes[identifier]
                    item["dictionaries"].append(filename)
                    onChange(item["index"], identifier, item, currentProgress+1 if self.count > currentStep else None)
                    if self.count > currentStep:
                        currentStep += progress
                        currentProgress += 1

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
    
    def findItem(self, column, pattern, index):
        """ Find next item which matches in the given attribute """
        
        if index == None or index < 0:
            index = 0
        for i in range(index, self.count):
            if pattern in self.rows[i][column]:
                return i
        return -1
    
    def changeDictionaries(self, row, dictionaries):
        """ Change dictionary list for the item """
        
        self.rows[row]["dictionaries"] = self.indexStringToDictionaryList(dictionaries)
    
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
        