from dictionarymanager.store.Store import Store
from wx.grid import PyGridTableBase
import wx.grid as Grid

class dmGridTable(PyGridTableBase):
    """
    A custom wx.Grid Table using user supplied data
    """
    def __init__(self, store, colkeys, colnames, plugins):
        """ Init GridTableBase with a Store. """
        
        # The base class must be initialized *first*
        PyGridTableBase.__init__(self)
        self.store = store
        self.colkeys = colkeys
        self.colnames = colnames
        self.plugins = plugins or {}
        # we need to store the row length and column length to
        # see if the table has changed size
        self._rows = self.GetNumberRows()
        self._cols = self.GetNumberCols()

    def GetNumberCols(self):
        return len(self.colnames)

    def GetNumberRows(self):
        return self.store.getCount()

    def GetColKey(self, col):
        return self.colkeys[col]

    def GetColLabelValue(self, col):
        return self.colnames[col]
    
    def SetColLabelValue(self, col, name):
        self.colnames[col] = name
    
    def GetRowLabelValue(self, row):
        return str(row)

    def GetValue(self, row, col):
        return str(self.store.rows[row][self.GetColKey(col)])

    def GetRawValue(self, row, col):
        return self.store.rows[row][self.GetColKey(col)]

    def SetValue(self, row, col, value):
        item = self.store.rows[row]
        if col == 0:
            self.store.changeStroke(row, value)
        elif col == 1:
            self.store.changeTranslation(row, value)
        else:
            # editor already applied the modification
            value = item[Store.ATTR_DICTIONARIES]
            self.store.changeDictionaries(row, value)
        
        #self.store.rows[row][self.GetColKey(col)] = value
    
    def ResetView(self, grid):
        """
        (Grid) -> Reset the grid view.   Call this to
        update the grid if rows and columns have been added or deleted
        """
        grid.BeginBatch()

        for current, new, delmsg, addmsg in [
            (self._rows, self.GetNumberRows(), Grid.GRIDTABLE_NOTIFY_ROWS_DELETED, Grid.GRIDTABLE_NOTIFY_ROWS_APPENDED),
            (self._cols, self.GetNumberCols(), Grid.GRIDTABLE_NOTIFY_COLS_DELETED, Grid.GRIDTABLE_NOTIFY_COLS_APPENDED)
        ]:
            if new < current:
                msg = Grid.GridTableMessage(self,delmsg,new,current-new)
                grid.ProcessTableMessage(msg)
            elif new > current:
                msg = Grid.GridTableMessage(self,addmsg,new-current)
                grid.ProcessTableMessage(msg)
                self.UpdateValues(grid)

        grid.EndBatch()

        self._rows = self.GetNumberRows()
        self._cols = self.GetNumberCols()
        # update the column rendering plugins
        self._updateColAttrs(grid)

        # update the scrollbars and the displayed part of the grid
        grid.AdjustScrollbars()
        grid.ForceRefresh()
        
    def UpdateValues(self, grid):
        """Update all displayed values"""
        # This sends an event to the grid table to update all of the values
        msg = Grid.GridTableMessage(self, Grid.GRIDTABLE_REQUEST_VIEW_GET_VALUES)
        grid.ProcessTableMessage(msg)

    def _updateColAttrs(self, grid):
        """
        wx.Grid -> update the column attributes to add the
        appropriate renderer given the column name.  (renderers
        are stored in the self.plugins dictionary)

        Otherwise default to the default renderer.
        """
        col = 0
        for colkey in self.colkeys:
            attr = Grid.GridCellAttr()
            if colkey in self.plugins:
                plugin = self.plugins[colkey]
                renderer = plugin[0]()
                editor = plugin[1]()
                
                attr.SetRenderer(renderer)
                attr.SetEditor(editor)

            grid.SetColAttr(col, attr)
            col += 1
