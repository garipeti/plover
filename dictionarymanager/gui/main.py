"""

Plover Dictionary Manager

"""

from dictionarymanager.gui.widget.CustomGrid import CustomGrid
from dictionarymanager.gui.widget.CustomGridCellEditor import \
    CustomGridCellEditor
from dictionarymanager.gui.widget.CustomGridCellRenderer import \
    CutomGridCellRenderer
from dictionarymanager.store import Store
from threading import Timer
from wx._core import CURSOR_WAIT
from wx._gdi import StockCursor, NullCursor
from wx._misc import BeginBusyCursor, EndBusyCursor
from wx.grid import EVT_GRID_CELL_CHANGE, EVT_GRID_LABEL_LEFT_CLICK
from wxPython.grid import wxGridCellAttr
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
    GRID_LABEL_STROKE = "Stroke"
    GRID_LABEL_TRANSLATION = "Translation"
    GRID_LABEL_DICTIONARIES = "Dictionaries"
    GRID_LABELS = [GRID_LABEL_STROKE, GRID_LABEL_TRANSLATION, GRID_LABEL_DICTIONARIES]
    
    def __init__(self):
        
        wx.Frame.__init__(self, None,
                          title=Frame.TITLE,
                          pos=wx.DefaultPosition,
                          size=wx.DefaultSize,
                          style=wx.DEFAULT_FRAME_STYLE|wx.TAB_TRAVERSAL)
        
        # dictionary store
        self.store = Store.Store()
        
        # auxiliary variables
        self._cellChanging = False
        self._sortingColumn = 0
        self._sortingAsc = True
        self._keyTimer = None
        #self._controlInFocus = None
        
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
        
        # grid
        self.grid = CustomGrid(self)
        self.grid.CreateGrid(0, 3)
        self.grid.SetColSize(0, 300)
        self.grid.SetColSize(1, 300)
        self.grid.SetColSize(2, 300)
        self._changeGridLabel()
        self.grid.Bind(EVT_GRID_CELL_CHANGE, self._onCellChange)
        self.grid.Bind(EVT_GRID_LABEL_LEFT_CLICK, self._onLabelClick)
        
        attr = wxGridCellAttr()
        attr.SetEditor(CustomGridCellEditor(self.store))
        attr.SetRenderer(CutomGridCellRenderer(self.store))
        self.grid.SetColAttr(2, attr)
        
        self.store.subscribe("insert", self._onInsertRow)
        self.store.subscribe("delete", self._onDeleteRow)
        self.store.subscribe("update", self._onUpdateRow)
        
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
            
            self._startGridJob("Loading", "Loading dictionary")
            try:
                self.store.loadDictionary(os.path.join(dirname, filename))
            finally:
                self._endGridJob()
        else:
            dlg.Destroy()
    
    def _onProgressChange(self, percent):
        """ To track dictionary loading progress """
        
        if percent != None:
            self.progress.Update(percent)
            
    def _onInsertRow(self, item, index):
        self.grid.InsertRows(index, 1)
        self.grid.SetCellValue(index, 0, item["stroke"])
        self.grid.SetCellValue(index, 1, item["translation"])
        self.grid.SetCellValue(index, 2, self.store.dictionaryFilenameListToIndexString(item["dictionaries"]))
    
    def _onDeleteRow(self, item, index):
        self.grid.DeleteRows(index, 1)
        
    def _onUpdateRow(self, item, index):
        self.grid.SetCellValue(index, 0, item["stroke"])
        self.grid.SetCellValue(index, 1, item["translation"])
        self.grid.SetCellValue(index, 2, self.store.dictionaryFilenameListToIndexString(item["dictionaries"]))
        
    def _onCellChange(self, evt):
        """ Handle Grid Cell change """
    
        if self._cellChanging:
            return
        row = evt.Row
        self._cellChanging = True
        value = self.grid.GetCellValue(row, evt.Col)
        if evt.Col == 0:
            self.store.changeStroke(row, value)
        elif evt.Col == 1:
            self.store.changeTranslation(row, value)
        else:
            self.store.changeDictionaries(row, value)
        self._cellChanging = False
    
    def _onLabelClick(self, evt):
        """ Handle Grid label click"""
        
        if evt.Row == -1:
            propertyName = "stroke" if evt.Col == 0 else "translation" if evt.Col == 1 else "dictionaries"
            self._sortingAsc = (not self._sortingAsc) if evt.Col == self._sortingColumn else True
            self._sortingColumn = evt.Col
            self._changeGridLabel()
            
            self._startGridJob("Progress", "Sorting...")
            try:
                self.store.sort(propertyName, self._sortingAsc)
            finally:
                self._endGridJob()
    
    def _changeGridLabel(self):
        directionLabel = " (asc)" if self._sortingAsc else " (desc)"
        for i in range(3):
            self.grid.SetColLabelValue(i, self.GRID_LABELS[i] + (directionLabel if self._sortingColumn == i else ""))
        
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
            
        filters = []
        if self.searchStrokeField.GetValue() != "":
            filters.append({"pattern": self.searchStrokeField.GetValue(), "column": "stroke"})
        if self.searchTranslationField.GetValue() != "":
            filters.append({"pattern": self.searchTranslationField.GetValue(), "column": "translation"})
        
        BeginBusyCursor()
        try:
            self.store.filter(filters)
        finally:
            EndBusyCursor()
        
    def _startGridJob(self, title, text):
        BeginBusyCursor()
        self.progress = wx.ProgressDialog(title, text)
        self.grid.BeginBatch()
        self.store.subscribe("progress", self._onProgressChange)
        
    def _endGridJob(self):
        self.store.unsubscribe("progress", self._onProgressChange)
        self.grid.EndBatch()
        self.progress.Destroy()
        EndBusyCursor()
        
    def _save(self, event=None):
        """ Save dictionaries """
        
        self.store.saveDictionaries()
    
    def _quit(self, event=None):
        """ Quit application """
        
        self.Destroy()
        