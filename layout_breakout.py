"""Layout for the `breakout` board: six capsules onto a Cycfi Internal Breakout.

This is the geometry only. The machinery it runs on -- the Board wrapper, the
outline helpers, the fit and hole-clearance checks and the mechanical export --
lives in gen_pcb.py, which is shared with the other variant.

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
cable bundles leave on opposite edges with the trunk leaving east.

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

Track waypoints are given relative to real pad positions read back from the
placed footprints, so nothing here depends on guessing KiCad's rotation
conventions -- and the assertions in check_placement() are what turn a wrong
guess into a failed build rather than a shorted board.
"""

import pcbnew

import design as circuit
import rules

TRACK = rules.TRACK
POWER_TRACK = rules.POWER_TRACK
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
HOLE_SCREW = circuit.MOUNTING_PATTERN["hole_screw"]

# Which connector the trunk cable lands on, for the mechanical export.
TRUNK_REFS = "J1"

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


def column_x(channel):
    """Centre of a channel's column. CH1 is west, CH6 is nearest J1."""
    return CH_X0 + (channel - 1) * CH_PITCH


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

def route(board):
    """Everything, in the order the docstrings above assume."""
    route_near_row(board)
    route_far_row(board)
    route_supply(board)
    return stitch(board)


def mechanical_parts(board, placement):
    """The parts list for fab/*-mechanical.json, in this board's own terms."""
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
    return parts


OUTLINE_SOURCE = {
    "matches": "Cycfi Internal Breakout v2.5",
    "from": circuit.MOUNTING_PATTERN["source"],
    "caveat": "v2.6 is a physical redesign with no published dimensions; this "
              "is the v2.5 geometry. Measure a v2.6 before cutting anything "
              "that must fit one.",
}
