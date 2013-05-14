from plover.config import get_option_as_set, get_option_as_list, \
    set_list_as_option, save_config
from plover.steno_dictionary import StenoDictionary
from threading import Timer
from wx._misc import BeginBusyCursor, EndBusyCursor
from wx.grid import EVT_GRID_CELL_CHANGE
from wxPython._core import wxOK
from wxPython.grid import wxGrid
import os.path
import plover.config as conf
import wx

class QuickLoader(wx.Dialog):
    """ Dictionary Quick Loader dialog """
    
    TITLE = "Quick Loader"
    
    def __init__(self, steno_engine, parent = None):
        wx.Dialog.__init__(self, parent,
                          title=self.TITLE,
                          pos=wx.DefaultPosition,
                          size=wx.DefaultSize,
                          style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER
                                 | wx.MAXIMIZE_BOX | wx.MINIMIZE_BOX)
        self.config = conf.get_config()
        self.stenoEngine = steno_engine
        self.parent = parent
        self.error = None
        
        # Grid
        self.grid = wxGrid(self)
        self.grid.CreateGrid(0, 2)
        self.grid.SetColSize(0, 100)
        self.grid.SetColSize(1, 150)
        self.grid.SetRowLabelSize(0)
        self.grid.SetColLabelSize(0)
        
        attr = wx.grid.GridCellAttr()
        attr.SetReadOnly(True)
        self.grid.SetColAttr(1, attr)
        
        self.grid.Bind(EVT_GRID_CELL_CHANGE, self._onCellChange)
        
        # dictionary lists
        self.loadedDictList = None
        self.cfgDictList = None
        
        # Layout
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.grid, 1, wx.EXPAND)
        
        self.SetSizer(self.sizer)
        
    def _onCellChange(self, evt):
        row = evt.Row
        name = self.grid.GetCellValue(row, 0)
        
        (shortcut, filename) = list(self.dictList)[row]
        entry = filename
        if shortcut != "":
            entry += ";" + shortcut
        cfgDictList = get_option_as_set(self.config, conf.DICTIONARY_CONFIG_SECTION, conf.DICTIONARY_LIST_OPTION)
        cfgDictList.remove(entry)
        cfgDictList.add(filename + ";" + name)
        
        set_list_as_option(self.config, conf.DICTIONARY_CONFIG_SECTION, conf.DICTIONARY_LIST_OPTION, cfgDictList)
        save_config(self.config)
    
    def _stenoEngineCallback(self, undo, do, prev):
        if len(do) > 0:
            translation = do[0].english
            for (key, value) in self.dictList:
                if translation == key:
                    BeginBusyCursor()
                    try:
                        self.stenoEngine.store.toggleDictionary(value)
                        self.Hide()
                    except ValueError, e:
                        self.error = e
                        wx.CallAfter(self._showError)
                    finally:
                        EndBusyCursor()
                    break
            
    
    def Show(self):
        self.stenoEngine.translator.add_listener(self._stenoEngineCallback)
        
        self.loadedDictList = get_option_as_set(self.config, conf.DICTIONARY_CONFIG_SECTION, conf.DICTIONARY_FILE_OPTION)
        cfgDictList = get_option_as_set(self.config, conf.DICTIONARY_CONFIG_SECTION, conf.DICTIONARY_LIST_OPTION)
        self.dictList = set()
        for item in cfgDictList:
            path = item.split(";")
            shortcut = ""
            if len(path) > 1:
                shortcut = path.pop(-1)
            self.dictList.add((shortcut, ";".join(path).strip()))
        
        index = 0
        for (key, value) in self.dictList:
            if self.grid.GetNumberRows() <= index:
                self.grid.AppendRows()
            self.grid.SetCellValue(index, 0, key)
            self.grid.SetCellValue(index, 1, os.path.basename(value))
            index += 1
        
        wx.Dialog.Show(self)
        self.Fit()
        
    def Hide(self):
        # we cannot remove listener right now because probably we are in a loop over those listeners
        Timer(0.1, self._removeListener)
        wx.Dialog.Hide(self)
        
    def _removeListener(self):
        self.stenoEngine.translator.remove_listener(self._stenoEngineCallback)
        
    def _showError(self):
        dlg = wx.MessageDialog(self.parent, str(self.error), style=wxOK | wx.ICON_ERROR)
        dlg.ShowModal()
        dlg.Destroy()
        