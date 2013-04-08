from dictionarymanager.gui.widget.dmGridCellEditor import dmGridCellEditor
from dictionarymanager.gui.widget.dmGridCellRenderer import dmGridCellRenderer
from dictionarymanager.store.Store import Store
from wx._misc import BeginBusyCursor, EndBusyCursor
from wx.grid import EVT_GRID_LABEL_LEFT_CLICK, EVT_GRID_CELL_CHANGE
from wxPython.grid import wxGrid, wxGridCellAttr
import wx


class dmGrid(wxGrid):
    
    GRID_LABEL_STROKE = "Stroke"
    GRID_LABEL_TRANSLATION = "Translation"
    GRID_LABEL_DICTIONARIES = "Dictionaries"
    GRID_LABELS = [GRID_LABEL_STROKE, GRID_LABEL_TRANSLATION, GRID_LABEL_DICTIONARIES]
    
    def __init__(self, *args, **kwargs):
        wxGrid.__init__(self, *args, **kwargs)

    def CreateGrid(self, store, rows, cols):
        wxGrid.CreateGrid(self, rows, cols)
        self.store = store
    
        self._sortingColumn = 0
        self._sortingAsc = True
        self._cellChanging = False
        
        self.Bind(EVT_GRID_LABEL_LEFT_CLICK, self._onLabelClick)
        self.Bind(EVT_GRID_CELL_CHANGE, self._onCellChange)
        
        attr = wxGridCellAttr()
        attr.SetEditor(dmGridCellEditor())
        attr.SetRenderer(dmGridCellRenderer())
        self.SetColAttr(2, attr)
        self._changeGridLabel()
        
        self.store.subscribe("insert", self._onInsertRow)
        self.store.subscribe("delete", self._onDeleteRow)
        self.store.subscribe("update", self._onUpdateRow)
        
    def _onInsertRow(self, item, index):
        self.InsertRows(index, 1)
        self.SetCellValue(index, 0, item[Store.ATTR_STROKE])
        self.SetCellValue(index, 1, item[Store.ATTR_TRANSLATION])
        self.SetCellValue(index, 2, self.store.renderDictionaries(item))
    
    def _onDeleteRow(self, item, index):
        self.DeleteRows(index, 1)
        
    def _onUpdateRow(self, item, index):
        self.SetCellValue(index, 0, item[Store.ATTR_STROKE])
        self.SetCellValue(index, 1, item[Store.ATTR_TRANSLATION])
        self.SetCellValue(index, 2, self.store.renderDictionaries(item))
        
    def _onLabelClick(self, evt):
        """ Handle Grid label click"""
        
        if evt.Row == -1:
            propertyName = Store.ATTR_STROKE if evt.Col == 0 else Store.ATTR_TRANSLATION if evt.Col == 1 else Store.ATTR_DICTIONARIES
            self._sortingAsc = (not self._sortingAsc) if evt.Col == self._sortingColumn else True
            self._sortingColumn = evt.Col
            self._changeGridLabel()
            
            self._startGridJob("Progress", "Sorting...")
            self.MakeCellVisible(0, 0)
            try:
                self.store.sort(propertyName, self._sortingAsc)
            finally:
                self._endGridJob()
    
    def _changeGridLabel(self):
        directionLabel = " (asc)" if self._sortingAsc else " (desc)"
        for i in range(3):
            self.SetColLabelValue(i, self.GRID_LABELS[i] + (directionLabel if self._sortingColumn == i else ""))
    
    def _onCellChange(self, evt):
        """ Handle Grid Cell change """
    
        if self._cellChanging:
            return
        row = evt.Row
        self._cellChanging = True
        value = self.GetCellValue(row, evt.Col)
        if evt.Col == 0:
            row = self.store.changeStroke(row, value)
        elif evt.Col == 1:
            row = self.store.changeTranslation(row, value)
        else:
            # The new value is already in store just triggering reposition
            row = self.store.changeDictionaries(row, self.store.getDictionariesForRow(row))
        self._cellChanging = False
        if row is not None:
            self.MakeCellVisible(row, evt.Col)
            self.SelectRow(row)
    
    def _onProgressChange(self, percent):
        """ To track dictionary loading progress """
        
        if percent is not None:
            self.progress.Update(percent)
            
    def _startGridJob(self, title, text):
        BeginBusyCursor()
        self.progress = wx.ProgressDialog(title, text)
        self.BeginBatch()
        self.store.subscribe("progress", self._onProgressChange)
        
    def _endGridJob(self):
        self.store.unsubscribe("progress", self._onProgressChange)
        self.EndBatch()
        self.progress.Destroy()
        EndBusyCursor()
    