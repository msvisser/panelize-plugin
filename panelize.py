from pcbnew import *
from .constants import Layers, DrawSegmentShape

class PanelSettings:
    TABS_SPACE_EVENLY = 0
    TABS_SPACE_AROUND = 1
    TABS_SPACE_AUTO = 2

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
        self.tab_mode = PanelSettings.TABS_SPACE_EVENLY
        self.trim_silkscreen = False
        self.fiducial_mask = FromMM(2.5)
        self.fiducial_copper = FromMM(1)

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
            if type(drawing) == DRAWSEGMENT and drawing.GetLayer() == Layers.Edge_Cuts:
                outline_thickness = max(outline_thickness, drawing.GetWidth())
        box.Inflate(-outline_thickness / 2, -outline_thickness / 2)
        board_w = box.GetWidth()
        board_h = box.GetHeight()

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

        # Calculate half the outline width and 1.5 outline width
        outline_1w2 = self.settings.outline_width / 2
        outline_3w2 = self.settings.outline_width * 3 / 2

        # Add holes in the frame of the panel
        hole_size = wxSize(self.settings.outline_hole, self.settings.outline_hole)
        self.AddHole(outline_1w2, outline_1w2, hole_size)
        self.AddHole(needed_width - outline_1w2, outline_1w2, hole_size)
        self.AddHole(outline_1w2, needed_height - outline_1w2, hole_size)

        # Add fiducials to the front
        self.AddFiducial(outline_3w2, outline_1w2)
        self.AddFiducial(needed_width - outline_1w2, outline_3w2)
        self.AddFiducial(outline_1w2, needed_height - outline_3w2)
        # Add fiducials to the back
        self.AddFiducial(outline_1w2, outline_3w2, back=True)
        self.AddFiducial(needed_width - outline_3w2, outline_1w2, back=True)
        self.AddFiducial(outline_3w2, needed_height - outline_1w2, back=True)

        # Add boards
        for y in range(self.settings.boards_y):
            for x in range(self.settings.boards_x):
                board_x = self.settings.outline_width + self.settings.spacing_width + (self.settings.spacing_width + board_w) * x
                board_y = self.settings.outline_width + self.settings.spacing_width + (self.settings.spacing_width + board_h) * y
                self.AppendBoard(other_board, box, board_x, board_y, outline_thickness)

        hole_size = wxSize(FromMM(0.5), FromMM(0.5))
        tab_ver_offsets, tab_hor_offsets = self.GetTabOffsets(other_board, box, outline_thickness)
        # Add the tabs for each of the boards
        for y in range(self.settings.boards_y+1):
            for x in range(self.settings.boards_x+1):
                board_x = self.settings.outline_width + self.settings.spacing_width + (self.settings.spacing_width + board_w) * x
                board_y = self.settings.outline_width + self.settings.spacing_width + (self.settings.spacing_width + board_h) * y

                if x != self.settings.boards_x:
                    for tab_offset in tab_ver_offsets:
                        # Calculate the position of the tab
                        lx = board_x + tab_offset
                        ly = board_y - self.settings.spacing_width

                        hits = []
                        # Open up both sides of the tab
                        for offset in [0, self.settings.spacing_width]:
                            hit_rect = EDA_RECT(
                                wxPoint(lx - self.settings.tab_width/2, ly + offset),
                                wxSize(self.settings.tab_width, 0)
                            )
                            # Check all drawing items for outline segments that need to be opened up
                            for drawing in self.board.GetDrawings():
                                if (type(drawing) == DRAWSEGMENT and
                                    drawing.GetShape() == DrawSegmentShape.Segment and
                                    drawing.GetLayer() == Layers.Edge_Cuts and
                                    drawing.HitTest(hit_rect, False, 10)
                                ):
                                    hits.append((drawing, hit_rect))
                                    break

                        # If the number of hits is not two, this tab is missing one or more of its
                        # sides, therefore we should not add it
                        if len(hits) != 2:
                            continue

                        # Break the outline for each of the hits
                        for drawing, hit_rect in hits:
                            self.BreakOutline(drawing, hit_rect, 0)

                        # Add the holes slightly inset
                        for hole_offset in [FromMM(0.1), self.settings.spacing_width - FromMM(0.1)]:
                            self.AddHole(lx, ly + hole_offset, hole_size)
                            for i in range(1, int(self.settings.tab_width / FromMM(2))+1):
                                self.AddHole(lx - FromMM(i), ly + hole_offset, hole_size)
                                self.AddHole(lx + FromMM(i), ly + hole_offset, hole_size)

                        # Add in the connecting lines
                        self.AddBoardOutline(hit_rect.GetLeft(), ly, hit_rect.GetLeft(), ly + self.settings.spacing_width, outline_thickness)
                        self.AddBoardOutline(hit_rect.GetRight(), ly, hit_rect.GetRight(), ly + self.settings.spacing_width, outline_thickness)

                if y != self.settings.boards_y:
                    for tab_offset in tab_hor_offsets:
                        # Calculate the position of the tab
                        lx = board_x - self.settings.spacing_width
                        ly = board_y + tab_offset

                        hits = []
                        # Open up both sides of the tab
                        for offset in [0, self.settings.spacing_width]:
                            hit_rect = EDA_RECT(
                                wxPoint(lx + offset, ly - self.settings.tab_width/2),
                                wxSize(0, self.settings.tab_width)
                            )
                            # Check all drawing items for outline segments that need to be opened up
                            for drawing in self.board.GetDrawings():
                                if (type(drawing) == DRAWSEGMENT and
                                    drawing.GetShape() == DrawSegmentShape.Segment and
                                    drawing.GetLayer() == Layers.Edge_Cuts and
                                    drawing.HitTest(hit_rect, False, 10)
                                ):
                                    hits.append((drawing, hit_rect))
                                    break

                        # If the number of hits is not two, this tab is missing one or more of its
                        # sides, therefore we should not add it
                        if len(hits) != 2:
                            continue

                        # Break the outline for each of the hits
                        for drawing, hit_rect in hits:
                            self.BreakOutline(drawing, hit_rect, 1)

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
        line.SetLayer(Layers.Edge_Cuts)
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

    def AddFiducial(self, x, y, back=False):
        # Create a new footprint for the fiducial
        fid = MODULE(self.board)
        self.board.Add(fid)

        # Determine the layers for the mask and copper
        mask_layer = Layers.F_Mask if not back else Layers.B_Mask
        copper_layer = Layers.F_Cu if not back else Layers.B_Cu

        # Create the mask pad
        mask_pad = D_PAD(fid)
        fid.Add(mask_pad)
        mask_pad.SetAttribute(PAD_ATTRIB_SMD)
        mask_pad.SetSize(wxSize(self.settings.fiducial_mask, self.settings.fiducial_mask))
        mask_pad.SetLayerSet(LSET(mask_layer))

        # Create the copper pad
        copper_pad = D_PAD(fid)
        fid.Add(copper_pad)
        copper_pad.SetAttribute(PAD_ATTRIB_SMD)
        copper_pad.SetSize(wxSize(self.settings.fiducial_copper, self.settings.fiducial_copper))
        copper_pad.SetLayerSet(LSET(copper_layer))

        # Move the fiducial to the correct place
        fid.SetPosition(wxPoint(x, y))

    def AppendBoard(self, other_board, box, board_x, board_y, outline_thickness):
        # Clone the bounding box to make sure the inflate does not change it
        box = EDA_RECT(box.GetOrigin(), box.GetSize())
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
                (drawing.GetLayer() == Layers.F_SilkS or drawing.GetLayer() == Layers.B_SilkS) and
                not drawing.HitTest(hitbox, True, 0))

    def GetTabOffsets(self, other_board, box, outline_thickness):
        # Offsets of the tabs
        tab_ver_offsets = []
        tab_hor_offsets = []
        # Get the width and height of the board
        board_w = box.GetWidth()
        board_h = box.GetHeight()

        if self.settings.tab_mode == PanelSettings.TABS_SPACE_EVENLY:
            # Space the tabs evenly over the sides of the board
            tab_ver_offsets.extend(self.SpaceItemsEvenly(0, board_w, self.settings.tabs_x))
            tab_hor_offsets.extend(self.SpaceItemsEvenly(0, board_h, self.settings.tabs_y))
        elif self.settings.tab_mode == PanelSettings.TABS_SPACE_AROUND:
            # Space the tabs with equal space around them
            tab_ver_offsets.extend(self.SpaceItemsAround(0, board_w, self.settings.tabs_x))
            tab_hor_offsets.extend(self.SpaceItemsAround(0, board_h, self.settings.tabs_y))
        elif self.settings.tab_mode == PanelSettings.TABS_SPACE_AUTO:
            # Find the ranges of the board edges which follow the bounding box
            overlap_ver, overlap_hor = self.FindBoardEdgeRanges(other_board, box)

            # Distribute the vertical tabs based on the ranges
            tabs_ver_dist = self.ScoreDistributeTabs(overlap_ver, self.settings.tabs_x)
            for i, count in enumerate(tabs_ver_dist):
                if count > 0:
                    tab_ver_offsets.extend(self.SpaceItemsAround(overlap_ver[i][0], overlap_ver[i][1], count))
            # Distribute the horizontal tabs based on the ranges
            tabs_hor_dist = self.ScoreDistributeTabs(overlap_hor, self.settings.tabs_y)
            for i, count in enumerate(tabs_hor_dist):
                if count > 0:
                    tab_hor_offsets.extend(self.SpaceItemsAround(overlap_hor[i][0], overlap_hor[i][1], count))

        return (tab_ver_offsets, tab_hor_offsets)

    def SpaceItemsAround(self, low, high, count):
        # Space the items with equal space around each item
        result = []
        spacing = (high - low) / (count * 2)
        for t in range(count):
            result.append(low + (t*2+1) * spacing)
        return result

    def SpaceItemsEvenly(self, low, high, count):
        # Space the items with equal distance between them
        result = []
        spacing = (high - low) / (count + 1)
        for t in range(count):
            result.append(low + (t+1) * spacing)
        return result

    def FindBoardEdgeRanges(self, other_board, box):
        # Get the origin of the board
        origin_point = box.GetOrigin()
        # Get the width and heigth of the board
        board_w = box.GetWidth()
        board_h = box.GetHeight()

        # Hit rectangle to match the top edge
        rect_top = EDA_RECT(origin_point, wxSize(board_w, 0))
        rect_top.Inflate(0, 10)
        # Hit rectangle to match the left edge
        rect_left = EDA_RECT(origin_point, wxSize(0, board_h))
        rect_left.Inflate(10, 0)
        # Hit rectangle to match the bottom edge
        rect_bottom = EDA_RECT(origin_point + wxPoint(0, board_h), wxSize(board_w, 0))
        rect_bottom.Inflate(0, 10)
        # Hit rectangle to match the right edge
        rect_rigth = EDA_RECT(origin_point + wxPoint(board_w, 0), wxSize(0, board_h))
        rect_rigth.Inflate(10, 0)
        # List for all the hits of each edge
        hits_top = []
        hits_left = []
        hits_bottom = []
        hits_right = []

        # Check each drawing in the board
        for drawing in other_board.GetDrawings():
            # Make sure the drawing is a line segment and is on the Edge_Cuts layer
            if type(drawing) == DRAWSEGMENT and drawing.GetShape() == DrawSegmentShape.Segment and drawing.GetLayer() == Layers.Edge_Cuts:
                start = drawing.GetStart() - origin_point
                end = drawing.GetEnd() - origin_point
                # Check if this drawing hits any of the edges
                if drawing.HitTest(rect_top, True, 0):
                    hits_top.append((start[0], end[0]) if start[0] < end[0] else (end[0], start[0]))
                elif drawing.HitTest(rect_left, True, 0):
                    hits_left.append((start[1], end[1]) if start[1] < end[1] else (end[1], start[1]))
                elif drawing.HitTest(rect_bottom, True, 0):
                    hits_bottom.append((start[0], end[0]) if start[0] < end[0] else (end[0], start[0]))
                elif drawing.HitTest(rect_rigth, True, 0):
                    hits_right.append((start[1], end[1]) if start[1] < end[1] else (end[1], start[1]))

        # Sort all the ranges that were found
        hits_top.sort()
        hits_left.sort()
        hits_bottom.sort()
        hits_right.sort()

        # Filter out any range that is smaller than a single tab
        f = lambda i: i[1]-i[0] > self.settings.tab_width
        overlap_ver = filter(f, self.FindOverlappingRanges(hits_top, hits_bottom))
        overlap_hor = filter(f, self.FindOverlappingRanges(hits_left, hits_right))
        # Return the ranges that were found
        return (overlap_ver, overlap_hor)

    def FindOverlappingRanges(self, a, b):
        from collections import deque
        # Put the ranges is a queue
        aq, bq = deque(a), deque(b)
        results = []
        # While there is an item is both of the queues
        while len(aq) and len(bq):
            # Take the first item of the queues
            ia = aq.popleft()
            ib = bq.popleft()

            # Determine the overlapping range
            mx = max(ia[0], ib[0])
            mn = min(ia[1], ib[1])
            diff = mx-mn

            if diff > 0:
                # If there is no overlap, return the range with the highest end
                if ib[1] < ia[1]:
                    aq.appendleft(ia)
                else:
                    bq.appendleft(ib)
            else:
                # If there is overlap, insert the overlap into the results
                results.append((mx, mn))
                # Return a partial range to the queue if it is not consumed
                if mn < ia[1]:
                    aq.appendleft((mn+1, ia[1]))
                if mn < ib[1]:
                    bq.appendleft((mn+1, ib[1]))

        # Return the overlapping ranges
        return results

    def ScoreDistributeTabs(self, ranges, count):
        # Set the initial scores to the width of the range
        score_orig = [b - a for a, b in ranges]
        score = score_orig[:]
        # Set the number of tabs for each range to zero
        tabs = [0 for _ in ranges]

        # Distribute the tabs
        for _ in range(count):
            # Find the range with the highest score
            hs, hs_idx = 0, 0
            for i, s in enumerate(score):
                if s > hs:
                    hs, hs_idx = s, i
            # Assign a tab to the range
            tabs[hs_idx] += 1
            # Update the score of the range based on the number of tabs
            score[hs_idx] = (score_orig[hs_idx] - tabs[hs_idx] * self.settings.tab_width) / (tabs[hs_idx] + 1)

        # Return the number of tabs for each range
        return tabs
