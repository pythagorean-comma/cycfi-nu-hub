"""Build the PCB for the design in design.py.

Two layers. GND is poured on both and everything else is a handful of tracks,
because there are only seven nets and no components to route between.

The outline is not this board's to choose. It is the Internal Breakout's --
50 x 35 mm with rounded corners and four M2 holes on 45 x 30 mm centres,
measured off Cycfi's own internal_breakout.brd -- so that a mount, a cavity or
an enclosure pocket cut for a breakout takes a hub as well. See
circuit.MOUNTING_PATTERN for what in that is transcribed and what is rounded.

Inside it the board is three bands. Six signal headers across the north, six
power headers across the south, and between them the middle band carrying the
2x5 to the breakout at its east end, the fan-in to it, the V+ bus and the
grounding pad. Channels run in string order from CH1 at the west, so reading
the board left to right reads the strings low to high, and the two capsule
cable bundles still leave on opposite edges with the trunk leaving east.

The one part of this that is not obvious is how the six channels reach the
2x5, and it is forced by the connector's own geometry rather than chosen. Its
pads are 1.35 mm on a 2.00 mm pitch, so the clear gap between two of them is
0.65 mm and a track needs 0.80 mm -- see the assertion in rules.py. Nothing
can be routed between the pads of a 2.00 mm header, which means the far row
cannot be reached from the near side at all. So:

    odd  pins 3/5/7 (CH5/CH3/CH1) are the west row, and are reached
         directly from the west on F.Cu;
    even pins 4/6/8 (CH6/CH4/CH2) are the east row, and go north of the
         signal headers on B.Cu, east past the connector, and come back
         into it from the outside.

Which of the two rows is near is itself a placement decision, and it is the
one that makes the fan-in planar. The connector puts CH1/CH2 at its southern
pair and CH5/CH6 at its northern one, so a channel's target y falls as its
number falls -- and with CH1 at the *west* end of the board, the westmost
channel wants the southernmost lane. That nests. Mirror the board and every
lane crosses every other one.

The fan-in is the one thing the new outline did not change. What it did change
is how little room there is to do it in: the strip's lanes ran through open
copper along the north edge, and here the same band has the two north mounting
holes sitting in it, 2.5 mm in from a rounded corner. The lanes clear those by
going under them rather than around -- see check_holes_clear(), which is the
only thing on the board that knows an unplated hole is there at all.

Track waypoints are given relative to real pad positions read back from the
placed footprints, so nothing here depends on guessing KiCad's rotation
conventions -- and the assertions in check_placement() are what turn a wrong
guess into a failed build rather than a shorted board.
"""

import json
import pathlib
import sys

import pcbnew

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import design as circuit  # noqa: E402
import kicad  # noqa: E402
import rules  # noqa: E402
# The schematic writer's UUID helper, so the board derives exactly the same
# symbol identifiers the schematic wrote rather than re-implementing the hash.
from kisch import _uuid as symbol_uuid  # noqa: E402

FOOTPRINT_DIR = kicad.FOOTPRINT_DIR

TRACK = rules.TRACK
POWER_TRACK = rules.POWER_TRACK
VIA_DIAMETER = rules.VIA_DIAMETER
VIA_DRILL = rules.VIA_DRILL
CLEARANCE = rules.CLEARANCE
KEEPOUT = rules.PAD_KEEPOUT

F = pcbnew.F_Cu
B = pcbnew.B_Cu

# -- the outline, which is Cycfi's ------------------------------------------
# Every number in this block comes from circuit.MOUNTING_PATTERN rather than
# being written here, so there is one place the breakout's geometry is
# recorded and one place it would have to change if a v2.6 board is ever
# measured. BOARD_R is the only figure this file chooses: Cycfi's own four
# corner arcs disagree with each other, so a true fillet is drawn at the
# radius three of the four work out to.
BOARD_W, BOARD_H = circuit.MOUNTING_PATTERN["outline"]
BOARD_R = 1.75

_HOLE_INSET = circuit.MOUNTING_PATTERN["hole_inset"]
HOLE_DRILL = circuit.MOUNTING_PATTERN["hole_drill"]

# -- the three bands ---------------------------------------------------------
Y_SIGNAL = 7.5        # S1..S6 pad row, clear of the north mounting holes
Y_POWER = 27.5        # P1..P6 pad row, clear of the south ones
CH_X0 = 7.5           # centre of the CH1 column
CH_PITCH = 7.0        # 6.2 mm is the widest 3-way 2.00 mm housing, so this
                      # leaves 0.8 mm between two of them side by side

# Six columns on a 7 mm pitch put 35 mm between CH1's centre and CH6's, and a
# 1x03's courtyard adds 3.5 mm at each end. 42 mm of the 50 available, centred,
# which is what fixes CH_X0 -- there is no slack in it to move them east.
assert CH_X0 - 3.5 == BOARD_W - (CH_X0 + 5 * CH_PITCH + 3.5), (
    "the channel columns are no longer centred on the board")

# J1's pin 1. The footprint steps +2 in x to the east row and +2 in y to the
# next pair, so this one corner fixes all ten pads.
#
# It sits at the east end of the middle band rather than against the east edge,
# and the 3.5 mm beyond its courtyard is not slack: the three descents to the
# east row live in it. Its y is what leaves a clear band between the signal
# row and the top of the connector for the lanes to cross in.
J1_PIN1 = (43.0, 13.0)

# -- lanes -------------------------------------------------------------------
# The even channels' route north of the signal headers, outermost first: CH2
# starts furthest west so it takes the lane nearest the north edge, and comes
# back down the east side furthest out. Nesting in both axes at once is what
# keeps the three of them from crossing.
#
# North of the signal row and not south of it, and that is not a free choice.
# Each lane is reached by a drop out of its own header, and each descent
# begins at its own lane -- so the outermost lane has to be the one furthest
# from the header row *and* clear of every descent. Those are the same
# direction only on the side the descents run away from. Put the lanes in the
# equally roomy band south of the row and CH2's lane crosses CH4's descent;
# DRC catches it, but the geometry is what decides it.
EASTBOUND_Y = {2: 4.6, 4: 5.2, 6: 5.8}
DESCENT_X = {2: 48.0, 4: 47.2, 6: 46.4}

# The odd channels need no lane of their own: each drops from its header
# straight to the y of the pad it is going to, and runs east along it.

VPLUS_Y = 24.0        # the V+ bus, between J1's bottom pair and the power row

# Stitching vias, in the empty band between the CH1 lane and the V+ bus. GND
# is already stitched at every header -- nineteen through-hole pads on it --
# so these are belt and braces on a board where they cost nothing.
STITCH_Y = 22.0
STITCH_X = (7.0, 13.0, 19.0, 25.0, 31.0, 37.0)

# -- fixed placements --------------------------------------------------------
PAD_XY = (3.0, 17.0)          # E1, the shield/ground pad, on the west margin
HOLE_XY = {
    "H1": (_HOLE_INSET, _HOLE_INSET),
    "H2": (_HOLE_INSET, BOARD_H - _HOLE_INSET),
    "H3": (BOARD_W - _HOLE_INSET, _HOLE_INSET),
    "H4": (BOARD_W - _HOLE_INSET, BOARD_H - _HOLE_INSET),
}
assert (HOLE_XY["H3"][0] - HOLE_XY["H1"][0],
        HOLE_XY["H2"][1] - HOLE_XY["H1"][1]) \
    == circuit.MOUNTING_PATTERN["hole_centres"], (
        "the mounting holes no longer sit on the breakout's centres")

# Headers are placed rotated so their pins run along the board rather than
# across it. +90 puts pin 1 westmost; check_placement() asserts it did.
ROW_ROTATION = 90


def to_mm(value):
    return pcbnew.ToMM(value)


# ---------------------------------------------------------------------------
# rounded rectangle
# ---------------------------------------------------------------------------
#
# Three views of the same shape, because three things consume it and none of
# them take the same form: Edge_Cuts wants segments and true arcs, a zone
# wants a closed polygon, and check_fits() wants to know whether a point is
# inside. Deriving all three from one (rectangle, radius) is what stops the
# pours and the outline drifting apart at the corners -- which they would do
# silently, as a sliver of copper hanging over a rounded edge.

def rounded_rectangle_segments(rectangle, radius):
    """The four straight edges, each stopping short of its corners."""
    left, top, right, bottom = rectangle
    r = radius
    return [((left + r, top), (right - r, top)),
            ((right, top + r), (right, bottom - r)),
            ((right - r, bottom), (left + r, bottom)),
            ((left, bottom - r), (left, top + r))]


def rounded_rectangle_arcs(rectangle, radius):
    """The four corners as (start, mid, end), clockwise on screen."""
    left, top, right, bottom = rectangle
    r = radius
    # How far the arc's midpoint sits in from the corner of the bounding box.
    k = r * (1 - 2 ** -0.5)
    return [((left, top + r), (left + k, top + k), (left + r, top)),
            ((right - r, top), (right - k, top + k), (right, top + r)),
            ((right, bottom - r), (right - k, bottom - k), (right - r, bottom)),
            ((left + r, bottom), (left + k, bottom - k), (left, bottom - r))]


def rounded_rectangle_polygon(rectangle, radius, steps=8):
    """The same outline as a closed polygon, for a zone.

    y is down, so the angles run clockwise on screen: a corner centred at
    (cx, cy) sweeping 180 to 270 degrees is the *top-left* one.
    """
    import math

    left, top, right, bottom = rectangle
    r = radius
    corners = (((right - r, top + r), -90, 0),
               ((right - r, bottom - r), 0, 90),
               ((left + r, bottom - r), 90, 180),
               ((left + r, top + r), 180, 270))
    points = []
    for (cx, cy), start, end in corners:
        for step in range(steps + 1):
            angle = math.radians(start + (end - start) * step / steps)
            points.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))
    return points


def point(x, y):
    return pcbnew.VECTOR2I_MM(float(x), float(y))


def column_x(channel):
    """Centre of a channel's column. CH1 is west, CH6 is nearest J1."""
    return CH_X0 + (channel - 1) * CH_PITCH


class Board:
    def __init__(self):
        self.board = pcbnew.BOARD()
        self.board.SetCopperLayerCount(2)
        self.nets = {}
        self.footprints = {}
        self._make_nets()

    # -- nets and parts ---------------------------------------------------
    def _make_nets(self):
        for name in sorted(circuit.NETS):
            net = pcbnew.NETINFO_ITEM(self.board, name)
            self.board.Add(net)
            self.nets[name] = net

    def net(self, name):
        return self.nets[name]

    def place(self, ref, x, y, rotation=0):
        part = circuit.PARTS[ref]
        library, name = part.footprint.split(":", 1)
        footprint = pcbnew.FootprintLoad(str(FOOTPRINT_DIR / f"{library}.pretty"), name)
        if footprint is None:
            raise SystemExit(f"could not load footprint {part.footprint} for {ref}")
        self.board.Add(footprint)
        # FootprintLoad returns the footprint under its bare name; without the
        # library nickname KiCad cannot tie it back to a library, so
        # "Update Footprints from Library" has nothing to work from.
        footprint.SetFPIDAsString(part.footprint)
        # Link back to the schematic symbol of the same reference. The UUIDs
        # are derived from the project name, so both generators compute the
        # same value independently -- this is what makes cross-probing work
        # and stops "Update PCB from Schematic" treating every footprint as
        # a new part.
        footprint.SetPath(pcbnew.KIID_PATH(
            f"/{symbol_uuid(f'{circuit.PROJECT}:part:{ref}:1')}"))
        footprint.SetSheetname("/")
        footprint.SetSheetfile(f"{circuit.PROJECT}.kicad_sch")
        footprint.SetPosition(point(x, y))
        if rotation:
            footprint.SetOrientationDegrees(rotation)
        footprint.SetReference(ref)
        footprint.SetValue(part.value)
        footprint.Reference().SetVisible(True)
        footprint.Value().SetVisible(False)
        self.footprints[ref] = footprint

        owner = circuit.DESIGN.pin_owner()
        for pad in footprint.Pads():
            key = (ref, pad.GetNumber())
            if key in owner:
                pad.SetNet(self.net(owner[key]))
        return footprint

    def pad(self, ref, number):
        """Absolute position of a pad, in millimetres."""
        for candidate in self.footprints[ref].Pads():
            if candidate.GetNumber() == str(number):
                position = candidate.GetPosition()
                return (round(to_mm(position.x), 4), round(to_mm(position.y), 4))
        raise KeyError(f"{ref} has no pad {number}")

    # -- copper -----------------------------------------------------------
    def track(self, net, points, layer=F, width=TRACK):
        for start, end in zip(points, points[1:]):
            if start == end:
                continue
            segment = pcbnew.PCB_TRACK(self.board)
            segment.SetStart(point(*start))
            segment.SetEnd(point(*end))
            segment.SetWidth(pcbnew.FromMM(width))
            segment.SetLayer(layer)
            segment.SetNet(self.net(net))
            self.board.Add(segment)

    def via(self, net, x, y):
        item = pcbnew.PCB_VIA(self.board)
        item.SetPosition(point(x, y))
        item.SetWidth(pcbnew.FromMM(VIA_DIAMETER))
        item.SetDrill(pcbnew.FromMM(VIA_DRILL))
        item.SetViaType(pcbnew.VIATYPE_THROUGH)
        item.SetLayerPair(F, B)
        item.SetNet(self.net(net))
        self.board.Add(item)

    def zone(self, net, layer, points, priority=0):
        item = pcbnew.ZONE(self.board)
        item.SetLayer(layer)
        item.SetNet(self.net(net))
        item.SetAssignedPriority(priority)
        item.SetLocalClearance(pcbnew.FromMM(CLEARANCE))
        item.SetMinThickness(pcbnew.FromMM(0.2))
        outline = item.Outline()
        outline.NewOutline()
        for x, y in points:
            outline.Append(pcbnew.FromMM(float(x)), pcbnew.FromMM(float(y)))
        self.board.Add(item)
        return item

    def outline(self, rectangle, radius):
        """Edge cuts: four segments and four corner arcs.

        The corners are rounded because the breakout's are, and a square
        corner is *more* material than a round one -- a square 50 x 35 does
        not go where a rounded 50 x 35 goes. Matching the outline and then
        leaving the corners sharp would give a board that measures right and
        will not drop into the pocket.
        """
        for start, end in rounded_rectangle_segments(rectangle, radius):
            shape = pcbnew.PCB_SHAPE(self.board)
            shape.SetShape(pcbnew.SHAPE_T_SEGMENT)
            shape.SetStart(point(*start))
            shape.SetEnd(point(*end))
            shape.SetLayer(pcbnew.Edge_Cuts)
            shape.SetWidth(pcbnew.FromMM(0.1))
            self.board.Add(shape)
        for start, middle, end in rounded_rectangle_arcs(rectangle, radius):
            shape = pcbnew.PCB_SHAPE(self.board)
            shape.SetShape(pcbnew.SHAPE_T_ARC)
            shape.SetArcGeometry(point(*start), point(*middle), point(*end))
            shape.SetLayer(pcbnew.Edge_Cuts)
            shape.SetWidth(pcbnew.FromMM(0.1))
            self.board.Add(shape)

    def reference(self, ref, x=None, y=None, size=rules.MIN_SILK_TEXT,
                  visible=True):
        """Move, resize or hide a footprint's reference designator.

        Left alone these inherit their footprint's rotation and its default
        offset, which on a strip this crowded puts half of them on top of
        their own neighbours and two of them over the board edge, where a fab
        clips them.
        """
        item = self.footprints[ref].Reference()
        item.SetVisible(visible)
        if not visible:
            return
        if x is not None:
            item.SetPosition(point(x, y))
        item.SetTextAngleDegrees(0)
        item.SetTextSize(pcbnew.VECTOR2I(pcbnew.FromMM(size), pcbnew.FromMM(size)))
        item.SetTextThickness(pcbnew.FromMM(size * 0.15))

    def text(self, body, x, y, size=1.0, layer=pcbnew.F_SilkS):
        item = pcbnew.PCB_TEXT(self.board)
        item.SetText(body)
        item.SetPosition(point(x, y))
        item.SetLayer(layer)
        item.SetTextSize(pcbnew.VECTOR2I(pcbnew.FromMM(size), pcbnew.FromMM(size)))
        item.SetTextThickness(pcbnew.FromMM(size * 0.15))
        self.board.Add(item)


# ---------------------------------------------------------------------------
# placement
# ---------------------------------------------------------------------------

def place_all(board):
    """Thirteen connectors, a pad and four holes."""
    # J1's anchor is its pin 1, so placing it there puts the whole connector.
    board.place("J1", *J1_PIN1)

    for channel in range(1, circuit.CHANNELS + 1):
        x = column_x(channel)
        # Anchors are pin 1, and pin 1 goes west, so each header is offset by
        # half its own pin span to sit centred on the column.
        board.place(f"S{channel}", x - 1.0, Y_SIGNAL, ROW_ROTATION)
        board.place(f"P{channel}", x - 2.0, Y_POWER, ROW_ROTATION)

    board.place("E1", *PAD_XY)
    for ref, position in HOLE_XY.items():
        board.place(ref, *position)


def check_placement(board):
    """Assert the geometry the routing below is written against.

    Every waypoint in this file is a literal, and every literal assumes a pad
    is somewhere. Rotation conventions are the classic way for that assumption
    to be wrong -- a footprint turned the other way still places, still routes
    and still passes DRC, with pin 1 at the far end of the connector and V+ on
    the capsule's ground. So the assumptions are written down and checked
    instead of being left implicit in the coordinates.
    """
    problems = []

    def want(condition, message):
        if not condition:
            problems.append(message)

    # Pin 1 is the west-most pad on every capsule header. The whole board has
    # one rule for which way round a housing goes, and this is it.
    for channel in range(1, circuit.CHANNELS + 1):
        x = column_x(channel)
        for ref, pins in ((f"S{channel}", (1, 2)), (f"P{channel}", (1, 2, 3))):
            positions = [board.pad(ref, pin) for pin in pins]
            want(all(abs(p[1] - positions[0][1]) < 1e-6 for p in positions),
                 f"{ref} is not lying along the board: {positions}")
            want(positions == sorted(positions),
                 f"{ref} pin 1 is not west-most: {positions}")
            centre = (positions[0][0] + positions[-1][0]) / 2
            want(abs(centre - x) < 1e-6,
                 f"{ref} is centred on {centre}, not on column {x}")

    # J1: odd pins on the near (west) row, pairs stepping south.
    for pin in range(1, 11):
        expected = (J1_PIN1[0] + (0 if pin % 2 else 2.0),
                    J1_PIN1[1] + ((pin - 1) // 2) * 2.0)
        found = board.pad("J1", pin)
        want(found == expected, f"J1 pad {pin} is at {found}, expected {expected}")

    # Every lane has to clear the pads it runs past. Checked against the same
    # rule DRC will apply, so a lane nudged into a pad fails here first, with
    # a message that says which lane.
    #
    # The eastbound lanes run in the band between the north edge and the
    # signal pads. It is 2.2 mm of usable width for three lanes, because the
    # two north mounting holes eat the top of it -- check_holes_clear() is
    # what holds that end, since an unplated hole is invisible here.
    for channel, y in EASTBOUND_Y.items():
        want(y >= rules.MIN_COPPER_EDGE_CLEARANCE + TRACK / 2,
             f"CH{channel}'s eastbound lane at y={y} is off the board edge")
        want(Y_SIGNAL - y >= KEEPOUT,
             f"CH{channel}'s eastbound lane at y={y} is inside the signal pads")
    for channel, x in DESCENT_X.items():
        want(x - (J1_PIN1[0] + 2.0) >= KEEPOUT,
             f"CH{channel}'s descent at x={x} is inside J1's east row")
        want(BOARD_W - x >= rules.MIN_COPPER_EDGE_CLEARANCE + TRACK / 2,
             f"CH{channel}'s descent at x={x} is off the board edge")
    want(min(DESCENT_X.values()) - max(EASTBOUND_Y.values()) > 0,
         "the descents and the eastbound lanes are not separable")

    # The two nestings must run the same way round. A channel that takes an
    # outer lane and an inner descent encloses nothing and crosses both its
    # neighbours -- which is the mistake this layout made once already, when
    # the lanes were tried in the band south of the signal row.
    order = sorted(EASTBOUND_Y, key=lambda ch: EASTBOUND_Y[ch])
    want(order == sorted(DESCENT_X, key=lambda ch: -DESCENT_X[ch]),
         f"lane order {order} does not match descent order "
         f"{sorted(DESCENT_X, key=lambda ch: -DESCENT_X[ch])}: the outermost "
         f"lane must also take the outermost descent")

    if problems:
        raise SystemExit("placement is not what the routing assumes:\n  "
                         + "\n  ".join(problems))


# ---------------------------------------------------------------------------
# routing
# ---------------------------------------------------------------------------

def route_near_row(board):
    """CH1, CH3 and CH5: straight there, on F.Cu.

    These are the odd pins of J1, which are its west row -- the side facing
    the channels. Each drops from its header to the y of its pad and runs
    east along it. They nest because CH1 is furthest west and wants the
    deepest lane, so no drop ever crosses a lane already laid.
    """
    for channel in (1, 3, 5):
        pin = next(p for p, net in circuit.BREAKOUT_J3.items()
                   if net == f"CH{channel}")
        source = board.pad(f"S{channel}", 1)
        target = board.pad("J1", pin)
        board.track(f"CH{channel}",
                    [source, (source[0], target[1]), target], layer=F)


def route_far_row(board):
    """CH2, CH4 and CH6: the long way round, on B.Cu.

    J1's even pins are its east row, and there is no route to them between
    the pads of the west row -- see the module docstring and the assertion in
    rules.py. So each of these goes north over its own header, east above the
    whole signal row, down the outside of the connector, and back in from the
    east, where nothing is in the way.

    Both nestings run the same direction: the channel that starts furthest
    west takes the lane nearest the north edge and the descent nearest the
    east edge, so it encloses the other two rather than crossing them. See
    EASTBOUND_Y for why the band has to be the northern one.
    """
    for channel in (2, 4, 6):
        pin = next(p for p, net in circuit.BREAKOUT_J3.items()
                   if net == f"CH{channel}")
        source = board.pad(f"S{channel}", 1)
        target = board.pad("J1", pin)
        lane_y = EASTBOUND_Y[channel]
        lane_x = DESCENT_X[channel]
        board.track(f"CH{channel}", [
            source,                      # header pin, through-hole: no via needed
            (source[0], lane_y),         # north, over the header row
            (lane_x, lane_y),            # east, above everything
            (lane_x, target[1]),         # south, outside the connector
            target,                      # west, into the east row
        ], layer=B)


def route_supply(board):
    """V+ from J1 pin 9 along the south of the board to all six headers.

    One bus rather than six spurs, on F.Cu, in the gap between J1's bottom
    pair and the power row. POWER_TRACK is not carrying current so much as
    keeping the run stiff and easy to inspect: the capsule's bias networks
    are all tens of kilohms and its op-amp is a TLV170, so six of them
    together draw single-figure milliamps at most.
    """
    entry = board.pad("J1", 9)
    west = board.pad("P1", 1)
    board.track("V+", [entry, (entry[0], VPLUS_Y), (west[0], VPLUS_Y)],
                layer=F, width=POWER_TRACK)
    for channel in range(1, circuit.CHANNELS + 1):
        pad = board.pad(f"P{channel}", 1)
        board.track("V+", [(pad[0], VPLUS_Y), pad], layer=F, width=POWER_TRACK)


def stitch(board):
    """GND vias between the two pours."""
    for x in STITCH_X:
        board.via("GND", x, STITCH_Y)
    return len(STITCH_X)


def check_holes_clear(board):
    """No track or via may run into a mounting hole.

    This is new with the breakout's outline and it is not ceremony. On the
    61 x 24 strip the holes sat 3.5 mm in from the ends, a long way from
    anything; here they are 2.5 mm in from all four edges, which puts H3 and
    H4 in the same east margin the three descents run down -- CH4's descent
    passes 0.3 mm from H3's centre line, and misses it only because the two
    never share a y.

    Nothing else here would catch it. An unplated hole carries no pad and no
    net, so it is on no net's keepout and in no netlist; check_placement()
    runs before any copper exists; and check_fits() compares the hole's
    courtyard against the board outline, which says nothing about what is
    routed through it. A track laid straight across one would build, pass the
    netlist comparison and arrive as a board with a screw hole through a
    signal.
    """
    def distance_to_segment(px, py, ax, ay, bx, by):
        dx, dy = bx - ax, by - ay
        span = dx * dx + dy * dy
        if span == 0:
            return ((px - ax) ** 2 + (py - ay) ** 2) ** 0.5
        t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / span))
        return ((px - ax - t * dx) ** 2 + (py - ay - t * dy) ** 2) ** 0.5

    problems = []
    for ref, (hx, hy) in HOLE_XY.items():
        for item in board.board.GetTracks():
            half = to_mm(item.GetWidth()) / 2
            needed = HOLE_DRILL / 2 + rules.MIN_HOLE_CLEARANCE + half
            start, end = item.GetStart(), item.GetEnd()
            gap = distance_to_segment(hx, hy,
                                      to_mm(start.x), to_mm(start.y),
                                      to_mm(end.x), to_mm(end.y))
            if gap < needed:
                net = item.GetNetname() or "?"
                problems.append(
                    f"{net} passes {gap:.2f} mm from {ref} at ({hx}, {hy}); "
                    f"{needed:.2f} mm is the minimum")
    if problems:
        raise SystemExit("copper runs into a mounting hole:\n  "
                         + "\n  ".join(problems))


# ---------------------------------------------------------------------------
# copper, outline, silk
# ---------------------------------------------------------------------------

def add_copper(board, points):
    """GND poured on both layers.

    Free, on a two-layer board that is mostly air. What it buys is a return
    directly under every signal trace and a reference plane between the six
    of them -- worth little against a Nu's low-impedance output, but worth
    nothing against it either, and it costs the same to fabricate.
    """
    board.zone("GND", F, points)
    board.zone("GND", B, points)


def silkscreen(board):
    """Legends, sized so they fit on the board they are printed on.

    The stroke font advances about one text height per character, so a line of
    n characters at size s is roughly n*s wide. Every full-width line is
    checked against the board rather than trusted: a fab silently clips what
    runs off the edge, and the line most worth keeping is the longest one.
    """
    # Three widths, not one, because three different things are in the way at
    # three different heights.
    #
    #   full    a band with nothing in it across the whole board
    #   between the north and south margins, where a line long enough to
    #           reach x < 3.6 or x > 46.4 would print over a mounting hole
    #   body    the middle band, which J1 occupies from x = 41.5 east
    full_middle = BOARD_W / 2
    full_width = BOARD_W - 2.0
    between_middle = BOARD_W / 2
    between_width = (BOARD_W - 2 * (_HOLE_INSET + HOLE_DRILL / 2)) - 2.0
    body_middle = (J1_PIN1[0] - 2.0) / 2
    body_width = J1_PIN1[0] - 2.0 - 2.0

    def legend(body, y, size, middle, width):
        assert size >= rules.MIN_SILK_TEXT, (
            f"{size} mm text is below the {rules.MIN_SILK_TEXT} mm floor DRC "
            f"is set to enforce: {body!r}")
        assert len(body) * size < width, (
            f"silkscreen line is {len(body) * size:.0f} mm and only "
            f"{width:.0f} mm is free: {body!r}")
        board.text(body, middle, y, size=size)

    # The north margin. Two lines rather than the strip's one: 50 mm is not
    # 61 mm and the old single title no longer fits between the two holes.
    legend("CYCFI NU HUB   rev A", 1.7, 0.9, between_middle, between_width)
    legend("6 x NU CAPSULE -> INTERNAL BREAKOUT", 3.5, 0.8,
           between_middle, between_width)

    # The channel columns. CH1 is the low E and they run in string order, so
    # the number is the only thing that needs printing. Above the row here,
    # not below it: below is where the fan-in band starts.
    for channel in range(1, circuit.CHANNELS + 1):
        board.text(f"CH{channel}", column_x(channel), 5.3, size=1.2)

    # Everything a person needs to make up a cable, in the middle band west of
    # the connector. Three lines where the strip had three, but split
    # differently: the row legend was one 55-character line and the middle
    # band is only 37 mm wide, so it reads as two.
    legend("PIN 1 IS THE WEST PAD ON EVERY HEADER", 13.0, 0.8,
           body_middle, body_width)
    legend("N ROW = SIGNAL  1=OUT 2=GND", 15.2, 0.8, body_middle, body_width)
    legend("S ROW = POWER  1=V+ 2,3=GND", 17.4, 0.8, body_middle, body_width)

    # The one line that must not be missed goes full width, in the clear band
    # between J1's bottom pair and the power row's designators.
    legend(circuit.SILK_NOTE, 23.4, 0.8, full_middle, full_width)
    legend(circuit.SUPPLY_NOTE.upper(), 30.4, 0.8, full_middle, full_width)

    # J1's own corners. Pins 1 and 2 are the ones that must stay empty, and
    # pins 9 and 10 are the ones that hurt if a wire lands on the wrong one.
    # All three sit outside the connector's own silk outline, not beside it.
    board.text("NC", J1_PIN1[0] - 2.5, J1_PIN1[1], size=0.8)
    board.text("V+", J1_PIN1[0] - 2.5, J1_PIN1[1] + 8.0, size=0.8)
    board.text("G", J1_PIN1[0] + 5.2, J1_PIN1[1] + 8.0, size=0.8)

    # E1's legend goes above the pad: below it is where the cable legend
    # starts, and the two collided.
    # Not "BRIDGE": the pad's designed job is the trunk cable's screen drain,
    # and a bridge earth is a builder's choice with a weak case on an
    # all-active instrument. Silk that names the optional use first invites it.
    board.text("SHIELD", PAD_XY[0], PAD_XY[1] - 3.8, size=0.8)
    board.text("GND", PAD_XY[0], PAD_XY[1] - 2.6, size=0.8)


def designators(board):
    """Where each reference designator goes.

    The two rows need different answers, and the reason is the footprints'
    own silk. A 1x02's outline is 4.2 mm wide on a 7 mm pitch, which leaves
    2.8 mm between one box and the next -- room for a designator. A 1x03's is
    6.2 mm wide, which leaves 0.8 mm, and a two-character label is 1.4 mm. So
    the power row's designators go above it instead, in the band between the
    V+ bus and the top of the footprint outlines.

    The mounting holes get no designator at all: four identical corner holes,
    and their default positions land two of them over the board edge, where a
    fab clips them anyway.
    """
    for channel in range(1, circuit.CHANNELS + 1):
        x = column_x(channel)
        board.reference(f"S{channel}", x - 3.4, Y_SIGNAL)
        # 2.1 mm above the row, not 1.5: the 1x03's own silk outline runs at
        # y = Y_POWER - 1.11, and a designator any lower overlaps it.
        board.reference(f"P{channel}", x, Y_POWER - 2.1)
    board.reference("J1", J1_PIN1[0] + 1.0, J1_PIN1[1] - 2.0, size=0.9)
    board.reference("E1", PAD_XY[0], PAD_XY[1] - 5.0)
    for ref in circuit.MOUNTING_HOLES:
        board.reference(ref, visible=False)


def mechanical(board, rectangle):
    """Describe the finished board for whatever has to be built around it.

    The enclosure lives in its own repository, because it needs CadQuery and
    this one deliberately needs nothing. That split is only safe if the
    dimensions cross the boundary as data rather than as numbers copied out of
    a PDF, so this writes the one file the enclosure consumes and verify.py
    checks it back against the board.

    Everything here is read off the placed footprints rather than off the
    constants at the top of this file. The constants are what the board was
    asked to be; this is what it came out as.
    """
    left, top, right, bottom = rectangle

    def body(ref):
        """Courtyard bounding box -- the space the part actually claims."""
        box = board.footprints[ref].GetCourtyard(pcbnew.F_CrtYd).BBox()
        if box.GetWidth() == 0:
            return None
        return {"x_min": round(to_mm(box.GetLeft()), 3),
                "y_min": round(to_mm(box.GetTop()), 3),
                "x_max": round(to_mm(box.GetRight()), 3),
                "y_max": round(to_mm(box.GetBottom()), 3)}

    def placement(ref, group, note):
        footprint = board.footprints[ref]
        position = footprint.GetPosition()
        return {
            "ref": ref,
            "value": circuit.PARTS[ref].value,
            "group": group,
            "x": round(to_mm(position.x), 3),
            "y": round(to_mm(position.y), 3),
            "rotation": round(footprint.GetOrientationDegrees(), 1),
            "footprint": circuit.PARTS[ref].footprint,
            "body": body(ref),
            "note": note,
        }

    parts = [placement("J1", "trunk",
                       "2x5 to Internal Breakout J3; cable leaves the east "
                       "side, over the 3.5 mm margin beyond the connector")]
    for channel in range(1, circuit.CHANNELS + 1):
        parts.append(placement(
            f"S{channel}", "capsule_signal",
            f"CH{channel} signal, {circuit.STRINGS[channel]}; "
            f"cable leaves the north edge"))
        parts.append(placement(
            f"P{channel}", "capsule_power",
            f"CH{channel} power, {circuit.STRINGS[channel]}; "
            f"cable leaves the south edge"))
    parts.append(placement("E1", "ground_pad",
                           "solder pad for the trunk cable screen"))

    holes = []
    for ref in circuit.MOUNTING_HOLES:
        position = board.footprints[ref].GetPosition()
        holes.append({
            "ref": ref,
            "x": round(to_mm(position.x), 3),
            "y": round(to_mm(position.y), 3),
            "drill": HOLE_DRILL,
            "plated": False,
            "screw": circuit.MOUNTING_PATTERN["hole_screw"],
            "body": body(ref),
        })

    return {
        "schema": "cycfi-nu-hub/mechanical",
        "schema_version": 1,
        "project": circuit.PROJECT,
        "generated_by": "gen_pcb.py -- do not edit; regenerate with ./build.sh",
        "units": "mm",
        # The sign of y is the classic way an enclosure comes out mirrored,
        # so it is stated rather than left to be inferred from the numbers.
        "axes": {
            "origin": "top-left corner of the board outline",
            "x": "increases east; CH1 is at the west end, CH6 at the east",
            "y": "increases SOUTH -- downward on the layout, KiCad's convention",
            "z": "increases up, out of the component side",
            "warning": "CAD tools normally put +Y up. Convert before modelling.",
            "to_y_up": "y_up = board.height - y",
        },
        "board": {
            "width": round(right - left, 3),
            "height": round(bottom - top, 3),
            "thickness": 1.6,
            "shape": "rounded rectangle",
            "corner_radius": BOARD_R,
            "copper_layers": 2,
        },
        # Where the outline and the hole pattern came from, carried across to
        # the enclosure with the caveat attached. A pocket cut from this fits
        # a v2.5 breakout as well as a hub; whether it fits a v2.6 is unknown,
        # because Cycfi have published no dimensions for one.
        "outline_source": {
            "matches": "Cycfi Internal Breakout v2.5",
            "from": circuit.MOUNTING_PATTERN["source"],
            "caveat": "v2.6 is a physical redesign with no published "
                      "dimensions; this is the v2.5 geometry. Measure a v2.6 "
                      "before cutting anything that must fit one.",
        },
        "mounting_holes": holes,
        "parts": parts,
        "component_height": {
            "known": False,
            "reason": "Header bodies are in the footprints, but the mated "
                      "crimp housing is not, and the 2x5 housing is not yet "
                      "chosen. Measure the tallest mated stack before "
                      "closing a lid over it.",
            "measure": ["2x5 housing mated on J1",
                        "3-way housing mated on P1-P6",
                        "2-way housing mated on S1-S6",
                        "solder joints proud of the underside"],
        },
    }


def check_fits(board, rectangle, radius):
    """Nothing may stick out of the outline, corners included.

    board_extent() in the sibling project derives the outline from the parts;
    here the size is declared, because the whole point of this revision is
    that it is somebody else's size. That trade needs this check, or a part
    nudged east just quietly hangs over the edge.

    The corners count. A courtyard can sit inside the bounding rectangle on
    all four sides and still overhang a rounded corner, and on a board whose
    corners were rounded specifically so it would drop into a pocket, that is
    exactly the failure worth catching.
    """
    left, top, right, bottom = rectangle
    # A rounded rectangle is exactly the set of points within `radius` of the
    # rectangle inset by `radius`, so clamping a point into that inner
    # rectangle gives the nearest point on the shape and one comparison
    # settles both the edges and the corners.
    inner = (left + radius, top + radius, right - radius, bottom - radius)

    def overhang(px, py):
        cx = min(max(px, inner[0]), inner[2])
        cy = min(max(py, inner[1]), inner[3])
        return ((px - cx) ** 2 + (py - cy) ** 2) ** 0.5 - radius

    problems = []
    for ref, footprint in board.footprints.items():
        # The courtyard polygon, not its bounding box. The M2 mounting holes'
        # courtyards are circles that clear the board edge by 0.03 mm, and the
        # corners of a circle's bounding box are not on the circle -- testing
        # those reports all four holes as hanging 0.7 mm off a board they fit.
        courtyard = footprint.GetCourtyard(pcbnew.F_CrtYd)
        worst = None
        for index in range(courtyard.OutlineCount()):
            chain = courtyard.Outline(index)
            for vertex in range(chain.PointCount()):
                corner = chain.CPoint(vertex)
                beyond = overhang(to_mm(corner.x), to_mm(corner.y))
                if worst is None or beyond > worst[0]:
                    worst = (beyond, to_mm(corner.x), to_mm(corner.y))
        if worst is not None and worst[0] > 1e-6:
            problems.append(
                f"{ref} courtyard hangs {worst[0]:.3f} mm over the outline at "
                f"({worst[1]:.3f}, {worst[2]:.3f})")
    if problems:
        raise SystemExit("parts do not fit the board:\n  " + "\n  ".join(problems))


def main():
    board = Board()
    place_all(board)
    check_placement(board)

    route_near_row(board)
    route_far_row(board)
    route_supply(board)
    vias = stitch(board)
    check_holes_clear(board)

    rectangle = (0.0, 0.0, BOARD_W, BOARD_H)
    check_fits(board, rectangle, BOARD_R)
    board.outline(rectangle, BOARD_R)
    # The pours follow the rounded corners in as well. Inset as a plain
    # rectangle their corners would poke 0.02 mm outside a 1.75 mm arc -- not
    # much, but it is copper over the edge of the board, and it is the sort of
    # thing that survives review precisely because it is too small to see.
    inner = (rules.ZONE_INSET, rules.ZONE_INSET,
             BOARD_W - rules.ZONE_INSET, BOARD_H - rules.ZONE_INSET)
    add_copper(board, rounded_rectangle_polygon(inner, BOARD_R - rules.ZONE_INSET))
    silkscreen(board)
    designators(board)

    here = pathlib.Path(__file__).parent
    destination = here / circuit.PROJECT / f"{circuit.PROJECT}.kicad_pcb"
    pcbnew.ZONE_FILLER(board.board).Fill(board.board.Zones())
    pcbnew.SaveBoard(str(destination), board.board)

    interface = here / "fab" / f"{circuit.PROJECT}-mechanical.json"
    interface.parent.mkdir(parents=True, exist_ok=True)
    interface.write_text(json.dumps(mechanical(board, rectangle), indent=2) + "\n")

    print(f"wrote {destination}")
    print(f"  and {interface.name} for the enclosure")
    print(f"  {len(board.footprints)} footprints, {vias} stitching vias, "
          f"{len(list(board.board.GetTracks()))} track/via items")
    print(f"  board {BOARD_W:.1f} x {BOARD_H:.1f} mm "
          f"= {BOARD_W * BOARD_H:.0f} mm2")


if __name__ == "__main__":
    main()
