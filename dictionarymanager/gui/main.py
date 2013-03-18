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
from wxPython._core import wxYES_NO, wxCENTER, wxOK
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
        self.searchField = wx.TextCtrl(self, wx.ID_ANY, value="Enter a stroke or a translation")
        self.searchStroke = wx.Button(self, wx.ID_ANY, label="Search Stroke")
        self.searchTranslation = wx.Button(self, wx.ID_ANY, label="Search Translation")
        
        self.searchStroke.Bind(wx.EVT_BUTTON, self._onStrokeSearch)
        self.searchTranslation.Bind(wx.EVT_BUTTON, self._onTranslationSearch)
        
        # search fields layout
        searchSizer = wx.BoxSizer(wx.HORIZONTAL)
        searchSizer.Add(self.searchField, 1, wx.EXPAND)
        searchSizer.Add(self.searchStroke, 0, wx.EXPAND)
        searchSizer.Add(self.searchTranslation, 0, wx.EXPAND)
        
        # grid
        self.grid = CustomGrid(self)
        self.grid.CreateGrid(0, 3)
        self.grid.SetDefaultRenderer(CutomGridCellRenderer(self.store))
        self.grid.SetColLabelValue(0, "Stroke")
        self.grid.SetColSize(0, 300)
        self.grid.SetColLabelValue(1, "Translation")
        self.grid.SetColSize(1, 300)
        self.grid.SetColLabelValue(2, "Dictionaries")
        self.grid.SetColSize(2, 300)
        self.grid.SetDefaultEditor(CustomGridCellEditor(self.store))
        #self.gridDictionaryEditor = CustomGridCellEditor(self.store)
        self.grid.Bind(EVT_GRID_CELL_CHANGE, self._onCellChange)
        
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
            self.store.loadDictionary(os.path.join(dirname, filename), self._onGridChange)
            self.grid.EndBatch()
            self.progress.Destroy()
        else:
            dlg.Destroy()
    
    def _onGridChange(self, index, identifier, item, percent):
        """ To track dictionary loading progress """
        
        if percent != None:
            self.progress.Update(percent)
        if index == self.store.count-1:
            self.grid.AppendRows(1)
            self.grid.SetCellValue(index, 0, item["stroke"])
            self.grid.SetCellValue(index, 1, item["translation"])
            #self.grid.SetCellEditor(index, 2, self.gridDictionaryEditor)
        self.grid.SetCellValue(index, 2, self.store.dictionaryFilenameListToIndexString(item["dictionaries"]))
    
    def _onCellChange(self, evt):
        """ Handle Grid Cell change """
        
        print(str(evt))
        row = evt.Row
        value = self.grid.GetCellValue(evt.Row, evt.Col)
        if evt.Col == 0:
            self.store.changeStroke(row, value)
        elif evt.Col == 1:
            self.store.changeTranslation(row, value)
        else:
            self.store.changeDictionaries(row, value)
    
    def _onStrokeSearch(self, evt):
        """ Stroke Search Button click """
        
        self._findRow("stroke", self.searchField.GetValue())
    
    def _onTranslationSearch(self, evt):
        """ TRanslation Search Button click """
        
        self._findRow("translation", self.searchField.GetValue())
    
    def _findRow(self, column, pattern):
        """ Find next matching row """
        
        selected = self.grid.GetSelectedRows()
        if len(selected) > 0:
            start = selected[0]+1
        else:
            start = 0
        self._findRowFrom(column, pattern, start)
    
    def _findRowFrom(self, column, pattern, start):
        """ Find next matching row from start index """
        
        index = self.store.findItem(column, pattern, start)
        if index > -1:
            self.grid.MakeCellVisible(index, 0)
            self.grid.SelectRow(index, False)
        elif start != 0:
            dlg = wx.MessageDialog(self, "Not found. Do you want to start it from the beginning?", style=wxYES_NO | wxCENTER)
            if dlg.ShowModal() == wx.ID_YES:
                self._findRowFrom(column, pattern, 0)
        else:
            dlg = wx.MessageDialog(self, "Not found.", style=wxOK | wxCENTER)
            dlg.ShowModal()
    
    def _save(self, event=None):
        """ Save dictionaries """
        
        self.store.saveDictionaries()
    
    def _quit(self, event=None):
        """ Quit application """
        
        self.Destroy()
        