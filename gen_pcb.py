"""Build the PCB for the design in design.py.

Two layers. GND is poured on both and everything else is a handful of tracks,
because there are only seven nets and no components to route between.

The board is a strip. Six signal headers along the north edge, six power
headers along the south edge, the 2x5 to the breakout at the east end, and the
channels in string order from CH1 at the west. Reading it left to right reads
the strings low to high, and the two cable bundles leave on opposite edges.

The one part of this that is not obvious is how the six channels reach the
2x5, and it is forced by the connector's own geometry rather than chosen. Its
pads are 1.35 mm on a 2.00 mm pitch, so the clear gap between two of them is
0.65 mm and a track needs 0.80 mm -- see the assertion in rules.py. Nothing
can be routed between the pads of a 2.00 mm header, which means the far row
cannot be reached from the near side at all. So:

    odd  pins 3/5/7 (CH5/CH3/CH1) are the near row, and are reached
         directly from the west on F.Cu;
    even pins 4/6/8 (CH6/CH4/CH2) are the far row, and go north of the
         signal headers on B.Cu, east past the connector, and come back
         into it from the outside.

Which of the two rows is near is itself a placement decision, and it is the
one that makes the fan-in planar. The connector puts CH1/CH2 at its southern
pair and CH5/CH6 at its northern one, so a channel's target y falls as its
number falls -- and with CH1 at the *west* end of the board, the westmost
channel wants the southernmost lane. That nests. Mirror the board and every
lane crosses every other one.

Track waypoints are given relative to real pad positions read back from the
placed footprints, so nothing here depends on guessing KiCad's rotation
conventions -- and the assertions in check_placement() are what turn a wrong
guess into a failed build rather than a shorted board.
"""

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

# -- the strip ---------------------------------------------------------------
BOARD_W = 61.0
BOARD_H = 24.0

Y_SIGNAL = 4.0        # S1..S6 pad row, north edge
Y_POWER = 20.0        # P1..P6 pad row, south edge
CH_X0 = 10.0          # centre of the CH1 column
CH_PITCH = 7.0        # 6.2 mm is the widest 3-way 2.00 mm housing, so this
                      # leaves 0.8 mm between two of them side by side

# J1's pin 1. The footprint steps +2 in x to the even row and +2 in y to the
# next pair, so this one corner fixes all ten pads.
#
# Not hard against the east edge, and the gap east of it is not slack: the
# three descents to the far row live in it, and beyond them the two eastern
# mounting holes, whose courtyards are 6 mm across because they have to clear
# a screw head. That is what sets BOARD_W.
J1_PIN1 = (51.0, 8.0)

# -- lanes -------------------------------------------------------------------
# The even channels' route north of the signal headers, outermost first: CH2
# starts furthest west so it takes the lane nearest the board edge, and comes
# back down the east side furthest out. Nesting in both axes at once is what
# keeps the three of them from crossing.
NORTH_LANES = {2: 1.4, 4: 2.0, 6: 2.6}
EAST_LANES = {2: 55.4, 4: 54.8, 6: 54.2}

# The odd channels need no lane of their own: each drops from its header
# straight to the y of the pad it is going to, and runs east along it.

VPLUS_Y = 18.0        # the V+ bus, between J1's bottom pair and the power row

# Stitching vias, in the empty band between the CH1 lane and the V+ bus. GND
# is already stitched at every header -- nineteen through-hole pads on it --
# so these are belt and braces on a board where they cost nothing.
STITCH_Y = 16.5
STITCH_X = (12.0, 19.0, 26.0, 33.0, 40.0, 47.0)

# -- fixed placements --------------------------------------------------------
PAD_XY = (3.5, 12.0)          # E1, the bridge/shield pad, on the west margin
HOLE_XY = {"H1": (3.5, 3.5), "H2": (3.5, 20.5),
           "H3": (57.5, 3.5), "H4": (57.5, 20.5)}

# Headers are placed rotated so their pins run along the board rather than
# across it. +90 puts pin 1 westmost; check_placement() asserts it did.
ROW_ROTATION = 90


def to_mm(value):
    return pcbnew.ToMM(value)


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

    def zone(self, net, layer, rectangle, priority=0):
        left, top, right, bottom = rectangle
        item = pcbnew.ZONE(self.board)
        item.SetLayer(layer)
        item.SetNet(self.net(net))
        item.SetAssignedPriority(priority)
        item.SetLocalClearance(pcbnew.FromMM(CLEARANCE))
        item.SetMinThickness(pcbnew.FromMM(0.2))
        outline = item.Outline()
        outline.NewOutline()
        for x, y in ((left, top), (right, top), (right, bottom), (left, bottom)):
            outline.Append(pcbnew.FromMM(float(x)), pcbnew.FromMM(float(y)))
        self.board.Add(item)
        return item

    def outline(self, rectangle):
        left, top, right, bottom = rectangle
        corners = [(left, top), (right, top), (right, bottom), (left, bottom),
                   (left, top)]
        for start, end in zip(corners, corners[1:]):
            shape = pcbnew.PCB_SHAPE(self.board)
            shape.SetShape(pcbnew.SHAPE_T_SEGMENT)
            shape.SetStart(point(*start))
            shape.SetEnd(point(*end))
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
    for channel, y in NORTH_LANES.items():
        want(y >= rules.MIN_COPPER_EDGE_CLEARANCE + TRACK / 2,
             f"CH{channel}'s north lane at y={y} is off the board edge")
        want(Y_SIGNAL - y >= KEEPOUT,
             f"CH{channel}'s north lane at y={y} is inside the signal pads")
    for channel, x in EAST_LANES.items():
        want(x - (J1_PIN1[0] + 2.0) >= KEEPOUT,
             f"CH{channel}'s east lane at x={x} is inside J1's far row")
        want(BOARD_W - x >= rules.MIN_COPPER_EDGE_CLEARANCE + TRACK / 2,
             f"CH{channel}'s east lane at x={x} is off the board edge")
    want(min(EAST_LANES.values()) - max(NORTH_LANES.values()) > 0,
         "the east lanes and north lanes are not separable")

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
    east edge, so it encloses the other two rather than crossing them.
    """
    for channel in (2, 4, 6):
        pin = next(p for p, net in circuit.BREAKOUT_J3.items()
                   if net == f"CH{channel}")
        source = board.pad(f"S{channel}", 1)
        target = board.pad("J1", pin)
        lane_y = NORTH_LANES[channel]
        lane_x = EAST_LANES[channel]
        board.track(f"CH{channel}", [
            source,                      # header pin, through-hole: no via needed
            (source[0], lane_y),         # north, over the header row
            (lane_x, lane_y),            # east, above everything
            (lane_x, target[1]),         # south, outside the connector
            target,                      # west, into the far row
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


# ---------------------------------------------------------------------------
# copper, outline, silk
# ---------------------------------------------------------------------------

def add_copper(board, rectangle):
    """GND poured on both layers.

    Free, on a two-layer board that is mostly air. What it buys is a return
    directly under every signal trace and a reference plane between the six
    of them -- worth little against a Nu's low-impedance output, but worth
    nothing against it either, and it costs the same to fabricate.
    """
    board.zone("GND", F, rectangle)
    board.zone("GND", B, rectangle)


def silkscreen(board):
    """Legends, sized so they fit on the board they are printed on.

    The stroke font advances about one text height per character, so a line of
    n characters at size s is roughly n*s wide. Every full-width line is
    checked against the board rather than trusted: a fab silently clips what
    runs off the edge, and the line most worth keeping is the longest one.
    """
    # Two widths, not one. A line spanning the whole board runs under J1's
    # silk outline and comes out unreadable, so the three legend lines are
    # centred on the strip *west* of the connector and checked against that
    # width instead of the board's.
    full_middle = BOARD_W / 2
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

    legend("CYCFI NU HUB   6 x NU CAPSULE -> INTERNAL BREAKOUT   rev A",
           1.4, 0.85, full_middle, BOARD_W - 2.0)
    legend(circuit.SUPPLY_NOTE.upper(), 22.8, 0.8, full_middle, BOARD_W - 2.0)

    # The channel columns. CH1 is the low E and they run in string order, so
    # the number is the only thing that needs printing.
    for channel in range(1, circuit.CHANNELS + 1):
        board.text(f"CH{channel}", column_x(channel), 6.7, size=1.2)

    # Everything a person needs to make up a cable, in the empty band between
    # the two header rows. The band has to hold these three lines *and* the
    # power row's designators, which is what sets the spacing: below 16.6 is
    # the designators' and the 1x03 outlines' territory.
    legend("PIN 1 IS THE WEST PAD ON EVERY HEADER", 12.2, 0.8,
           body_middle, body_width)
    legend("N ROW = SIGNAL 1=OUT 2=GND   S ROW = POWER 1=V+ 2,3=GND", 14.0,
           0.8, body_middle, body_width)
    legend(circuit.SILK_NOTE, 15.8, 0.8, body_middle, body_width)

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


def check_fits(board, rectangle):
    """Nothing may stick out of the outline.

    board_extent() in the sibling project derives the outline from the parts;
    here the strip is a declared size, because half the point of the layout is
    that it is a known, small rectangle. That trade needs this check, or a
    part nudged east just quietly hangs over the edge.
    """
    left, top, right, bottom = rectangle
    problems = []
    for ref, footprint in board.footprints.items():
        box = footprint.GetCourtyard(pcbnew.F_CrtYd).BBox()
        if box.GetWidth() == 0:
            continue        # mounting holes carry no courtyard
        edges = (to_mm(box.GetLeft()), to_mm(box.GetTop()),
                 to_mm(box.GetRight()), to_mm(box.GetBottom()))
        if (edges[0] < left or edges[1] < top
                or edges[2] > right or edges[3] > bottom):
            problems.append(f"{ref} courtyard {edges} is outside {rectangle}")
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

    rectangle = (0.0, 0.0, BOARD_W, BOARD_H)
    check_fits(board, rectangle)
    board.outline(rectangle)
    inner = (rules.ZONE_INSET, rules.ZONE_INSET,
             BOARD_W - rules.ZONE_INSET, BOARD_H - rules.ZONE_INSET)
    add_copper(board, inner)
    silkscreen(board)
    designators(board)

    here = pathlib.Path(__file__).parent
    destination = here / circuit.PROJECT / f"{circuit.PROJECT}.kicad_pcb"
    pcbnew.ZONE_FILLER(board.board).Fill(board.board.Zones())
    pcbnew.SaveBoard(str(destination), board.board)

    print(f"wrote {destination}")
    print(f"  {len(board.footprints)} footprints, {vias} stitching vias, "
          f"{len(list(board.board.GetTracks()))} track/via items")
    print(f"  board {BOARD_W:.1f} x {BOARD_H:.1f} mm "
          f"= {BOARD_W * BOARD_H:.0f} mm2")


if __name__ == "__main__":
    main()
