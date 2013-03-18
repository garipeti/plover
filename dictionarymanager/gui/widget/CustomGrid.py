
from dictionarymanager.gui.widget.CustomGridCellEditor import \
    CustomGridCellEditor
from wxPython.grid import wxGrid, wxGridCellTextEditor


class CustomGrid(wxGrid):
    def __init__(self, *args, **kwargs):
        wxGrid.__init__(self, *args, **kwargs)
    
    def GetDefaultEditorForCell(self, row, col):
        #if col == 2:
            return CustomGridCellEditor
        #else:
        #    return wxGridCellTextEditor