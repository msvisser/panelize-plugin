import pcbnew
import wx
import os
from .panelize import PanelSettings
from pcbnew import ActionPlugin, GetBoard

class PanelizePluginDialog(wx.Dialog):
    def __init__(self, parent=None):
        # wx.Dialog.__init__(self, parent, title='Create panelized board')
        wx.Dialog.__init__ ( self, parent, id = wx.ID_ANY, title = u"Create panelized board", pos = wx.DefaultPosition, size = wx.Size( 380,460 ), style = wx.CAPTION|wx.CLOSE_BOX|wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER )
        self.Bind(wx.EVT_CLOSE, self.OnCancel, id=self.GetId())

        # Create a panel
        panel = wx.Panel(self)

        # Create boxes
        vbox = wx.BoxSizer(wx.VERTICAL)
        item_grid = wx.FlexGridSizer(0, 2, 3, 5)
        item_grid.AddGrowableCol(1)

        # Create the file selector
        item_grid.Add(wx.StaticText(panel, label='Board file'), 1, wx.ALIGN_CENTRE_VERTICAL)
        file_group = wx.BoxSizer(wx.HORIZONTAL)
        self.file_name = wx.TextCtrl(panel)
        self.file_name.SetMinSize(wx.Size(400, 22))
        self.select_file = wx.Button(panel, label='Select file')
        self.Bind(wx.EVT_BUTTON, self.SelectFile, id=self.select_file.GetId())
        file_group.Add(self.file_name, 1, wx.EXPAND)
        file_group.Add(self.select_file, 0, wx.LEFT, 3)
        item_grid.Add(file_group, 1, wx.EXPAND)

        # Create the numerical options
        item_grid.Add(wx.StaticText(panel, label='Boards horizontal', size=wx.Size(120, -1)), 1, wx.ALIGN_CENTRE_VERTICAL)
        self.boards_x = wx.SpinCtrl(panel, style=wx.SP_ARROW_KEYS, min=1, value='1')
        item_grid.Add(self.boards_x, 1, wx.EXPAND)

        item_grid.Add(wx.StaticText(panel, label='Boards vertical'), 1, wx.ALIGN_CENTRE_VERTICAL)
        self.boards_y = wx.SpinCtrl(panel, style=wx.SP_ARROW_KEYS, min=1, value='1')
        item_grid.Add(self.boards_y, 1, wx.EXPAND)

        item_grid.Add(wx.StaticText(panel, label='Tabs horizontal', size=wx.Size(120, -1)), 1, wx.ALIGN_CENTRE_VERTICAL)
        self.tabs_y = wx.SpinCtrl(panel, style=wx.SP_ARROW_KEYS, value='1')
        item_grid.Add(self.tabs_y, 1, wx.EXPAND)

        item_grid.Add(wx.StaticText(panel, label='Tabs vertical'), 1, wx.ALIGN_CENTRE_VERTICAL)
        self.tabs_x = wx.SpinCtrl(panel, style=wx.SP_ARROW_KEYS, value='1')
        item_grid.Add(self.tabs_x, 1, wx.EXPAND)

        item_grid.Add(wx.StaticText(panel, label='Tab mode'), 1, wx.ALIGN_CENTRE_VERTICAL)
        self.tab_mode = wx.Choice(panel, choices=['Space evenly', 'Space around', 'Automatic'])
        item_grid.Add(self.tab_mode, 1, wx.EXPAND)

        item_grid.Add(wx.StaticText(panel, label='Frame width (mm)'), 1, wx.ALIGN_CENTRE_VERTICAL)
        self.outline_width = wx.SpinCtrlDouble(panel, style=wx.SP_ARROW_KEYS, min=0.1, inc=0.1, value='5.0')
        self.outline_width.SetDigits(1)
        item_grid.Add(self.outline_width, 1, wx.EXPAND)

        item_grid.Add(wx.StaticText(panel, label='Frame hole (mm)', size=wx.Size(120, -1)), 1, wx.ALIGN_CENTRE_VERTICAL)
        self.outline_hole = wx.SpinCtrlDouble(panel, style=wx.SP_ARROW_KEYS, min=0.1, inc=0.1, value='2.5')
        self.outline_hole.SetDigits(1)
        self.outline_hole.Enabled = False
        item_grid.Add(self.outline_hole, 1, wx.EXPAND)

        item_grid.Add(wx.StaticText(panel, label='Board spacing (mm)'), 1, wx.ALIGN_CENTRE_VERTICAL)
        self.spacing_width = wx.SpinCtrlDouble(panel, style=wx.SP_ARROW_KEYS, min=0.1, inc=0.1, value='2.0')
        self.spacing_width.SetDigits(1)
        item_grid.Add(self.spacing_width, 1, wx.EXPAND)

        item_grid.Add(wx.StaticText(panel, label='Tab width (mm)'), 1, wx.ALIGN_CENTRE_VERTICAL)
        self.tab_width = wx.SpinCtrlDouble(panel, style=wx.SP_ARROW_KEYS, min=0.1, inc=0.1, value='2.5')
        self.tab_width.SetDigits(1)
        item_grid.Add(self.tab_width, 1, wx.EXPAND)

        item_grid.Add(wx.StaticText(panel, label='Trim silkscreen'), 1, wx.ALIGN_CENTRE_VERTICAL)
        self.trim_silkscreen = wx.CheckBox(panel)
        item_grid.Add(self.trim_silkscreen, 1, wx.EXPAND)

        item_grid.Add(wx.StaticText(panel, label='Fiducial mask (mm)', size=wx.Size(140, -1)), 1, wx.ALIGN_CENTRE_VERTICAL)
        self.fiducial_mask = wx.SpinCtrlDouble(panel, style=wx.SP_ARROW_KEYS, min=0.1, inc=0.1, value='2.5')
        self.fiducial_mask.SetDigits(1)
        self.fiducial_mask.Enabled = False
        item_grid.Add(self.fiducial_mask, 1, wx.EXPAND)

        item_grid.Add(wx.StaticText(panel, label='Fiducial copper (mm)'), 1, wx.ALIGN_CENTRE_VERTICAL)
        self.fiducial_copper = wx.SpinCtrlDouble(panel, style=wx.SP_ARROW_KEYS, min=0.1, inc=0.1, value='1.0')
        self.fiducial_copper.SetDigits(1)
        self.fiducial_copper.Enabled = False
        item_grid.Add(self.fiducial_copper, 1, wx.EXPAND)

        # Create two buttons
        button_box = wx.BoxSizer(wx.HORIZONTAL)
        btn_cancel = wx.Button(panel, label='Cancel')
        self.Bind(wx.EVT_BUTTON, self.OnCancel, id=btn_cancel.GetId())
        button_box.Add(btn_cancel, 1, wx.RIGHT, 10)
        btn_create = wx.Button(panel, label='Create panel')
        self.Bind(wx.EVT_BUTTON, self.OnCreate, id=btn_create.GetId())
        button_box.Add(btn_create, 1)

        # Add the items to the vbox
        vbox.Add(item_grid, 1, wx.EXPAND | wx.ALIGN_CENTRE | wx.ALL, 10)
        vbox.Add(button_box, 0, wx.ALIGN_RIGHT | wx.LEFT | wx.RIGHT | wx.BOTTOM, 20)
        # Make the vbox
        panel.SetSizer(vbox)
        vbox.Fit(self)
        self.Centre()

    def OnCancel(self, event):
        self.EndModal(0)

    def OnCreate(self, event):
        self.EndModal(1)

    def SelectFile(self, event):
        search_path = os.path.expanduser("~")
        if self.file_name.GetValue() != "":
            search_path = os.path.dirname(self.file_name.GetValue())
        dlg = wx.FileDialog(self, "Select Board file", search_path, "", "*.kicad_pcb", wx.FD_OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            self.file_name.SetValue(dlg.GetPath())
        dlg.Destroy()

    def GetSettings(self):
        settings = PanelSettings(self.file_name.GetValue())
        settings.boards_x = self.boards_x.GetValue()
        settings.boards_y = self.boards_y.GetValue()
        settings.tabs_x = self.tabs_x.GetValue()
        settings.tabs_y = self.tabs_y.GetValue()
        settings.outline_width = pcbnew.FromMM(self.outline_width.GetValue())
        settings.outline_hole = pcbnew.FromMM(self.outline_hole.GetValue())
        settings.spacing_width = pcbnew.FromMM(self.spacing_width.GetValue())
        settings.tab_width = pcbnew.FromMM(self.tab_width.GetValue())
        settings.tab_mode = self.tab_mode.GetSelection()
        settings.trim_silkscreen = self.trim_silkscreen.IsChecked()
        settings.fiducial_mask = pcbnew.FromMM(self.fiducial_mask.GetValue())
        settings.fiducial_copper = pcbnew.FromMM(self.fiducial_copper.GetValue())
        return settings

    def LoadSettings(self, settings):
        self.file_name.SetValue(settings.board_file)
        self.boards_x.SetValue(settings.boards_x)
        self.boards_y.SetValue(settings.boards_y)
        self.tabs_x.SetValue(settings.tabs_x)
        self.tabs_y.SetValue(settings.tabs_y)
        self.outline_width.SetValue(pcbnew.ToMM(settings.outline_width))
        self.outline_hole.SetValue(pcbnew.ToMM(settings.outline_hole))
        self.spacing_width.SetValue(pcbnew.ToMM(settings.spacing_width))
        self.tab_width.SetValue(pcbnew.ToMM(settings.tab_width))
        self.tab_mode.SetSelection(settings.tab_mode)
        self.trim_silkscreen.SetValue(settings.trim_silkscreen)
        self.fiducial_mask.SetValue(pcbnew.ToMM(settings.fiducial_mask))
        self.fiducial_copper.SetValue(pcbnew.ToMM(settings.fiducial_copper))

        # self.file_name.SetValue("D:\Temp\Src.kicad_pcb")
