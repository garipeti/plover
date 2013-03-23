
from wx.grid import PyGridCellRenderer
import wx

class CutomGridCellRenderer(PyGridCellRenderer):   
    def __init__(self, store): 
        PyGridCellRenderer.__init__(self)
        self.store = store

    def Draw(self, grid, attr, dc, rect, row, col, isSelected):
        #text = ", ".join( grid.GetTable().getValueAsCustom(row, col, "list"))
        text = grid.GetCellValue(row, col)
        if text[:7] == "__dic__":
            text = self.store.indexStringToDictionaryFilenameString(text)
        dc.SetFont( attr.GetFont() ) 
        hAlign, vAlign = attr.GetAlignment()       
        if isSelected: 
            bg = grid.GetSelectionBackground() 
            fg = grid.GetSelectionForeground() 
        else: 
            bg = attr.GetBackgroundColour()
            fg = attr.GetTextColour() 
        dc.SetTextBackground(bg) 
        dc.SetTextForeground(fg)
        dc.SetBrush(wx.Brush(bg, wx.SOLID))
        dc.SetPen(wx.TRANSPARENT_PEN)
        dc.DrawRectangleRect(rect)            
        grid.DrawTextRectangle(dc, text, rect, hAlign, vAlign)

    def GetBestSize(self, grid, attr, dc, row, col): 
        text = self.valueToString(grid.GetCellValue(row, col))
        dc.SetFont(attr.GetFont())
        w, h = dc.GetTextExtent(text)                   
        return wx.Size(w, h)        

    def Clone(self): 
        return CutomGridCellRenderer()