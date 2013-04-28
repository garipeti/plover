import wx
from wxPython.grid import wxGrid
import plover.config as conf

class QuickLoader(wx.Dialog):
    """ Dictionary Quick Loader dialog """
    
    TITLE = "Quick Loader"
    
    def __init__(self, parent = None):
        wx.Dialog.__init__(self, parent,
                          title=self.TITLE,
                          pos=wx.DefaultPosition,
                          size=wx.DefaultSize,
                          style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER
                                 | wx.MAXIMIZE_BOX | wx.MINIMIZE_BOX)
        self.config = conf.get_config()
        
        # Grid
        self.grid = wxGrid(self)
        self.grid.CreateGrid(0, 3)
        self.grid.SetColSize(0, 50)
        self.grid.SetColSize(1, 100)
        self.grid.SetColSize(2, 150)
        self.grid.SetRowLabelSize(0)
        self.grid.SetColLabelSize(0)
        
        cfgLoadedDictList = self.config.get(conf.DICTIONARY_CONFIG_SECTION, conf.DICTIONARY_FILE_OPTION)
        loadedDictList = filter(None, [x.strip() for x in cfgLoadedDictList.splitlines()])
        cfgDictList = self.config.get(conf.DICTIONARY_CONFIG_SECTION, conf.DICTIONARY_LIST_OPTION)
        dictList = map(lambda x: (x.split(";")[0].strip(), ";".join(x.split(";")[-1:]).strip()), filter(None, [x.strip() for x in cfgDictList.splitlines()]))
        
        index = 0
        for (key, value) in dictList:
            self.grid.AppendRows()
            self.grid.SetCellValue(index, 0, str(index))
            self.grid.SetCellValue(index, 1, key)
            self.grid.SetCellValue(index, 2, value)
            index += 1
        
        # Layout
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.grid, 1, wx.EXPAND)
        
        self.SetSizerAndFit(self.sizer)
        
    def Show(self):
        wx.Dialog.Show(self)
        
    def Hide(self):
        wx.Dialog.Hide(self)
        
    