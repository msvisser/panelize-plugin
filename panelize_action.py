import pcbnew
import os
import wx
from .panelize import Panel, PanelSettings
from .panelize_gui import PanelizePluginDialog

class PanelizePlugin(pcbnew.ActionPlugin):
    def defaults(self):
        self.name = "Create Panel"
        self.category = "Modify PCB"
        self.description = "Automatically create a panel of boards"
        self.show_toolbar_button = True
        self.icon_file_name = os.path.join(os.path.dirname(__file__), 'panelize_plugin.png')

        self.settings_history = PanelSettings("")

    def Run(self):
        # Check if the current board is empty
        if not pcbnew.GetBoard().IsEmpty():
            dlg = wx.MessageDialog(None,
                'A panel cannot be created when the board is non-empty. Delete everything, or create a new empty board.',
                'Cannot create panel',
                wx.OK
            )
            dlg.ShowModal()
            dlg.Destroy()
            return

        # Ask the user for the board and settings
        panelize_dialog = PanelizePluginDialog()
        panelize_dialog.LoadSettings(self.settings_history)
        ok = panelize_dialog.ShowModal()
        if not ok:
            panelize_dialog.Destroy()
            return
        settings = panelize_dialog.GetSettings()
        panelize_dialog.Destroy()
        self.settings_history = settings

        # Load the board to be panelized
        try:
            Panel(settings).create_panel()
        except IOError:
            dlg = wx.MessageDialog(None,
                'The board that was selected could not be opened.',
                'Cannot open board',
                wx.OK
            )
            dlg.ShowModal()
            dlg.Destroy()
