"""

Plover Dictionary Manager

"""

from dictionarymanager.gui.widget.dmGrid import dmGrid
from dictionarymanager.store import Store
from threading import Timer
from wx._misc import BeginBusyCursor, EndBusyCursor
import os
import wx

class DictionaryManagerGUI(wx.App):
    """The main entry point for the Dictionary Manager."""
    
    def __init__(self):
        wx.App.__init__(self, redirect=False)
    
    def OnInit(self):
        """Called just before the application starts."""
        frame = Frame()
        frame.SetSize((600, 400))
        frame.Show()
        self.SetTopWindow(frame)
        return True

class Frame(wx.Frame):
    """ Main Frame """
    
    TITLE = "Dictionary Manager"
    
    def __init__(self):
        
        wx.Frame.__init__(self, None,
                          title=Frame.TITLE,
                          pos=wx.DefaultPosition,
                          size=wx.DefaultSize,
                          style=wx.DEFAULT_FRAME_STYLE|wx.TAB_TRAVERSAL)
        
        # dictionary store
        self.store = Store.Store()
        
        # auxiliary variables
        self._keyTimer = None
        
        # menu
        menubar = wx.MenuBar()
        fileMenu = wx.Menu()
        openMenuItem = fileMenu.Append(wx.ID_OPEN, '&Open dictionary')
        saveMenuItem = fileMenu.Append(wx.ID_SAVE, '&Save dictionaries')
        quitMenuItem = fileMenu.Append(wx.ID_EXIT, 'Quit', 'Quit application')
        menubar.Append(fileMenu, '&File')
        self.SetMenuBar(menubar)
        self.Bind(wx.EVT_MENU, self._open, openMenuItem)
        self.Bind(wx.EVT_MENU, self._save, saveMenuItem)
        self.Bind(wx.EVT_MENU, self._quit, quitMenuItem)

        # add new stroke button
        self.addRowButton = wx.Button(self, wx.ID_ANY, label="Add")
        self.Bind(wx.EVT_BUTTON, self._addRow, self.addRowButton)
        
        # search fields
        self.searchStrokeField = wx.TextCtrl(self, wx.ID_ANY, value="")
        self.searchTranslationField = wx.TextCtrl(self, wx.ID_ANY, value="")
        
        self.searchStrokeField.Bind(wx.EVT_KEY_UP, self._onFilterKeyUp)
        self.searchTranslationField.Bind(wx.EVT_KEY_UP, self._onFilterKeyUp)
        
        # search fields layout
        searchSizer = wx.BoxSizer(wx.HORIZONTAL)
        searchSizer.Add(wx.StaticText(self, label="Filter by stroke:"), 0, wx.ALL, 5)
        searchSizer.Add(self.searchStrokeField, 1, wx.EXPAND)
        searchSizer.Add(wx.StaticText(self, label="Filter by translation:"), 0, wx.ALL, 5)
        searchSizer.Add(self.searchTranslationField, 1, wx.EXPAND)
        searchSizer.Add(self.addRowButton, 0, wx.EXPAND)
        
        # grid
        self.grid = dmGrid(self)
        self.grid.CreateGrid(self.store, 0, 3)
        self.grid.SetColSize(0, 300)
        self.grid.SetColSize(1, 300)
        self.grid.SetColSize(2, 300)
        
        # main Layout
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(searchSizer, 0, wx.EXPAND)
        sizer.Add(self.grid, 1, wx.EXPAND)
        self.SetSizerAndFit(sizer)
        
        self.Bind(wx.EVT_CLOSE, self._quit)
    
    def _open(self, event=None):
        """ Open up File Dialog to load dictionary """
        
        dlg = wx.FileDialog(self, "Choose a dictionary", ".", "", "*.*", wx.OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            filename = dlg.GetFilename()
            dirname = dlg.GetDirectory()
            dlg.Destroy()
            
            self.grid._startGridJob("Loading", "Loading dictionary")
            try:
                self.store.loadDictionary(os.path.join(dirname, filename))
            finally:
                self.grid._endGridJob()
        else:
            dlg.Destroy()
    
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
        