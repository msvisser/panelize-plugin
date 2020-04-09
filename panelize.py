from pcbnew import *

class PanelSettings:
    def __init__(self, board_file):
        self.board_file = board_file
        self.outline_width = FromMM(5)
        self.spacing_width = FromMM(2)
        self.tab_width = FromMM(2)
        self.boards_x = 1
        self.boards_y = 1
        self.tabs_x = 0
        self.tabs_y = 0

class Panel:
    def __init__(self):
        self.board = GetBoard()

    def create_panel(self, settings):
        # Load the board to be panelized
        other_board = LoadBoard(settings.board_file)

        # Get the thickness of the outline
        box = other_board.GetBoardEdgesBoundingBox()
        outline_thickness = 0
        for drawing in other_board.GetDrawings():
            if type(drawing) == DRAWSEGMENT and drawing.GetLayer() == 44:
                outline_thickness = max(outline_thickness, drawing.GetWidth())
        board_w = box.GetWidth() - outline_thickness
        board_h = box.GetHeight() - outline_thickness

        # Update the number of copper layers if needed
        this_copper = self.board.GetCopperLayerCount()
        other_copper = other_board.GetCopperLayerCount()
        if other_copper > this_copper:
            self.board.SetCopperLayerCount(other_copper)

        # Add outline
        needed_width = 2 * settings.outline_width + settings.spacing_width + (settings.spacing_width + board_w) * settings.boards_x
        needed_height = 2 * settings.outline_width + settings.spacing_width + (settings.spacing_width + board_h) * settings.boards_y

        self.AddBoardOutlineSquare(0, 0, needed_width, needed_height, outline_thickness)
        self.AddBoardOutlineSquare(
            settings.outline_width,
            settings.outline_width,
            needed_width - 2*settings.outline_width,
            needed_height - 2*settings.outline_width,
            outline_thickness
        )

        # Add boards
        for y in range(settings.boards_y):
            for x in range(settings.boards_x):
                board_x = settings.outline_width + settings.spacing_width + (settings.spacing_width + board_w) * x
                board_y = settings.outline_width + settings.spacing_width + (settings.spacing_width + board_h) * y
                self.AppendBoard(other_board, board_x, board_y, outline_thickness)

        # Add the tabs for each of the boards
        for y in range(settings.boards_y+1):
            for x in range(settings.boards_x+1):
                board_x = settings.outline_width + settings.spacing_width + (settings.spacing_width + board_w) * x
                board_y = settings.outline_width + settings.spacing_width + (settings.spacing_width + board_h) * y
                x_spacing = board_w / (settings.tabs_x + 1)
                y_spacing = board_h / (settings.tabs_y + 1)

                if x != settings.boards_x:
                    for t in range(settings.tabs_x):
                        # Calculate the position of the tab
                        lx = board_x + (t+1) * x_spacing
                        ly = board_y - settings.spacing_width

                        # Open up both sides of the tab
                        for offset in [0, settings.spacing_width]:
                            hit_rect = EDA_RECT(
                                wxPoint(lx - settings.tab_width/2, ly + offset),
                                wxSize(settings.tab_width, 0)
                            )
                            # Check all drawing items for outline segments that need to be opened up
                            for drawing in self.board.GetDrawings():
                                if type(drawing) == DRAWSEGMENT and drawing.GetLayer() == 44 and drawing.HitTest(hit_rect, False, 10):
                                    self.BreakOutline(drawing, hit_rect, 0)
                                    break

                        # Add in the connecting lines
                        self.AddBoardOutline(hit_rect.GetLeft(), ly, hit_rect.GetLeft(), ly + settings.spacing_width, outline_thickness)
                        self.AddBoardOutline(hit_rect.GetRight(), ly, hit_rect.GetRight(), ly + settings.spacing_width, outline_thickness)

                if y != settings.boards_y:
                    for t in range(settings.tabs_y):
                        # Calculate the position of the tab
                        lx = board_x - settings.spacing_width
                        ly = board_y + (t+1) * y_spacing

                        # Open up both sides of the tab
                        for offset in [0, settings.spacing_width]:
                            hit_rect = EDA_RECT(
                                wxPoint(lx + offset, ly - settings.tab_width/2),
                                wxSize(0, settings.tab_width)
                            )
                            # Check all drawing items for outline segments that need to be opened up
                            for drawing in self.board.GetDrawings():
                                if type(drawing) == DRAWSEGMENT and drawing.GetLayer() == 44 and drawing.HitTest(hit_rect, False, 10):
                                    self.BreakOutline(drawing, hit_rect, 1)
                                    break

                        # Add in the connecting lines
                        self.AddBoardOutline(lx, hit_rect.GetTop(), lx + settings.spacing_width, hit_rect.GetTop(), outline_thickness)
                        self.AddBoardOutline(lx, hit_rect.GetBottom(), lx + settings.spacing_width, hit_rect.GetBottom(), outline_thickness)

    def AddBoardOutline(self, x0, y0, x1, y1, width=FromMM(0.25)):
        line = DRAWSEGMENT(self.board)
        line.SetWidth(width)
        line.SetStart(wxPoint(x0, y0))
        line.SetEnd(wxPoint(x1, y1))
        line.SetLayer(44)
        self.board.Add(line)

    def AddBoardOutlineSquare(self, x, y, w, h, width=FromMM(0.25)):
        self.AddBoardOutline(x, y, x + w, y, width)
        self.AddBoardOutline(x + w, y, x + w, y + h, width)
        self.AddBoardOutline(x, y + h, x + w, y + h, width)
        self.AddBoardOutline(x, y, x, y + h, width)

    def BreakOutline(self, drawing, rect, direction):
        # Get the thickness of the original line
        outline_thickness = drawing.GetWidth()
        # Get the start and end point
        start = drawing.GetStart()
        end = drawing.GetEnd()
        # Swap the start and end coordinates if the line is backwards in the current direction
        start_x = start[0] if start[direction] < end[direction] else end[0]
        start_y = start[1] if start[direction] < end[direction] else end[1]
        end_x = end[0] if start[direction] < end[direction] else start[0]
        end_y = end[1] if start[direction] < end[direction] else start[1]
        # Remove the original line
        self.board.Delete(drawing)
        # Add two lines to replace the deleted line with a split
        self.AddBoardOutline(start_x, start_y, rect.GetLeft(), rect.GetTop(), outline_thickness)
        self.AddBoardOutline(rect.GetRight(), rect.GetBottom(), end_x, end_y, outline_thickness)

    def AppendBoard(self, other_board, board_x, board_y, outline_thickness):
        # Determine the bounding box of the board
        box = other_board.GetBoardEdgesBoundingBox()
        # Calculate the origin of the board, add half outline thickness since the bounding box is
        # determined on the outside of the lines
        origin_point = wxPoint(box.GetLeft() + outline_thickness/2, box.GetTop() + outline_thickness/2)
        # Determine the move offset needed to place the board at the correct position
        offset_point = wxPoint(board_x, board_y) - origin_point

        # Duplicate all the tracks
        for track in other_board.GetTracks():
            new_track = track.Duplicate()
            self.board.Add(new_track)
            new_track.Move(offset_point)
        # Duplicate all footprints
        for module in other_board.GetModules():
            module_dup = BOARD_ITEM.Duplicate(module)
            self.board.Add(module_dup)
            module_dup.Move(offset_point)
        # Duplicate all graphical items
        for drawing in other_board.GetDrawings():
            drawing_dup = drawing.Duplicate()
            self.board.Add(drawing_dup)
            drawing_dup.Move(offset_point)
        # Duplicate all zones
        for i in range(other_board.GetAreaCount()):
            zone = other_board.GetArea(i)
            zone_dup = zone.Duplicate()
            self.board.Add(zone_dup)
            zone_dup.Move(offset_point)
        # Duplicate all the nets
        for net in other_board.GetNetInfo().NetsByNetcode():
            self.board.Add(other_board.GetNetInfo().GetNetItem(net))

        # Refresh the board netlist
        self.board.BuildListOfNets()
        self.board.SynchronizeNetsAndNetClasses()
        self.board.BuildConnectivity()
