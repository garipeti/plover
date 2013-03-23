"""

Plover Dictionary Manager

"""

from dictionarymanager.gui.widget.CustomGrid import CustomGrid
from dictionarymanager.gui.widget.CustomGridCellEditor import \
    CustomGridCellEditor
from dictionarymanager.gui.widget.CustomGridCellRenderer import \
    CutomGridCellRenderer
from dictionarymanager.store import Store
from wx.grid import EVT_GRID_CELL_CHANGE
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
        
        self.searchStrokeField.Bind(wx.EVT_KEY_UP, self._onFilterChange)
        self.searchTranslationField.Bind(wx.EVT_KEY_UP, self._onFilterChange)
        
        # search fields layout
        searchSizer = wx.BoxSizer(wx.HORIZONTAL)
        searchSizer.Add(wx.StaticText(self, label="Enter a stroke"), 0, wx.EXPAND)
        searchSizer.Add(self.searchStrokeField, 1, wx.EXPAND)
        searchSizer.Add(wx.StaticText(self, label="Enter a translation"), 0, wx.EXPAND)
        searchSizer.Add(self.searchTranslationField, 1, wx.EXPAND)
        
        # grid
        self.grid = CustomGrid(self)
        self.grid.CreateGrid(0, 3)
        #self.grid.RegisterDataType("list", CutomGridCellRenderer(self.store), CustomGridCellEditor(self.store))
        #self.grid.SetDefaultRenderer(CutomGridCellRenderer(self.store))
        self.grid.SetColLabelValue(0, "Stroke")
        self.grid.SetColSize(0, 300)
        self.grid.SetColLabelValue(1, "Translation")
        self.grid.SetColSize(1, 300)
        self.grid.SetColLabelValue(2, "Dictionaries")
        self.grid.SetColSize(2, 300)
        #self.grid.SetColFormatCustom(2, "list")
        #self.grid.SetDefaultEditor(CustomGridCellEditor(self.store))
        #self.gridDictionaryEditor = CustomGridCellEditor(self.store)
        self.grid.Bind(EVT_GRID_CELL_CHANGE, self._onCellChange)
        
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
            self.progress = wx.ProgressDialog("Loading", "Loading dictionary")
            self.grid.BeginBatch()
            self.store.subscribe("progress", self._onProgressChange)
            self.store.loadDictionary(os.path.join(dirname, filename))
            self.store.unsubscribe("progress", self._onProgressChange)
            self.grid.EndBatch()
            self.progress.Destroy()
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
        #self.grid.SetCellEditor(index, 2, self.gridDictionaryEditor)
        #self.grid.GetTable().setValueAsCustom(item["index"], 2, "list", item["dictionaries"])
        self.grid.SetCellValue(index, 2, self.store.dictionaryFilenameListToIndexString(item["dictionaries"]))
    
    def _onDeleteRow(self, item, index):
        self.grid.DeleteRows(index, 1)
        
    def _onUpdateRow(self, item, index):
        self.grid.SetCellValue(index, 0, item["stroke"])
        self.grid.SetCellValue(index, 1, item["translation"])
        self.grid.SetCellValue(index, 2, self.store.dictionaryFilenameListToIndexString(item["dictionaries"]))
        
    def _onCellChange(self, evt):
        """ Handle Grid Cell change """
        print("on edit")
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
    
    def _onFilterChange(self, evt):
        """ KeyUp event on search fields """
        filters = []
        if self.searchStrokeField.GetValue() != "":
            filters.append({"pattern": self.searchStrokeField.GetValue(), "column": "stroke"})
        if self.searchTranslationField.GetValue() != "":
            filters.append({"pattern": self.searchTranslationField.GetValue(), "column": "translation"})
        
        self.progress = wx.ProgressDialog("Progress", "Filtering...")
        self.grid.BeginBatch()
        self.store.subscribe("progress", self._onProgressChange)
        self.store.filter(filters)
        self.store.unsubscribe("progress", self._onProgressChange)
        self.grid.EndBatch()
        self.progress.Destroy()
        
    def _save(self, event=None):
        """ Save dictionaries """
        
        self.store.saveDictionaries()
    
    def _quit(self, event=None):
        """ Quit application """
        
        self.Destroy()
        