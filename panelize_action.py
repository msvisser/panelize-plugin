import pcbnew
import os
from .panelize import Panel, PanelSettings

# BOARD_FILE = "/Users/michiel/Kicad/fan-adapter/fan-adapter.kicad_pcb"
# BOARD_FILE = "/Users/michiel/Kicad/multi-serial/multi-serial.kicad_pcb"
BOARD_FILE = "/Users/michiel/Kicad/icebreaker-pmod/hyperram/v1.0b/ibp-hyperram.kicad_pcb"
# BOARD_FILE = "/Users/michiel/Kicad/icebreaker/hardware/v1.0e/icebreaker.kicad_pcb"

class PanelizePlugin(pcbnew.ActionPlugin):
    def defaults(self):
        self.name = "Create Panel"
        self.category = "Modify PCB"
        self.description = "Automatically create a panel of boards"
        self.show_toolbar_button = True
        self.icon_file_name = os.path.join(os.path.dirname(__file__), 'panelize_plugin.png')

    def Run(self):
        # Load the board to be panelized
        settings = PanelSettings()
        settings.boards_x = 3
        settings.boards_y = 2
        settings.tabs_x = 1
        settings.tabs_y = 2
        Panel().create_panel(BOARD_FILE, settings)
