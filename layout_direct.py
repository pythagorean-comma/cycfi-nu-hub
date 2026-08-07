"""Layout for the `direct` board: six capsules onto the 19-pin output jack.

The breakout is gone, so nothing constrains the outline any more and the board
is as small as the connectors allow: 35 x 24.5 mm against the breakout-shaped
board's 50 x 35. What sets that floor is worth stating, because it is not the
copper.

Turn a 1x03 so its pins run *along* the row -- which is what the breakout board
does -- and each channel column costs 7.0 mm of courtyard. Turn it so the pins
run *across* and the courtyard costs 3.0 mm, at which point the limit is no
longer the footprint but the mated crimp housing, about 4.5 mm wide. So:

    ROW_ROTATION = 0    pins run south, columns on a 5.0 mm pitch,
                        six of them in 30 mm instead of 42

The two jack connectors get the same treatment. Lying broadside they are
11.0 x 5.0 mm each rather than 5.0 x 11.0, so the pair sits side by side inside
the width the columns already need and the middle band is 5 mm tall instead of
eleven. Everything else follows from those two rotations.

WARNING, and it is the reason check_placement() is written out rather than
copied from layout_breakout: pin 1 is the NORTH pad here, not the west one.
Every waypoint below assumes it. A header turned the other way still places,
still routes and still passes DRC, with V+ on the capsule's ground.

The fan-in
----------
Harder than the breakout board's, because all six channels land in one
4 x 2 mm cluster at the west end of J10 while their headers are spread across
the whole width. Three facts shape it:

  * A signal pad has its own connector's ground pad directly south of it, so
    nothing leaves a header going straight down. Every channel steps sideways
    into the 5 mm gap between two columns first.
  * J10's north row (CH1/CH3/CH5) is reachable from above. Its south row
    (CH2/CH4/CH6) is not reachable from the north at all, for the same reason
    the breakout board's far row is not: nothing routes between the pads of a
    2.00 mm header. Those three go around the west end and come back in from
    below.
  * That detour cannot be done on one layer, and this is the part that is not
    obvious. Each even channel drops from its header to a west-bound lane,
    runs west, turns south down the margin, and comes back east underneath.
    The lanes must be ordered so the channel travelling furthest west runs
    southernmost -- otherwise it crosses the others' drops. But that same
    ordering puts each lane straight across the *descents* of the channels
    north of it. The two requirements are contradictory on a single layer.

    So the three descents run on F.Cu and everything either side of them on
    B.Cu, with a via at each end. Six vias, and they are the cheapest thing
    on the board.

The west margin they descend through is 2.7 mm wide -- between H1's keepout and
J10's first pad column -- and carries all three. It is the tightest thing on
either board.
"""

import pcbnew

import design as circuit
import rules

TRACK = rules.TRACK
POWER_TRACK = rules.POWER_TRACK
CLEARANCE = rules.CLEARANCE
KEEPOUT = rules.PAD_KEEPOUT
VIA_KEEPOUT = rules.VIA_DIAMETER / 2 + CLEARANCE + TRACK / 2

F = pcbnew.F_Cu
B = pcbnew.B_Cu

# -- the outline, which is this board's own ---------------------------------
BOARD_W = 35.0
BOARD_H = 24.5
BOARD_R = 1.5

HOLE_DRILL = 2.2
HOLE_SCREW = "M2"
TRUNK_REFS = "J10 and J11"

# -- the three bands ---------------------------------------------------------
Y_SIGNAL = 2.5        # S1..S6 pin 1; pin 2 (GND) sits 2 mm south of it
Y_POWER = 18.0        # P1..P6 pin 1 (V+); pins 2 and 3 south of it
CH_X0 = 5.0           # centre of the CH1 column
CH_PITCH = 5.0        # the mated 3-way housing is about 4.5 mm across, so
                      # this leaves roughly 0.5 mm between two of them --
                      # tighter than the breakout board's 0.8 and close to
                      # the point where you need a tool to unplug one

# Pins run south rather than along the row. This is the whole reason the board
# is 35 mm and not 47: see the module docstring.
ROW_ROTATION = 0
JACK_ROTATION = 90

# The two jack connectors, by their pin 1. Rotated, the footprint steps +2 in
# x to the next pair and -2 in y to the even row, so these two corners fix all
# twenty pads. J10 sits west because it carries every channel; J11 is power and
# grounds, and goes east where the supply and the power row want it.
J10_PIN1 = (8.0, 12.5)
J11_PIN1 = (20.0, 12.5)

# -- lanes -------------------------------------------------------------------
# CH2/CH4/CH6, in order of travel. Read with the module docstring: the top
# lanes and the returns are B.Cu, the descents between them are F.Cu.
EVEN_STEP_X = {2: 7.5, 4: 17.5, 6: 27.5}    # where each leaves its header
EVEN_TOP_Y = {2: 6.6, 4: 7.5, 6: 8.4}       # west-bound lane above the jack
EVEN_WEST_X = {2: 6.3, 4: 5.4, 6: 4.5}      # descent down the west margin
EVEN_BACK_Y = {2: 13.9, 4: 14.7, 6: 15.5}   # east-bound lane below the jack

# CH1/CH3/CH5 on F.Cu, into J10's north row from above. CH1's header is
# already almost over its pad, so it needs no lane at all. The other two nest
# the same way round as the even channels and for the same reason.
ODD_STEP_X = {3: 12.5, 5: 22.5}
ODD_LANE_Y = {3: 8.0, 5: 8.8}

VPLUS_Y = 16.6        # the V+ bus, between the jack band and the power row

# Two stitching vias rather than the breakout board's six. There is nowhere
# else on a board this size reliably clear of copper, and with twenty-four
# through-hole ground pads tying the pours together they were never doing
# much anyway.
STITCH = ((2.0, 20.0), (33.0, 20.0))

# -- fixed placements --------------------------------------------------------
PAD_XY = (1.7, 3.2)           # E1, in the one corner nothing else wants
C1_XY = (20.0, 15.25)         # bulk, in the band below the jack
F1_XY = (26.0, 15.25)         # polyfuse, directly under J11's VIN pins
F1_ROTATION = 180             # pin 1 east, so V+ leaves on the side it runs

# Two holes, not four. A 30 mm connector block in a 35 mm board leaves 3.5 mm
# of margin and an M2 courtyard is 4.9 mm across, so the corners are gone. The
# middle band is the only place they fit: J10 and J11 together span 6.5 to
# 29.5, and nothing else reaches x < 6.5 or x > 29.5 at that height.
HOLE_XY = {"H1": (2.75, 11.5), "H2": (32.25, 11.5)}

OUTLINE_SOURCE = {
    "matches": "nothing -- this board's outline is its own",
    "from": "packing, not transcription: six 5.0 mm columns plus margin sets "
            "the width, and the signal, jack and power bands set the height",
    "caveat": "the 5.0 mm column pitch assumes a mated A4B-3S-2C housing about "
              "4.5 mm across, which is inferred rather than measured. Measure "
              "one before committing: the width is linear in it.",
}


def at_least(value, minimum):
    """`value >= minimum`, tolerant of millimetre literals in binary.

    15.2 - 14.4 is 0.7999999999999998, so a clearance rule written as
    ">= 0.8" rejects a spacing that is exactly legal. KiCad works in integer
    nanometres and does not have the problem; these assertions do. The
    tolerance is a millionth of a nanometre -- far below anything a fab, a
    gerber or KiCad can represent -- so it can only ever forgive arithmetic,
    never a real violation.
    """
    return value >= minimum - 1e-9


def column_x(channel):
    """Centre of a channel's column. CH1 is west, CH6 is east."""
    return CH_X0 + (channel - 1) * CH_PITCH


def jack_pad(anchor, pin):
    """Where a pin of a rotated 2x5 lands.

    Unrotated the footprint puts odd pins at x0 and even at x0+2, with pairs
    stepping +2 in y. Turned 90 degrees, local +y becomes global +x and local
    +x becomes global -y, so pairs step east and the even row sits north.
    """
    return (anchor[0] + ((pin - 1) // 2) * 2.0,
            anchor[1] - (0.0 if pin % 2 else 2.0))


def jack_target(channel):
    """The J10 pin a channel has to reach, as a position."""
    pin = next(p for p, net in circuit.JACK_J10.items()
               if net == f"CH{channel}")
    return jack_pad(J10_PIN1, pin)


# ---------------------------------------------------------------------------
# placement
# ---------------------------------------------------------------------------

def place_all(board):
    """Fourteen connectors, two parts, a pad and two holes."""
    board.place("J10", *J10_PIN1, JACK_ROTATION)
    board.place("J11", *J11_PIN1, JACK_ROTATION)

    for channel in range(1, circuit.CHANNELS + 1):
        x = column_x(channel)
        board.place(f"S{channel}", x, Y_SIGNAL, ROW_ROTATION)
        board.place(f"P{channel}", x, Y_POWER, ROW_ROTATION)

    board.place("F1", *F1_XY, F1_ROTATION)
    board.place("C1", *C1_XY)
    board.place("E1", *PAD_XY)
    for ref, position in HOLE_XY.items():
        board.place(ref, *position)


def check_placement(board):
    """Assert the geometry the routing below is written against.

    Written out rather than adapted from the breakout board's, because the
    rotation convention is the opposite one and an assertion carried over
    unchanged would pass a board with every header turned the wrong way. Pin 1
    is the NORTH pad on both rows here.
    """
    problems = []

    def want(condition, message):
        if not condition:
            problems.append(message)

    for channel in range(1, circuit.CHANNELS + 1):
        x = column_x(channel)
        for ref, pins, top in ((f"S{channel}", (1, 2), Y_SIGNAL),
                               (f"P{channel}", (1, 2, 3), Y_POWER)):
            positions = [board.pad(ref, pin) for pin in pins]
            want(all(abs(p[0] - x) < 1e-6 for p in positions),
                 f"{ref} is not standing across the board: {positions}")
            want(positions == sorted(positions, key=lambda p: p[1]),
                 f"{ref} pin 1 is not north-most: {positions}")
            want(abs(positions[0][1] - top) < 1e-6,
                 f"{ref} pin 1 is at y={positions[0][1]}, not {top}")

    for ref, anchor in (("J10", J10_PIN1), ("J11", J11_PIN1)):
        for pin in range(1, 11):
            expected = jack_pad(anchor, pin)
            found = board.pad(ref, pin)
            want(found == expected,
                 f"{ref} pad {pin} is at {found}, expected {expected}")

    # F1 must sit the way round the supply runs: pin 1 (VIN) east, towards
    # J11, and pin 2 (V+) west, towards the bus and the power headers.
    vin_pad, vplus_pad = board.pad("F1", 1), board.pad("F1", 2)
    want(vin_pad[0] > vplus_pad[0],
         f"F1 is reversed: pin 1 at {vin_pad}, pin 2 at {vplus_pad}. VIN "
         f"arrives from the east and V+ leaves west; turned round, the bus "
         f"would have to cross the part to get out")

    # -- the west margin, which is the tightest thing on the board -----------
    hole_keepout = HOLE_DRILL / 2 + rules.MIN_HOLE_CLEARANCE + TRACK / 2
    for channel, x in EVEN_WEST_X.items():
        want(at_least(abs(x - HOLE_XY["H1"][0]), hole_keepout),
             f"CH{channel}'s west descent at x={x} is inside H1's keepout")
        want(at_least(J10_PIN1[0] - x, KEEPOUT),
             f"CH{channel}'s west descent at x={x} is inside J10's first pads")
    spread = sorted(EVEN_WEST_X.values())
    for near, far in zip(spread, spread[1:]):
        want(at_least(far - near, TRACK + CLEARANCE),
             f"west descents at {near} and {far} are closer than "
             f"{TRACK + CLEARANCE} mm apart")

    # -- the two nestings ---------------------------------------------------
    # A B.Cu lane crosses every drop that ends south of it, so the channel
    # whose header sits furthest east -- the one that travels furthest west --
    # needs the southernmost lane.
    by_source = sorted(EVEN_TOP_Y, key=lambda ch: EVEN_STEP_X[ch])
    want(by_source == sorted(EVEN_TOP_Y, key=lambda ch: EVEN_TOP_Y[ch]),
         f"the even channels' lanes do not nest: heading west in source order "
         f"{by_source} they must also run north to south")

    # Coming back, each return crosses the rise of any channel whose pad is
    # further west, so the channel with the eastmost pad needs the
    # southernmost return.
    by_target = sorted(EVEN_BACK_Y, key=lambda ch: jack_target(ch)[0])
    want(by_target == sorted(EVEN_BACK_Y, key=lambda ch: EVEN_BACK_Y[ch]),
         f"the even channels' returns do not nest: in pad order {by_target} "
         f"they must also run north to south")

    # Each lane passes the vias where the other descents change layer, and a
    # via is wider than the track it joins. Cheap to check, invisible to read.
    #
    # A lane spans from its own descent outwards, so the only vias it can pass
    # are those further from the west edge than its own -- hence the same skip
    # on the way out and the way back.
    for channel, y in EVEN_TOP_Y.items():
        for other, x in EVEN_WEST_X.items():
            if other == channel or x < EVEN_WEST_X[channel]:
                continue
            want(at_least(abs(y - EVEN_TOP_Y[other]), VIA_KEEPOUT),
                 f"CH{channel}'s lane at y={y} passes CH{other}'s via at "
                 f"({x}, {EVEN_TOP_Y[other]}) closer than {VIA_KEEPOUT} mm")
    for channel, y in EVEN_BACK_Y.items():
        for other, x in EVEN_WEST_X.items():
            if other == channel or x < EVEN_WEST_X[channel]:
                continue
            want(at_least(abs(y - EVEN_BACK_Y[other]), VIA_KEEPOUT),
                 f"CH{channel}'s return at y={y} passes CH{other}'s via at "
                 f"({x}, {EVEN_BACK_Y[other]}) closer than {VIA_KEEPOUT} mm")

    for channel, y in EVEN_TOP_Y.items():
        want(at_least(y - (Y_SIGNAL + 2.0), KEEPOUT),
             f"CH{channel}'s lane at y={y} is inside the signal grounds")
        want(at_least(J10_PIN1[1] - 2.0 - y, KEEPOUT),
             f"CH{channel}'s lane at y={y} is inside the jack's north row")
    for channel, y in EVEN_BACK_Y.items():
        want(at_least(y - J10_PIN1[1], KEEPOUT),
             f"CH{channel}'s return at y={y} is inside the jack's south row")
        want(at_least(Y_POWER - y, KEEPOUT),
             f"CH{channel}'s return at y={y} is inside the power row")

    for channel, y in ODD_LANE_Y.items():
        want(at_least(y - (Y_SIGNAL + 2.0), KEEPOUT),
             f"CH{channel}'s lane at y={y} is inside the signal grounds")
        want(at_least(J10_PIN1[1] - 2.0 - y, KEEPOUT),
             f"CH{channel}'s lane at y={y} is inside the jack's north row")

    # The westmost descent turns back east a whisker above where the V+ bus
    # turns south into P1, and what meets there is a via rather than a track --
    # 0.4 mm of radius instead of 0.15. Sized as a track it clears by 0.08 mm
    # and DRC rejects it, which is how this assertion came to exist.
    bus_corner = (board.pad("P1", 1)[0], VPLUS_Y)
    via_to_bus = rules.VIA_DIAMETER / 2 + CLEARANCE + POWER_TRACK / 2
    for channel, x in EVEN_WEST_X.items():
        gap = ((x - bus_corner[0]) ** 2
               + (EVEN_BACK_Y[channel] - bus_corner[1]) ** 2) ** 0.5
        want(at_least(gap, via_to_bus),
             f"CH{channel}'s lower via at ({x}, {EVEN_BACK_Y[channel]}) is "
             f"{gap:.2f} mm from where the V+ bus turns into P1; a via needs "
             f"{via_to_bus:.2f} mm, not the {KEEPOUT:.2f} a track would")

    want(at_least(VPLUS_Y - J10_PIN1[1], KEEPOUT),
         f"the V+ bus at y={VPLUS_Y} is inside the jack's south row")
    want(at_least(Y_POWER - VPLUS_Y,
                  rules.HEADER_PAD / 2 + CLEARANCE + POWER_TRACK / 2),
         f"the V+ bus at y={VPLUS_Y} is inside the power row")

    if problems:
        raise SystemExit("placement is not what the routing assumes:\n  "
                         + "\n  ".join(problems))


# ---------------------------------------------------------------------------
# routing
# ---------------------------------------------------------------------------

def route_north_row(board):
    """CH1, CH3 and CH5: into J10's north row from above, on F.Cu.

    Each steps sideways out of its header to clear its own ground pin, then
    drops. CH1's header is already over its pad, so it needs no lane; the
    other two run west along one and drop in.

    They nest for the same reason the even channels do, in the same direction:
    CH5 starts furthest east, travels furthest west and so takes the
    southernmost lane, passing under CH3's drop rather than through it.
    """
    for channel in (1, 3, 5):
        source = board.pad(f"S{channel}", 1)
        target = jack_target(channel)
        if channel == 1:
            board.track(f"CH{channel}", [
                source,
                (target[0], source[1]),      # east, clear of its own ground
                target,                      # south, into the pad
            ], layer=F)
            continue
        step, lane = ODD_STEP_X[channel], ODD_LANE_Y[channel]
        board.track(f"CH{channel}", [
            source,
            (step, source[1]),               # west, into the gap between
            (step, lane),                    # south, past the signal row
            (target[0], lane),               # west, above the connector
            target,                          # south, into the pad
        ], layer=F)


def route_south_row(board):
    """CH2, CH4 and CH6: the long way round the west end, and across layers.

    J10's south row cannot be reached from the north at all -- nothing routes
    between the pads of a 2.00 mm header, which rules.py asserts. So each of
    these steps out of its header, runs west above the connectors on B.Cu,
    changes to F.Cu to descend the west margin, changes back and runs east
    underneath to come up into its pad from below.

    The layer change is not decoration. See the module docstring: the lane
    order that keeps the three from crossing each other's drops is the same
    order that puts every lane across the others' descents, and no single
    layer satisfies both.
    """
    vias = 0
    for channel in (2, 4, 6):
        source = board.pad(f"S{channel}", 1)
        target = jack_target(channel)
        step = EVEN_STEP_X[channel]
        top, back = EVEN_TOP_Y[channel], EVEN_BACK_Y[channel]
        west = EVEN_WEST_X[channel]
        net = f"CH{channel}"

        board.track(net, [
            source,
            (step, source[1]),               # west, out of the header row
            (step, top),                     # south, clear of the ground pin
            (west, top),                     # west, over the connectors
        ], layer=B)
        board.via(net, west, top)
        board.track(net, [(west, top), (west, back)], layer=F)
        board.via(net, west, back)
        board.track(net, [
            (west, back),
            (target[0], back),               # east, underneath the connector
            target,                          # north, into the pad
        ], layer=B)
        vias += 2
    return vias


def route_supply(board):
    """VIN in from the jack, through F1, out along the V+ bus.

    The two VIN pins are joined at the connector rather than each spurred to
    the fuse: they are the same net arriving twice, and one track between them
    is shorter than two to anywhere else.

    Everything downstream of F1 is one bus. POWER_TRACK is not about current
    -- six capsules draw single-figure milliamps between them -- but about
    keeping the run stiff and easy to follow with a probe.
    """
    high, low = board.pad("J11", 8), board.pad("J11", 7)
    fuse_in, fuse_out = board.pad("F1", 1), board.pad("F1", 2)

    # Down the connector, then across and into the fuse. The dog-leg keeps the
    # run clear of J11's ground pair two positions east.
    board.track("VIN", [high, low, (low[0], fuse_in[1] - 1.25),
                        (fuse_in[0], fuse_in[1] - 1.25), fuse_in],
                layer=F, width=POWER_TRACK)

    west = board.pad("P1", 1)
    east = board.pad(f"P{circuit.CHANNELS}", 1)
    board.track("V+", [fuse_out, (fuse_out[0], VPLUS_Y)],
                layer=F, width=POWER_TRACK)
    board.track("V+", [(west[0], VPLUS_Y), (east[0], VPLUS_Y)],
                layer=F, width=POWER_TRACK)
    for channel in range(1, circuit.CHANNELS + 1):
        pad = board.pad(f"P{channel}", 1)
        board.track("V+", [(pad[0], VPLUS_Y), pad], layer=F, width=POWER_TRACK)

    # C1 hangs off the bus; its ground end is left to the pour, like every
    # other ground on the board.
    bulk = board.pad("C1", 1)
    board.track("V+", [bulk, (bulk[0], VPLUS_Y)], layer=F, width=POWER_TRACK)


def stitch(board):
    """GND vias between the two pours."""
    for x, y in STITCH:
        board.via("GND", x, y)
    return len(STITCH)


def route(board):
    """Everything, in the order the docstrings above assume."""
    route_north_row(board)
    vias = route_south_row(board)
    route_supply(board)
    return vias + stitch(board)


# ---------------------------------------------------------------------------
# silk
# ---------------------------------------------------------------------------

def silkscreen(board):
    """Three lines and the designators, which is all there is room for.

    The breakout board prints the whole cable table. At 35 x 24.5 mm that does
    not fit, so what stays is the one thing a person can get catastrophically
    wrong by reading the board instead of the documentation -- and here that
    is no longer the pin map but the orientation, because a reversed J10 is
    not harmless. See circuit.JACK_REVERSAL_NOTE.
    """
    middle = BOARD_W / 2
    width = BOARD_W - 2.0

    def legend(body, y, size=0.8):
        assert size >= rules.MIN_SILK_TEXT, (
            f"{size} mm text is below the {rules.MIN_SILK_TEXT} mm floor DRC "
            f"is set to enforce: {body!r}")
        assert len(body) * size < width, (
            f"silkscreen line is {len(body) * size:.0f} mm and only "
            f"{width:.0f} mm is free: {body!r}")
        board.text(body, middle, y, size=size)

    legend("CYCFI NU HUB DIRECT   rev A", 6.3)
    legend("PIN 1 IS THE NORTH PAD ON EVERY HEADER", 7.45)
    legend(circuit.BOARD_NOTE, 8.6)


def designators(board):
    """Where each reference designator goes.

    Nothing has room beside it, so the two header rows take opposite
    solutions: the signal row's labels go above it, in the 1.5 mm strip
    between the board edge and the footprint outlines, and the power row's go
    in the 2.0 mm gap between one column and the next.
    """
    for channel in range(1, circuit.CHANNELS + 1):
        x = column_x(channel)
        board.reference(f"S{channel}", x, 0.9)
        board.reference(f"P{channel}", x - 2.5, Y_POWER + 2.0)
    board.reference("J10", 7.0, 14.8)
    board.reference("J11", 30.5, 14.8)
    board.reference("C1", 17.0, C1_XY[1])
    board.reference("F1", 23.0, F1_XY[1])
    board.reference("E1", PAD_XY[0], PAD_XY[1] + 2.6)
    for ref in circuit.MOUNTING_HOLES:
        board.reference(ref, visible=False)


def mechanical_parts(board, placement):
    """The parts list for fab/*-mechanical.json, in this board's own terms."""
    parts = [
        placement("J10", "trunk",
                  "2x5 to the 19-pin jack loom -- channels 1-6 and a ground"),
        placement("J11", "trunk",
                  "2x5 to the 19-pin jack loom -- VIN and two grounds"),
    ]
    for channel in range(1, circuit.CHANNELS + 1):
        parts.append(placement(
            f"S{channel}", "capsule_signal",
            f"CH{channel} signal, {circuit.STRINGS[channel]}; "
            f"cable leaves the north edge"))
        parts.append(placement(
            f"P{channel}", "capsule_power",
            f"CH{channel} power, {circuit.STRINGS[channel]}; "
            f"cable leaves the south edge"))
    parts.append(placement("F1", "supply",
                           "polyfuse, in series with the capsule supply"))
    parts.append(placement("C1", "supply",
                           "bulk across V+ where power enters the board"))
    parts.append(placement("E1", "ground_pad",
                           "solder pad for the jack loom's screen"))
    return parts
