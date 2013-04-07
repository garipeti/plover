"""

Plover Dictionary Manager

"""

from dictionarymanager.gui.widget.dmGrid import dmGrid
from dictionarymanager.store import Store
from threading import Timer
from wx._misc import BeginBusyCursor, EndBusyCursor
import os
import plover.config as conf
import wx

class DictionaryManagerGUI(wx.App):
    """The main entry point for the Dictionary Manager."""
    
    def __init__(self):
        wx.App.__init__(self, redirect=False)
    
    def OnInit(self):
        """Called just before the application starts."""
        frame = dmFrame()
        frame.SetSize((600, 400))
        frame.Show()
        self.SetTopWindow(frame)
        return True

class dmFrame(wx.Dialog):
    """ Main dmFrame """
    
    TITLE = "Dictionary Manager"
    LOAD_BUTTON_NAME = "Load dictionary"
    ADD_BUTTON_NAME = "Add translation"
    VISIBILITY_BUTTON_HIDE = "Hide"
    VISIBILITY_BUTTON_SHOW = "Show"
    LOADED_LABEL = "Loaded:"
    FILTER_STROKE_LABEL = "Filter by stroke:"
    FILTER_TRANSLATION_LABEL = "Filter by translation:"
    CHOOSE_DICTIONARY = "Choose a dictionary"
    LOADING = "Loading"
    LOADING_DICTIONARY = "Loading dictionary "
    
    POSITION_LABEL = 0
    POSITION_SAVE = 1
    POSITION_VISIBILITY = 2
    POSITION_CLOSE = 3
    
    def __init__(self):
        
        wx.Dialog.__init__(self, None,
                          title=dmFrame.TITLE,
                          pos=wx.DefaultPosition,
                          size=wx.DefaultSize,
                          style=wx.wx.DEFAULT_DIALOG_STYLE)
        
        # configuration
        self.config = conf.get_config()
        
        # dictionary store
        self.store = Store.Store()
        
        # auxiliary variables
        self._keyTimer = None
        
        # loaded dictionaries
        loadedHolder = wx.BoxSizer(wx.HORIZONTAL)
        loadedHolder.Add(wx.StaticText(self, label=self.LOADED_LABEL), 0, wx.ALL, 5)
        self.loadedSizer = wx.BoxSizer(wx.HORIZONTAL)
        loadedHolder.Add(self.loadedSizer, 1, wx.EXPAND)
        
        # search fields
        self.searchStrokeField = wx.TextCtrl(self, wx.ID_ANY, value="")
        self.searchTranslationField = wx.TextCtrl(self, wx.ID_ANY, value="")
        self.searchStrokeField.Bind(wx.EVT_KEY_UP, self._onFilterKeyUp)
        self.searchTranslationField.Bind(wx.EVT_KEY_UP, self._onFilterKeyUp)
        
        # search fields layout
        searchSizer = wx.BoxSizer(wx.HORIZONTAL)
        searchSizer.Add(wx.StaticText(self, label=self.FILTER_STROKE_LABEL), 0, wx.ALL, 5)
        searchSizer.Add(self.searchStrokeField, 1, wx.EXPAND)
        searchSizer.Add(wx.StaticText(self, label=self.FILTER_TRANSLATION_LABEL), 0, wx.ALL, 5)
        searchSizer.Add(self.searchTranslationField, 1, wx.EXPAND)
        
        # grid
        self.grid = dmGrid(self)
        self.grid.CreateGrid(self.store, 0, 3)
        self.grid.SetColSize(0, 300)
        self.grid.SetColSize(1, 300)
        self.grid.SetColSize(2, 300)
        
        # main Layout
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(loadedHolder, 0, wx.EXPAND)
        self.sizer.Add(searchSizer, 0, wx.EXPAND)
        self.sizer.Add(self.grid, 1, wx.EXPAND)
        
        # action buttons
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        # add new stroke button
        add_button = wx.Button(self, wx.ID_ANY, label=self.ADD_BUTTON_NAME)
        add_button.Bind(wx.EVT_BUTTON, self._addRow)
        button_sizer.Add(add_button)
        # save
        save_button = wx.Button(self, wx.ID_OPEN, self.LOAD_BUTTON_NAME)
        save_button.Bind(wx.EVT_BUTTON, self._open)
        button_sizer.Add(save_button)
        # close
        close_button = wx.Button(self, wx.ID_CLOSE)
        close_button.Bind(wx.EVT_BUTTON, self._quit)
        button_sizer.Add(close_button)
        self.sizer.Add(button_sizer, 0, flag=wx.ALL | wx.ALIGN_RIGHT, border=4)
        
        self.SetSizerAndFit(self.sizer)
        self.Bind(wx.EVT_CLOSE, self._quit)
        
        # load dictionaries from config
        dict_files = self.config.get(conf.DICTIONARY_CONFIG_SECTION, conf.DICTIONARY_FILE_OPTION)
        for dict_file in filter(None, [x.strip() for x in dict_files.splitlines()]):
            self._readDictionary(os.path.join(conf.CONFIG_DIR, dict_file))
    
    def _open(self, event=None):
        """ Open up File Dialog to load dictionary """
        
        dlg = wx.FileDialog(self, self.CHOOSE_DICTIONARY, ".", "", "*.*", wx.OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            filename = dlg.GetFilename()
            dirname = dlg.GetDirectory()
            dlg.Destroy()
            
            self._readDictionary(os.path.join(dirname, filename))
        else:
            dlg.Destroy()
    
    def _readDictionary(self, filename):
        self.grid._startGridJob(self.LOADING, self.LOADING_DICTIONARY + self.store.getDictionaryShortName(filename))
        try:
            self.store.loadDictionary(filename)
            
            box = wx.BoxSizer(wx.HORIZONTAL)
            box.Add(wx.StaticText(self, wx.ID_ANY, label=self.store.getDictionaryShortName(filename)))
            save = wx.BitmapButton(self, wx.ID_ANY, wx.ArtProvider_GetBitmap(wx.ART_FILE_SAVE))
            save.Bind(wx.EVT_BUTTON, self._saveDictionary)
            box.Add(save)
            box.Hide(save)
            visibility = wx.Button(self, wx.ID_ANY, self.VISIBILITY_BUTTON_HIDE)
            box.Add(visibility)
            remove = wx.BitmapButton(self, wx.ID_ANY, wx.ArtProvider_GetBitmap(wx.ART_CROSS_MARK))
            remove.Bind(wx.EVT_BUTTON, self._closeDictionary)
            box.Add(remove)
            
            self.loadedSizer.Add(box)
            self.loadedSizer.Layout()
        finally:
            self.grid._endGridJob()
    
    def _closeDictionary(self, evt):
        btn = evt.GetEventObject()
        items = self.loadedSizer.GetChildren()
        for i, item in enumerate(items):
            if item.GetSizer().GetChildren()[self.POSITION_CLOSE].GetWindow() == btn:
                self.loadedSizer.Hide(i)
                self.loadedSizer.Remove(i)
                self.sizer.Layout()
                self.store.closeDictionary(i)
                break
    
    def _onDictionaryChange(self, index):
        items = self.loadedSizer.GetChildren()
        if len(items) > index:
            items[index].GetSizer().Show(self.POSITION_SAVE)
    
    def _saveDictionary(self, evt):
        btn = evt.GetEventObject()
        items = self.loadedSizer.GetChildren()
        for i, item in enumerate(items):
            if item.GetSizer().GetChildren()[self.POSITION_SAVE].GetWindow() == btn:
                item.GetSizer().Hide(btn)
                self.store.saveDictionary(i)
    
    def _onFilterKeyUp(self, evt):
        """ KeyUp event on search fields """
        
        if self._keyTimer != None:
            self._keyTimer.cancel()
        
        self._keyTimer = Timer(0.5, self._callFilterChange)
        self._keyTimer.start()
    
    def _callFilterChange(self):
        wx.CallAfter(self._onFilterChange)
    
    def _onFilterChange(self):
        """ KeyUp event on search fields """
        
        if self._keyTimer != None:
            self._keyTimer.cancel()
            self._keyTimer = None
            
        filters = [
                   {"pattern": self.searchStrokeField.GetValue(), "column": Store.Store.ATTR_STROKE},
                   {"pattern": self.searchTranslationField.GetValue(), "column": Store.Store.ATTR_TRANSLATION}
                ]
        
        BeginBusyCursor()
        self.grid.MakeCellVisible(0, 0)
        try:
            self.store.filter(filters)
        finally:
            EndBusyCursor()
        
    def _addRow(self, event=None):
        """ Save dictionaries """
        row = self.store.insertItem()
        self.grid.MakeCellVisible(row, 0)
    
    def _save(self, event=None):
        """ Save dictionaries """
        
        self.store.saveDictionaries()
    
    def _quit(self, event=None):
        """ Quit application """
        
        self.Destroy()
        