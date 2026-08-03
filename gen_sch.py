"""Draw the schematic for the design in design.py.

One capsule row is laid out once in local coordinates and instantiated six
times, which is why the six channels are guaranteed identical.

Nothing here is drawn with long wires. Every connector pin gets a stub and a
global label, because on a board that is only a pin map, a drawing made of
crossing wires would obscure the one thing worth reading: which pin is on
which net. The table down the right-hand side of the sheet is the deliverable.
"""

import pathlib

import design as circuit
from kisch import Schematic

# eeschema's connection grid is 1.27 mm and kisch.auto_junctions() rejects
# anything off it, so every constant here is a multiple of it.
GRID = 1.27

ROW_PITCH = 30.48                # 24 grid steps between capsule rows
ROW_ORIGIN_Y = 38.1
POWER_X = 60.96                  # P1..P6 body
POWER_LABEL_X = 45.72            # where the V+ label sits
POWER_GND_X = 50.8               # the column both ground pins join on
SIGNAL_X = 111.76                # S1..S6 body
SIGNAL_LABEL_X = 96.52
SIGNAL_GND_X = 99.06

# J1 sits high on the right, so the note block can have the whole column
# beneath it. The longest note is the provenance line, about 210 mm at 1.4 mm
# text, which is what fixes NOTE_X: any further right and it runs off an A3.
J1_ORIGIN = (285.75, 60.96)
J1_LEFT_LABEL_X = 270.51
J1_RIGHT_LABEL_X = 303.53
J1_GND_X = 298.45

NOTE_X = 152.4
NOTE_Y = 106.68

# The odds and ends go below the capsule rows, on the left, clear of both the
# notes and the title block.
PAD_ORIGIN = (45.72, 215.9)
FLAG_ORIGIN = (45.72, 241.3)
HOLE_ORIGIN = (152.4, 241.3)


def row_y(index):
    return ROW_ORIGIN_Y + (index - 1) * ROW_PITCH


def place(sch, ref, x, y, angle=0):
    """Place a part from the design by reference.

    The description travels with the symbol, because it is the field that
    reaches the BOM -- and on this board the descriptions are the useful part
    of the BOM. "1x03 header" tells a builder nothing; "capsule 1 (low E)
    power, to capsule H2: 1=V+, 2=GND, 3=GND" is the wiring instruction.
    """
    part = circuit.PARTS[ref]
    return sch.place(ref, part.lib_id, part.value, x, y,
                     footprint=part.footprint, angle=angle,
                     extra={"Description": part.description}
                     if part.description else None)


def capsule_row(sch, index):
    """One capsule: its 3-pin power header and its 2-pin signal header.

    Drawn as the capsule presents them -- two separate connectors, because
    that is what is at the two ends of the capsule PCB. Drawing them as one
    5-pin block would be tidier and would misdescribe the hardware.
    """
    y = row_y(index)

    # -- power, mirroring the capsule's H2 -------------------------------
    power = place(sch, f"P{index}", POWER_X, y)
    sch.wire(power.pin(1), (POWER_LABEL_X, y - 2.54))
    sch.label("V+", POWER_LABEL_X, y - 2.54, angle=180)
    # Both ground pins, joined on one column and taken to a single symbol.
    sch.wire(power.pin(2), (POWER_GND_X, y))
    sch.wire(power.pin(3), (POWER_GND_X, y + 2.54))
    sch.wire((POWER_GND_X, y), (POWER_GND_X, y + 6.35))
    sch.power("power:GND", POWER_GND_X, y + 6.35)

    # -- signal, mirroring the capsule's H1 ------------------------------
    signal = place(sch, f"S{index}", SIGNAL_X, y)
    sch.wire(signal.pin(1), (SIGNAL_LABEL_X, y))
    sch.label(f"CH{index}", SIGNAL_LABEL_X, y, angle=180)
    sch.wire(signal.pin(2), (SIGNAL_GND_X, y + 2.54))
    sch.wire((SIGNAL_GND_X, y + 2.54), (SIGNAL_GND_X, y + 6.35))
    sch.power("power:GND", SIGNAL_GND_X, y + 6.35)

    # Clear of P{index}'s own reference designator, which kisch puts 6.35 mm
    # above the symbol.
    sch.text(f"CH{index}  {circuit.STRINGS[index]}", POWER_LABEL_X, y - 10.16,
             size=1.6)


def breakout(sch):
    """J1, drawn pin by pin against the breakout's own numbering.

    The symbol puts odd pins down the left and even pins down the right,
    which happens to be exactly how the connector is built -- pins 1 and 2 are
    a pair across the two rows -- so the drawing reads as the physical part.
    """
    ox, oy = J1_ORIGIN
    j1 = place(sch, "J1", ox, oy)

    for pin in circuit.BREAKOUT_UNUSED:
        # Not fitted at either end of the cable. The no-connect flag is what
        # tells ERC that, and it is also what stops verify.py reporting them.
        sch.no_connect(*j1.pin(pin))

    for pin, net in sorted(circuit.BREAKOUT_J3.items()):
        if pin in circuit.BREAKOUT_UNUSED:
            continue
        position = j1.pin(pin)
        left = pin % 2 == 1
        if net == "GND":
            sch.wire(position, (J1_GND_X, position[1]),
                     (J1_GND_X, position[1] + 6.35))
            sch.power("power:GND", J1_GND_X, position[1] + 6.35)
            continue
        label_x = J1_LEFT_LABEL_X if left else J1_RIGHT_LABEL_X
        sch.wire(position, (label_x, position[1]))
        sch.label(net, label_x, position[1], angle=180 if left else 0)

    sch.text("J1 -> Internal Breakout J3", ox - 15.24, oy - 15.24, size=2.0)
    sch.text("(silk: NU MULTI INPUT 1, underside of the breakout)",
             ox - 15.24, oy - 11.43, size=1.4)


def grounding(sch):
    """E1, the ground tail pad."""
    ox, oy = PAD_ORIGIN
    pad = place(sch, "E1", ox, oy)
    sch.wire(pad.pin(1), (ox, oy + 5.08))
    sch.power("power:GND", ox, oy + 5.08)
    sch.text("Trunk cable screen; cavity foil. See docs/DESIGN.md.",
             ox + 7.62, oy, size=1.4)


def mounting(sch):
    """The four mounting holes, so the board and the drawing agree on them."""
    ox, oy = HOLE_ORIGIN
    for offset, ref in enumerate(circuit.MOUNTING_HOLES):
        place(sch, ref, ox + offset * 12.7, oy)
    sch.text("M2.5 clearance, unplated -- not on GND", ox - 1.27, oy + 8.89,
             size=1.4)


def flags(sch):
    """PWR_FLAGs so ERC knows V+ and GND arrive from the connector."""
    ox, oy = FLAG_ORIGIN
    for offset, (ref, net) in enumerate((("#FLG01", "V+"), ("#FLG02", "GND"))):
        x = ox + offset * 25.4
        flag = sch.place(ref, "power:PWR_FLAG", "PWR_FLAG", x, oy)
        sch.wire(flag.pin(1), (x, oy + 5.08))
        if net == "GND":
            sch.power("power:GND", x, oy + 5.08)
        else:
            sch.label(net, x, oy + 5.08, angle=270)
    sch.text("No supply on this board: both rails arrive on J1.",
             ox - 5.08, oy - 6.35, size=1.4)


def notes(sch):
    """The prose that has to travel with the drawing.

    Sourced from design.py rather than written out again, so the sheet cannot
    drift from the circuit it is describing -- and verify.py checks that
    SILK_NOTE in particular reached both this and the silkscreen.
    """
    x, y = NOTE_X, NOTE_Y

    def line(body, size=1.6, step=5.08):
        nonlocal y
        sch.text(body, x, y, size=size)
        y += step

    line(circuit.SILK_NOTE, size=2.2)
    line(f"Verified against {circuit.CYCFI_SOURCE}.", size=1.4, step=6.35)

    line("Breakout J3, pin for pin:", size=1.8)
    for pin, net in sorted(circuit.BREAKOUT_J3.items()):
        unused = pin in circuit.BREAKOUT_UNUSED
        note = "  not fitted (shared with J4 pin 7/8)" if unused else ""
        line(f"    {pin:>2} = {net}{note}", size=1.4, step=3.81)

    y += 3.81
    line("Reversed, a 2x5 maps pin n to pin 11-n, so the two empty",
         size=1.4, step=3.81)
    line("positions land on V+ and GND: a backwards cable delivers no",
         size=1.4, step=3.81)
    line("supply rather than the wrong one. Nothing is damaged.",
         size=1.4, step=6.35)

    line("No components fitted. Each capsule carries its own", size=1.4, step=3.81)
    line(f"{circuit.CAPSULE_DECOUPLING},", size=1.4, step=3.81)
    line("and pin 1 of its power header is Schottky protected on the",
         size=1.4, step=3.81)
    line("capsule. There is nothing left for this board to do.",
         size=1.4, step=6.35)

    line(circuit.SUPPLY_NOTE, size=1.4, step=3.81)


def build(path):
    sch = Schematic(circuit.PROJECT,
                    title="Cycfi Nu hub -- 6 capsules to Internal Breakout",
                    rev="A", company="pythagorean-comma",
                    date="2026-08-03", paper="A3")
    for lib_id, (nick, libname, symname, rename) in circuit.LIBS.items():
        sch.use(nick, libname, symname, rename=rename)

    for index in range(1, circuit.CHANNELS + 1):
        capsule_row(sch, index)
    breakout(sch)
    grounding(sch)
    mounting(sch)
    flags(sch)
    notes(sch)

    sch.auto_junctions()
    sch.save(path)
    return sch


if __name__ == "__main__":
    out = pathlib.Path(__file__).parent / circuit.PROJECT / f"{circuit.PROJECT}.kicad_sch"
    out.parent.mkdir(parents=True, exist_ok=True)
    schematic = build(out)
    print(f"wrote {out} ({len(schematic.parts)} symbol instances, "
          f"{len(schematic.wires)} wires, {len(schematic.junctions)} junctions)")
