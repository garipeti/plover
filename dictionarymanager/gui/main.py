"""

Plover Dictionary Manager

"""

from dictionarymanager.gui.widget.dmDictionaryMenu import dmDictionaryMenu
from dictionarymanager.gui.widget.dmGrid import dmGrid
from dictionarymanager.store import Store
from threading import Timer
from wx._misc import BeginBusyCursor, EndBusyCursor
from wxPython._core import wxOK, WXK_ESCAPE
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
    POSITION_MENU = 1
    
    MENU_ICON_FILE = "gear.png"
    
    def __init__(self, store = None, parent = None):
        
        wx.Dialog.__init__(self, parent,
                          title=dmFrame.TITLE,
                          pos=wx.DefaultPosition,
                          size=(800,600),
                          style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER
                                 | wx.MAXIMIZE_BOX | wx.MINIMIZE_BOX)
        
        self.parent = parent
        
        # configuration
        self.config = conf.get_config()
        
        # dictionary store
        self.store = store if store is not None and isinstance(store, Store.Store) else Store.Store(self.config)
        self.store.subscribe("dataChange", self._onDictionaryChange)
        
        # auxiliary variables
        self._keyTimer = None
        
        # loaded dictionaries
        loadedHolder = wx.BoxSizer(wx.HORIZONTAL)
        loadedHolder.Add(wx.StaticText(self, label=self.LOADED_LABEL), 0, flag=wx.TOP|wx.BOTTOM|wx.RIGHT|wx.ALIGN_CENTER_VERTICAL)
        loadedHolder.AddSpacer(5)
        self.loadedSizer = wx.BoxSizer(wx.HORIZONTAL)
        loadedHolder.Add(self.loadedSizer, 1, wx.EXPAND)
        self.dictionaryMenus = []
        menuIconPath = os.path.join(conf.ASSETS_DIR, self.MENU_ICON_FILE)
        self.menuIcon = wx.Image(menuIconPath, wx.BITMAP_TYPE_ANY).ConvertToBitmap()
        
        # search fields
        self.searchStrokeField = wx.TextCtrl(self, wx.ID_ANY, value="")
        self.searchTranslationField = wx.TextCtrl(self, wx.ID_ANY, value="")
        self.searchStrokeField.Bind(wx.EVT_KEY_UP, self._onFilterKeyUp)
        self.searchTranslationField.Bind(wx.EVT_KEY_UP, self._onFilterKeyUp)
        
        # search fields layout
        searchSizer = wx.BoxSizer(wx.HORIZONTAL)
        searchSizer.Add(wx.StaticText(self, label=self.FILTER_STROKE_LABEL), 0, flag=wx.TOP|wx.BOTTOM|wx.RIGHT|wx.ALIGN_CENTER_VERTICAL)
        searchSizer.Add(self.searchStrokeField, 1, wx.EXPAND)
        searchSizer.Add(wx.StaticText(self, label=self.FILTER_TRANSLATION_LABEL), 0, flag=wx.TOP|wx.BOTTOM|wx.RIGHT|wx.ALIGN_CENTER_VERTICAL)
        searchSizer.Add(self.searchTranslationField, 1, wx.EXPAND)
        
        # grid
        self.grid = dmGrid(self)
        self.grid.CreateGrid(self.store, 0, 3)
        self.grid.SetColSize(0, 250)
        self.grid.SetColSize(1, 300)
        self.grid.SetColSize(2, 150)
        
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
        
        self.SetSizer(self.sizer)
        self.Bind(wx.EVT_CLOSE, self._quit)
        self.Bind(wx.EVT_KEY_DOWN, self._keydown)
        
        # load dictionaries from config
        if self.parent is None:
            dict_files = conf.get_option_as_list(self.config, conf.DICTIONARY_CONFIG_SECTION, conf.DICTIONARY_FILE_OPTION)
            for dict_file in dict_files:
                self._readDictionary(dict_file)
        else:
            for dict_file in self.store.getDictionaryFilenames():
                self._addDictionaryToSidebar(dict_file)
            
        if self.parent is not None:
            self.grid._onTableChange(None)
    
    def _open(self, event=None):
        """ Open up File Dialog to load dictionary """
        
        dlg = wx.FileDialog(self, self.CHOOSE_DICTIONARY, ".", "", "*.*", wx.FD_OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            fullpath = dlg.GetPath()
            dirname, filename = os.path.split(fullpath)
            if dirname != conf.CONFIG_DIR:
                filename = fullpath
            dlg.Destroy()
            self._readDictionary(filename)
        else:
            dlg.Destroy()
    
    def saveAsDictionary(self, filename):
        """ Open up File Dialog to save dictionary """
        
        i = self.store.getDictionaryIndexByName(filename)
        if i is not None:
            dlg = wx.FileDialog(self, self.CHOOSE_DICTIONARY, ".", "", "*.*", wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
            if dlg.ShowModal() == wx.ID_OK:
                filename = dlg.GetFilename()
                dirname = dlg.GetDirectory()
                dlg.Destroy()
                
                BeginBusyCursor()
                try:
                    self.store.saveDictionary(i, os.path.join(dirname, filename))
                finally:
                    EndBusyCursor()
                
            else:
                dlg.Destroy()
    
    def _readDictionary(self, filename):
        try:
            self.store.loadDictionary(filename)
            self._addDictionaryToSidebar(filename)
        except ValueError as e:
            self._showErrorMessage(e)
    
    def _addDictionaryToSidebar(self, filename):
        box = wx.BoxSizer(wx.HORIZONTAL)
        box.Add(wx.StaticText(self, wx.ID_ANY, label=self.store.getDictionaryShortName(filename)), 
                flag=wx.TOP|wx.BOTTOM|wx.RIGHT|wx.ALIGN_CENTER_VERTICAL)
        
        menu = dmDictionaryMenu(filename, 
                                save_callback = self.saveDictionary,
                                save_as_callback = self.saveAsDictionary,
                                close_callback = self.closeDictionary,
                                hide_callback = self.toggleDictionaryVisibility)
        menu.setSaveState(False)
        self.dictionaryMenus.append(menu)
        
        menuButton = wx.BitmapButton(self, wx.ID_ANY, self.menuIcon)
        menuButton.Bind(wx.EVT_BUTTON, self._toggleDictionaryMenu)
        box.Add(menuButton)
        
        self.loadedSizer.Add(box)
        self.loadedSizer.Layout()
    
    def _toggleDictionaryMenu(self, evt):
        btn = evt.GetEventObject()
        pos = btn.GetPosition()
        pos.Set(pos.Get()[0], pos.Get()[1] + btn.GetSize().GetHeight())
        items = self.loadedSizer.GetChildren()
        for i, item in enumerate(items):
            if item.GetSizer().GetChildren()[self.POSITION_MENU].GetWindow() == btn:
                self.PopupMenu(self.dictionaryMenus[i], pos)
    
    def _showErrorMessage(self, error):
        dlg = wx.MessageDialog(self, str(error), style=wxOK)
        dlg.ShowModal()
        dlg.Destroy()
    
    def closeDictionary(self, filename):
        i = self.store.getDictionaryIndexByName(filename)
        if i is not None:
            self.loadedSizer.Hide(i)
            self.loadedSizer.Remove(i)
            self.sizer.Layout()
            self.store.closeDictionary(i)

    def _onDictionaryChange(self, index, hasChanges):
        items = self.loadedSizer.GetChildren()
        if len(items) > index:
            self.dictionaryMenus[index].setSaveState(hasChanges)
    
    def saveDictionary(self, filename):
        i = self.store.getDictionaryIndexByName(filename)
        if i is not None:
            BeginBusyCursor()
            try:
                self.store.saveDictionary(i)
                self.dictionaryMenus[i].setSaveState(False)
            finally:
                EndBusyCursor()
                
    def toggleDictionaryVisibility(self, filename):
        print(filename)
        i = self.store.getDictionaryIndexByName(filename)
        print(i)
        if i is not None:
            BeginBusyCursor()
            self.grid.MakeCellVisible(0, 0)
            try:
                self.dictionaryMenus[i].toggleVisibility()
                self.store.toggleDictionaryVisibility(i)
            finally:
                EndBusyCursor()
        
    def _onFilterKeyUp(self, evt):
        """ KeyUp event on search fields """
        
        if self._keyTimer is not None:
            self._keyTimer.cancel()
        
        self._keyTimer = Timer(0.1, self._callFilterChange)
        self._keyTimer.start()
    
    def _callFilterChange(self):
        wx.CallAfter(self._onFilterChange)
    
    def _onFilterChange(self):
        """ KeyUp event on search fields """
        
        if self._keyTimer is not None:
            self._keyTimer.cancel()
            self._keyTimer = None
            
        filters = {
                   Store.Store.ATTR_STROKE: self.searchStrokeField.GetValue(),
                   Store.Store.ATTR_TRANSLATION: self.searchTranslationField.GetValue()
                }
        
        BeginBusyCursor()
        self.grid.MakeCellVisible(0, 0)
        try:
            self.store.filter(filters)
        finally:
            EndBusyCursor()
        
    def _addRow(self, event=None):
        """ Add new translation to the grid """
        row = self.store.insertItem()
        if len(self.loadedSizer.GetChildren()) == 1:
            self.store.setDictionariesForRow(row, [0])
        self.grid.MakeCellVisible(row, 0)
        self.grid.ClearSelection()
        self.grid.SetGridCursor(row, 0)
        self.grid.EnableCellEditControl()
    
    def _save(self, event=None):
        """ Save dictionaries """
        
        self.store.saveDictionaries()
    
    def _quit(self, event=None):
        """ Quit application """
        
        if self.parent is not None:
            self.Hide()
        else:
            self.Destroy()

    def _keydown(self, event):
        """ Key down event handler """
        if self.parent is not None and event.GetKeyCode() == WXK_ESCAPE:
            self.Hide()
        else:
            event.Skip()

    def focusOnFilterStroke(self):
        self.searchStrokeField.SetFocus()

    def focusOnFilterTranslation(self):
        self.searchTranslationField.SetFocus()
