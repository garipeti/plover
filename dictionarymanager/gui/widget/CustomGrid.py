from wxPython.grid import wxGrid


class CustomGrid(wxGrid):
    def __init__(self, *args, **kwargs):
        wxGrid.__init__(self, *args, **kwargs)
