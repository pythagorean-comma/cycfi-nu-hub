"""Fabrication rules, in one place because two generators need them.

`gen_pcb.py` lays copper against these and `gen_project.py` writes them into
the .kicad_pro for DRC to enforce. Declaring them once is what stops a rule
being widened in the layout and not in the checker -- the one kind of drift
where the build still passes and the board is still wrong.

Nothing here is close to the edge of what a low-cost fab can do, and that is
deliberate. This board carries six audio channels and a few milliamps of
supply across 60 mm; there is no performance to win by tightening it, so every
number is set where it buys margin instead.

The annular ring is the only figure with real arithmetic behind it. A
fabricator's cumulative drill and layer-registration error runs to about
0.003" = 0.0762 mm, and a ring smaller than that misregistration is a broken
via:

    ring = (VIA_DIAMETER - VIA_DRILL) / 2 = 0.200 mm
    worst case after full misregistration = 0.200 - 0.076 = 0.124 mm

against an IPC-2221 Class 2 minimum external annular ring of 0.05 mm. The
assertion at the bottom of this file is what holds that, so shrinking a via
here fails the import rather than the board.
"""

# Cumulative drill and registration error to design against.
REGISTRATION = 0.0762     # 0.003 inch

TRACK = 0.30              # the six channel signals
POWER_TRACK = 0.60        # V+
VIA_DIAMETER = 0.80
VIA_DRILL = 0.40
CLEARANCE = 0.25

ANNULAR_RING = (VIA_DIAMETER - VIA_DRILL) / 2
assert ANNULAR_RING - REGISTRATION > 0.05, (
    f"annular ring {ANNULAR_RING}mm does not survive {REGISTRATION}mm of "
    f"misregistration with IPC Class 2 margin -- see the module docstring")

# The 2.00 mm headers are the reason the layout looks the way it does. Their
# pads are 1.35 mm on a 2.00 mm pitch, so the clear gap between two adjacent
# pads is 0.65 mm, and a TRACK-wide track needs
#
#     TRACK + 2 * CLEARANCE = 0.80 mm
#
# to pass between them. It does not fit, and no plausible thinning makes it
# fit. That single number is why the far row of the 2x5 is reached around the
# outside of the connector instead of between its pads -- see gen_pcb.py.
HEADER_PITCH = 2.00
HEADER_PAD = 1.35
assert TRACK + 2 * CLEARANCE > HEADER_PITCH - HEADER_PAD, (
    "a track now fits between two header pads; the detour in gen_pcb.py "
    "exists only because it does not, so re-read route_signals() before "
    "relaxing this")

# How far a track's centre must stay from the centre of a header pad.
PAD_KEEPOUT = HEADER_PAD / 2 + CLEARANCE + TRACK / 2

# DRC constraint floors. These sit just *below* the geometry above rather than
# at it: they are the check that catches a rule being widened in one generator
# and not the other, so they must not be so tight that legitimate geometry
# trips them, nor so loose that they would pass a board drawn to nothing.
MIN_TRACK_WIDTH = 0.25
MIN_CLEARANCE = 0.20
MIN_VIA_DIAMETER = 0.70
MIN_VIA_ANNULAR_WIDTH = 0.18
MIN_THROUGH_HOLE_DIAMETER = 0.35
MIN_HOLE_CLEARANCE = 0.25
MIN_HOLE_TO_HOLE = 0.25
MIN_COPPER_EDGE_CLEARANCE = 0.50

# Board edge to the zone boundary. Matches MIN_COPPER_EDGE_CLEARANCE so the
# pours cannot be the thing that violates it.
ZONE_INSET = MIN_COPPER_EDGE_CLEARANCE

# Smallest silkscreen text. Declared here rather than in gen_pcb.py because
# gen_project.py writes it into the .kicad_pro as min_text_height for DRC to
# enforce, and the two used to be separate numbers -- so every legend on the
# board was a DRC warning against a rule this project had set itself, and the
# build never said so because it only ever asked for errors.
#
# 0.8 mm is also about the floor a fab will guarantee to render legibly, so
# there is nothing to gain by going under it: text too small to read is not a
# smaller label, it is a missing one.
MIN_SILK_TEXT = 0.8

assert MIN_TRACK_WIDTH <= TRACK
assert MIN_CLEARANCE <= CLEARANCE
assert MIN_VIA_DIAMETER <= VIA_DIAMETER
assert MIN_THROUGH_HOLE_DIAMETER <= VIA_DRILL
assert MIN_VIA_ANNULAR_WIDTH <= ANNULAR_RING
