from wxPython._controls import wxCheckListBox
from wxPython._core import wxSIZE_ALLOW_MINUS_ONE, WXK_SHIFT, wxLB_MULTIPLE
from wxPython.grid import wxPyGridCellEditor

class CustomGridCellEditor(wxPyGridCellEditor):
    def __init__(self, store):
        wxPyGridCellEditor.__init__(self)
        self.store = store

    def Create(self, parent, id, evtHandler):
        """
        Called to create the control, which must derive from wxControl.
        """
        self._tc = wxCheckListBox(parent, id, choices = [], style = wxLB_MULTIPLE)
        self.SetControl(self._tc)
        if evtHandler:
            self._tc.PushEventHandler(evtHandler)
    
    def GetItems(self):
        return self.store.getDictionaryNames()
        
    def SetSize(self, rect):
        """
        Called to position/size the edit control within the cell rectangle.
        If you don't fill the cell (the rect) then be sure to override
        PaintBackground and do something meaningful there.
        """
        self._tc.SetDimensions(rect.x, rect.y, rect.width+4, 100,
                               wxSIZE_ALLOW_MINUS_ONE)

    def Show(self, show, attr):
        self.base_Show(show, attr)
    
    def BeginEdit(self, row, col, grid):
        """
        Fetch the value from the table and prepare the edit control
        to begin editing.  Set the focus to the edit control.
        """
        self.items = self.GetItems()
        self._tc.Set(self.items)
        value = grid.GetTable().GetValue(row, col)
        if len(value) > 0:
            self.startValue = self.store.indexStringToIndexList(value)
        self._tc.SetChecked(self.startValue)
        self._tc.SetFocus()

    def EndEdit(self, row, col, grid):
        """
        Complete the editing of the current cell. Returns true if the value
        has changed.  If necessary, the control may be destroyed.
        """
        
        selections = self._tc.GetChecked()
        changed = False if len(selections) == len(self.startValue) else True
        if not changed:
            for selected in selections:
                if selected not in self.startValue :
                    changed = True
            
        if changed:
            grid.GetTable().SetValue(row, col, self.store.indexListToIndexString(selections)) # update the table

        self.startValue = []
        self._tc.SetChecked(self.startValue)
        return changed

    def Reset(self):
        """
        Reset the value in the control back to its starting value.
        """
        self._tc.SetChecked(self.startValue)


    def IsAcceptedKey(self, evt):
        """
        Return True to allow the given key to start editing: the base class
        version only checks that the event has no modifiers.  F2 is special
        and will always start the editor.
        """
        ## Oops, there's a bug here, we'll have to do it ourself..
        ##return self.base_IsAcceptedKey(evt)

        return (not (evt.ControlDown() or evt.AltDown()) and
                evt.GetKeyCode() != WXK_SHIFT)


    def StartingKey(self, evt):
        """
        If the editor is enabled by pressing keys on the grid, this will be
        called to let the editor do something about that first key if desired.
        """
        key = evt.GetKeyCode()
        #ch = None
        #if key in [WXK_NUMPAD0, WXK_NUMPAD1, WXK_NUMPAD2, WXK_NUMPAD3, WXK_NUMPAD4,
        #           WXK_NUMPAD5, WXK_NUMPAD6, WXK_NUMPAD7, WXK_NUMPAD8, WXK_NUMPAD9]:
        #    ch = ch = chr(ord('0') + key - WXK_NUMPAD0)

        #elif key < 256 and key >= 0 and chr(key) in string.printable:
        #    ch = chr(key)
        #    if not evt.ShiftDown():
        #        ch = ch.lower()

        #if ch is not None:
        #    self._tc.SetStringSelection(ch)
        #else:
        #    evt.Skip()


    def StartingClick(self):
        """
        If the editor is enabled by clicking on the cell, this method will be
        called to allow the editor to simulate the click on the control if
        needed.
        """
        


    def Destroy(self):
        """final cleanup"""
        self.base_Destroy()
    
    def Clone(self):
        """
        Create a new object which is the copy of this one
        """
        return CustomGridCellEditor(self.store)
