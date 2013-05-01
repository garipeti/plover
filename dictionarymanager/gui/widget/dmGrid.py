from dictionarymanager.gui.widget.dmGridCellEditor import dmGridCellEditor
from dictionarymanager.gui.widget.dmGridCellRenderer import dmGridCellRenderer
from dictionarymanager.gui.widget.dmGridTable import dmGridTable
from dictionarymanager.store.Store import Store
from wx._misc import BeginBusyCursor, EndBusyCursor, EVT_TIMER
from wx.grid import EVT_GRID_LABEL_LEFT_CLICK, EVT_GRID_CELL_CHANGE
from wxPython.grid import wxGrid
import wx
from wx._core import EVT_MOUSEWHEEL


class dmGrid(wxGrid):
    
    GRID_LABEL_STROKE = "Stroke"
    GRID_LABEL_TRANSLATION = "Translation"
    GRID_LABEL_DICTIONARIES = "Dictionaries"
    GRID_LABELS = [GRID_LABEL_STROKE, GRID_LABEL_TRANSLATION, GRID_LABEL_DICTIONARIES]
    
    def __init__(self, *args, **kwargs):
        wxGrid.__init__(self, *args, **kwargs)
        
        self._changedRow = None

    def CreateGrid(self, store, rows, cols):
        wxGrid.CreateGrid(self, rows, cols)
        self.store = store
        
        self._table = dmGridTable(self.store, [Store.ATTR_STROKE, 
                                               Store.ATTR_TRANSLATION, 
                                               Store.ATTR_DICTIONARIES], 
                                  self.GRID_LABELS[:],
                                  {
                                   Store.ATTR_DICTIONARIES: [dmGridCellRenderer, dmGridCellEditor]
                                   })
        self.SetTable(self._table)
    
        self._sortingColumn = 0
        self._sortingAsc = None
        
        self.Bind(EVT_GRID_LABEL_LEFT_CLICK, self._onLabelClick)
        self.Bind(EVT_GRID_CELL_CHANGE, self._onCellChange)
        self.Bind(EVT_MOUSEWHEEL, self._onMouseScroll)
        
        self._changeGridLabel()
        
        self.store.subscribe("tableChange", self._onTableChange)
        
    def _onMouseScroll(self, evt):
        if evt.ControlDown():
            self.changeZoomLevel(evt.GetWheelRotation())

    def changeZoomLevel(self, direction):
        font = self.GetDefaultCellFont()
        size = font.GetPointSize()
        if direction > 0:
            newSize = size + 1
        elif size > 5:
            newSize = size - 1
        else:
            return
        font.SetPointSize(newSize)
        
        # TODO: is there another way which is fast enough?
        dc = wx.ScreenDC()
        dc.SetFont(font)
        w, h, d, l = dc.GetFullTextExtent("|")
        self.SetDefaultCellFont(font)
        self.SetDefaultRowSize(h + d + l + 5)
        
        self._onTableChange(self.store)
    
    def _onTableChange(self, store):
        self._table.ResetView(self)
    
    def _onLabelClick(self, evt):
        """ Handle Grid label click"""
        
        if evt.Row == -1:
            if self._sortingAsc == False and evt.Col == self._sortingColumn:
                self._sortingAsc = None
                self._changeGridLabel()
                self.store.resetOrder()
            else:
                if self._sortingAsc is None:
                    self._sortingAsc = False
                
                propertyName = Store.ATTR_STROKE if evt.Col == 0 else Store.ATTR_TRANSLATION if evt.Col == 1 else Store.ATTR_DICTIONARIES
                self._sortingAsc = (not self._sortingAsc) if evt.Col == self._sortingColumn else True
                self._sortingColumn = evt.Col
                self._changeGridLabel()
                self.store.sort(propertyName, self._sortingAsc)
            
    
    def _changeGridLabel(self):
        directionLabel = ""
        if self._sortingAsc is not None:
            directionLabel = " (asc)" if self._sortingAsc else " (desc)"
        for i in range(3):
            self._table.SetColLabelValue(i, self.GRID_LABELS[i] + (directionLabel if self._sortingColumn == i else ""))
    
    def _onCellChange(self, evt):
        """ Handle Grid Cell change """
    
        row = evt.Row
        item = self.store.rows[row]
        
        self._changedRow = item
        # TODO: find an event instead of a timer
        # grid needs time to finish up before we can reorder grid
        self.timer = wx.Timer(self)
        self.Bind(EVT_TIMER, self.afterChange, self.timer)
        self.timer.Start(10)
        
    def afterChange(self, evt):
        self.timer.Stop()
        self.timer = None
        self.store.reSort()
        if self._changedRow is not None and self._changedRow in self.store.rows:
            index = self.store.rows.index(self._changedRow)
            self.MakeCellVisible(index, 1)
            self.SelectRow(index)
            
        