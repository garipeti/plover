import wx

class dmDictionaryMenu(wx.Menu):
    """ Dictionary action list menu """
    
    CLOSE_LABEL = "Close"
    SAVE_LABEL = "Save"
    SAVE_AS_LABEL = "Save as"
    HIDE_LABEL = "Hide"
    SHOW_LABEL = "Show"
    
    def __init__(self, dictionaryName, save_callback, save_as_callback, close_callback, hide_callback):
        wx.Menu.__init__(self)

        self.dictionaryName = dictionaryName
        self.saveCallback = save_callback
        self.saveAsCallback = save_as_callback
        self.closeCallback = close_callback
        self.hideCallback = hide_callback
        
        # menu items
        self.saveItemId = wx.NewId()
        item = wx.MenuItem(self, self.saveItemId, self.SAVE_LABEL)
        self.AppendItem(item)
        self.Bind(wx.EVT_MENU, self._save, item)
        item = wx.MenuItem(self, wx.NewId(), self.SAVE_AS_LABEL)
        self.AppendItem(item)
        self.Bind(wx.EVT_MENU, self._saveAs, item)
        self.visibilityItem = wx.MenuItem(self, wx.NewId(), self.HIDE_LABEL)
        self.AppendItem(self.visibilityItem)
        self.Bind(wx.EVT_MENU, self._hide, self.visibilityItem)
        item = wx.MenuItem(self, wx.NewId(), self.CLOSE_LABEL)
        self.AppendItem(item)
        self.Bind(wx.EVT_MENU, self._close, item)

    def setSaveState(self, state):
        """ Set the save menu item's state."""
        self.Enable(self.saveItemId, state)
        
    def toggleVisibility(self):
        """ Change visibility menu item. """
        self.visibilityItem.SetItemLabel(self.HIDE_LABEL if self.visibilityItem.GetLabel() == self.SHOW_LABEL else self.SHOW_LABEL)
    
    def _close(self, event):
        """ On close click """
        self.closeCallback(self.dictionaryName)

    def _save(self, event):
        """ On save click """
        self.saveCallback(self.dictionaryName)

    def _saveAs(self, event):
        """ On save as click """
        self.saveAsCallback(self.dictionaryName)

    def _hide(self, event):
        """ On hide click """
        self.hideCallback(self.dictionaryName)
