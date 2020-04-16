from pcbnew import *

# All types of different DRAWSEGMENT shapes
STROKE_SEGMENT = 0
STROKE_RECT = 1
STROKE_ARC = 2
STROKE_CIRCLE = 3
STROKE_POLYGON = 4
STROKE_CURVE = 5
STROKE_MAP = {
    0: 'SEGMENT',
    1: 'RECT',
    2: 'ARC',
    3: 'CIRCLE',
    4: 'POLYGON',
    5: 'CURVE',
}

class PanelSettings:
    def __init__(self, board_file):
        self.board_file = board_file
        self.outline_width = FromMM(5)
        self.outline_hole = FromMM(2.5)
        self.spacing_width = FromMM(2)
        self.tab_width = FromMM(2.5)
        self.boards_x = 1
        self.boards_y = 1
        self.tabs_x = 1
        self.tabs_y = 1
        self.trim_silkscreen = False

class Panel:
    def __init__(self, settings):
        self.board = GetBoard()
        self.settings = settings
        self.page_offset = wxPoint(FromMM(20), FromMM(20))

    def create_panel(self):
        # Load the board to be panelized
        other_board = LoadBoard(self.settings.board_file)

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
        needed_width = 2 * self.settings.outline_width + self.settings.spacing_width + (self.settings.spacing_width + board_w) * self.settings.boards_x
        needed_height = 2 * self.settings.outline_width + self.settings.spacing_width + (self.settings.spacing_width + board_h) * self.settings.boards_y

        self.AddBoardOutlineSquare(0, 0, needed_width, needed_height, outline_thickness)
        self.AddBoardOutlineSquare(
            self.settings.outline_width,
            self.settings.outline_width,
            needed_width - 2*self.settings.outline_width,
            needed_height - 2*self.settings.outline_width,
            outline_thickness
        )

        # Add holes in the frame of the panel
        outline_w2 = self.settings.outline_width / 2
        hole_size = wxSize(self.settings.outline_hole, self.settings.outline_hole)
        self.AddHole(outline_w2, outline_w2, hole_size)
        self.AddHole(needed_width - outline_w2, outline_w2, hole_size)
        self.AddHole(outline_w2, needed_height - outline_w2, hole_size)

        # Add boards
        for y in range(self.settings.boards_y):
            for x in range(self.settings.boards_x):
                board_x = self.settings.outline_width + self.settings.spacing_width + (self.settings.spacing_width + board_w) * x
                board_y = self.settings.outline_width + self.settings.spacing_width + (self.settings.spacing_width + board_h) * y
                self.AppendBoard(other_board, board_x, board_y, outline_thickness)

        hole_size = wxSize(FromMM(0.5), FromMM(0.5))
        # Add the tabs for each of the boards
        for y in range(self.settings.boards_y+1):
            for x in range(self.settings.boards_x+1):
                board_x = self.settings.outline_width + self.settings.spacing_width + (self.settings.spacing_width + board_w) * x
                board_y = self.settings.outline_width + self.settings.spacing_width + (self.settings.spacing_width + board_h) * y
                x_spacing = board_w / (self.settings.tabs_x + 1)
                y_spacing = board_h / (self.settings.tabs_y + 1)

                if x != self.settings.boards_x:
                    for t in range(self.settings.tabs_x):
                        # Calculate the position of the tab
                        lx = board_x + (t+1) * x_spacing
                        ly = board_y - self.settings.spacing_width

                        # Open up both sides of the tab
                        for offset in [0, self.settings.spacing_width]:
                            hit_rect = EDA_RECT(
                                wxPoint(lx - self.settings.tab_width/2, ly + offset),
                                wxSize(self.settings.tab_width, 0)
                            )
                            # Check all drawing items for outline segments that need to be opened up
                            for drawing in self.board.GetDrawings():
                                if (type(drawing) == DRAWSEGMENT and
                                    drawing.GetShape() == STROKE_SEGMENT and
                                    drawing.GetLayerName() == "Edge.Cuts" and
                                    drawing.HitTest(hit_rect, False, 10)
                                ):
                                    self.BreakOutline(drawing, hit_rect, 0)
                                    break

                        # Add the holes slightly inset
                        for hole_offset in [FromMM(0.1), self.settings.spacing_width - FromMM(0.1)]:
                            self.AddHole(lx,             ly + hole_offset, hole_size)
                            for i in range(1, int(self.settings.tab_width / FromMM(2))+1):
                                self.AddHole(lx - FromMM(i), ly + hole_offset, hole_size)
                                self.AddHole(lx + FromMM(i), ly + hole_offset, hole_size)

                        # Add in the connecting lines
                        self.AddBoardOutline(hit_rect.GetLeft(), ly, hit_rect.GetLeft(), ly + self.settings.spacing_width, outline_thickness)
                        self.AddBoardOutline(hit_rect.GetRight(), ly, hit_rect.GetRight(), ly + self.settings.spacing_width, outline_thickness)

                if y != self.settings.boards_y:
                    for t in range(self.settings.tabs_y):
                        # Calculate the position of the tab
                        lx = board_x - self.settings.spacing_width
                        ly = board_y + (t+1) * y_spacing

                        # Open up both sides of the tab
                        for offset in [0, self.settings.spacing_width]:
                            hit_rect = EDA_RECT(
                                wxPoint(lx + offset, ly - self.settings.tab_width/2),
                                wxSize(0, self.settings.tab_width)
                            )
                            # Check all drawing items for outline segments that need to be opened up
                            for drawing in self.board.GetDrawings():
                                if (type(drawing) == DRAWSEGMENT and
                                    drawing.GetShape() == STROKE_SEGMENT and
                                    drawing.GetLayerName() == "Edge.Cuts" and
                                    drawing.HitTest(hit_rect, False, 10)
                                ):
                                    self.BreakOutline(drawing, hit_rect, 1)
                                    break

                        # Add the holes slightly inset
                        for hole_offset in [FromMM(0.1), self.settings.spacing_width - FromMM(0.1)]:
                            self.AddHole(lx + hole_offset, ly, hole_size)
                            for i in range(1, int(self.settings.tab_width / FromMM(2))+1):
                                self.AddHole(lx + hole_offset, ly - FromMM(i), hole_size)
                                self.AddHole(lx + hole_offset, ly + FromMM(i), hole_size)

                        # Add in the connecting lines
                        self.AddBoardOutline(lx, hit_rect.GetTop(), lx + self.settings.spacing_width, hit_rect.GetTop(), outline_thickness)
                        self.AddBoardOutline(lx, hit_rect.GetBottom(), lx + self.settings.spacing_width, hit_rect.GetBottom(), outline_thickness)

        self.board.Move(self.page_offset)

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

    def AddHole(self, x, y, size):
        # Create a new footprint
        module = MODULE(self.board)
        self.board.Add(module)
        # Create a new pad
        pad = D_PAD(module)
        module.Add(pad)
        # Set the size of the pad
        pad.SetSize(size)
        pad.SetDrillSize(size)
        # Set the pad to non-plated through hole
        pad.SetAttribute(PAD_ATTRIB_HOLE_NOT_PLATED)
        # Move the pad to the requested position
        module.SetPosition(wxPoint(x, y))

    def AppendBoard(self, other_board, board_x, board_y, outline_thickness):
        # Determine the bounding box of the board
        box = other_board.GetBoardEdgesBoundingBox()
        # Deflate the bounding box by half the outline thickness to account for
        # the width of the outline
        box.Inflate(-outline_thickness / 2, -outline_thickness / 2)
        # Get the origin of the bounding box
        origin_point = box.GetOrigin()
        # Determine the move offset needed to place the board at the correct position
        offset_point = wxPoint(board_x, board_y) - origin_point

        # Inflate the bounding box again for the silkscreen trim check
        box.Inflate(self.settings.spacing_width / 2, self.settings.spacing_width / 2)

        # Duplicate all the tracks
        for track in other_board.GetTracks():
            new_track = track.Duplicate()
            self.board.Add(new_track)
            new_track.Move(offset_point)
        # Duplicate all footprints
        for module in other_board.GetModules():
            module_dup = BOARD_ITEM.Duplicate(module)
            self.board.Add(module_dup)

            # Go through all graphical items and possibly remove silkscreen
            marked_for_deletion = []
            for drawing in module_dup.GraphicalItems():
                if self.TrimSilkscreenTest(drawing, box):
                    marked_for_deletion.append(drawing)
            for item in marked_for_deletion:
                item.DeleteStructure()

            module_dup.Move(offset_point)
        # Duplicate all graphical items
        for drawing in other_board.GetDrawings():
            # Possibly skip silkscreen drawing if trimmed
            if self.TrimSilkscreenTest(drawing, box):
                continue

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

    def TrimSilkscreenTest(self, drawing, hitbox):
        return (self.settings.trim_silkscreen and
                (drawing.GetLayerName() == "F.SilkS" or drawing.GetLayerName() == "B.SilkS") and
                not drawing.HitTest(hitbox, True, 0))
