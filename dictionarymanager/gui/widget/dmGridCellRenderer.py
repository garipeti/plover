
from wx.grid import PyGridCellRenderer
import wx

class dmGridCellRenderer(PyGridCellRenderer):   
    def __init__(self): 
        PyGridCellRenderer.__init__(self)
    
    def Draw(self, grid, attr, dc, rect, row, col, isSelected):
        if col == 3:
            text = ", ".join(grid.store.getDictionaryShortNamesForRow(row))
        else:
            text = grid.GetCellValue(row, col)
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

    #def GetBestSize(self, grid, attr, dc, row, col): 
    #    text = self.valueToString(grid.GetCellValue(row, col))
    #    dc.SetFont(attr.GetFont())
    #    w, h = dc.GetTextExtent(text)                   
    #    return wx.Size(w, h)        

    def Clone(self): 
        return dmGridCellRenderer()