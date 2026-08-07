"""Six Cycfi Nu capsules onto one Cycfi Internal Breakout, as a netlist.

This is the authoritative circuit. The schematic is drawn from it and the
board is built from it, and the generated schematic is read back through
KiCad and compared against it, so a drawing mistake cannot quietly reach the
PCB.

There is no circuit here in the usual sense. The board carries no components
at all: it is thirteen connectors, a solder pad and some copper. Everything
below is therefore about getting one pin map right, and about the three facts
that map depends on -- all of which were read out of Cycfi's own Eagle sources
rather than taken on trust. See CAPSULE and BREAKOUT_J3.

    six capsules                       this board                breakout
    ------------                       ----------                --------
    H2 3-pin power  --- cable --->  P1..P6  (V+, GND, GND)  \
    H1 2-pin signal --- cable --->  S1..S6  (CHn, GND)       >-- J1 --> J3
                                                            /   2x5

What the board must not get wrong is in check_against_cycfi(): the pin map to
the breakout, and the pin map to each capsule. Both are asserted at import,
against the numbers transcribed from Cycfi's schematics at the top of this
file, so the whole design fails to load rather than builds wrong.
"""

import os

CHANNELS = 6

# ---------------------------------------------------------------------------
# Which board this is
# ---------------------------------------------------------------------------
#
# Two boards, and the capsule end of both is identical. What differs is what
# the six channels arrive at:
#
#   breakout  the six capsules join a Cycfi Internal Breakout on channels 1-6,
#             through one 2x5 wired one-to-one with its J3. Thirteen
#             connectors and no components.
#
#   direct    the breakout is deleted and the hub drives the instrument's
#             19-pin output jack itself, through the same two 2x5 headers the
#             breakout presents to it. Fourteen connectors, a polyfuse and a
#             bulk capacitor.
#
# The second exists because for an installation that uses none of the
# breakout's aux, CV, GK or power-select features, the breakout is a wire and
# a fuse -- see JACK_J10 for the evidence, which is Cycfi's own netlist.
VARIANTS = ("breakout", "direct")
VARIANT = os.environ.get("CYCFI_HUB_VARIANT", "breakout")
assert VARIANT in VARIANTS, (
    f"CYCFI_HUB_VARIANT={VARIANT!r} is not one of {VARIANTS}")

# Shared by the schematic, the board and the project scaffolding. The
# schematic's symbol UUIDs are derived from this name, and the board's
# footprints are linked back to those UUIDs, so the two generators must agree
# on it exactly -- hence one constant rather than three string literals.
PROJECT = "cycfi-nu-hub" if VARIANT == "breakout" else f"cycfi-nu-hub-{VARIANT}"

# ---------------------------------------------------------------------------
# What Cycfi's own files say
# ---------------------------------------------------------------------------
#
# Everything in this section was read out of
# https://github.com/cycfi/nu -- nu_capsule/nu_preamp.sch and
# internal_breakout/internal_breakout.sch, both Eagle 6.3 XML. The breakout
# silkscreen in that repository says "INTERNAL BREAKOUT V2.5"; nothing the hub
# touches changed for 2.6, but that is the revision the numbers below were
# taken from, so it is recorded rather than implied.
#
# These are transcriptions, not decisions. If Cycfi revise the breakout, this
# is the block that changes and check_against_cycfi() is what re-derives the
# consequences.

CYCFI_SOURCE = ("cycfi/nu @ github.com/cycfi/nu -- nu_capsule/nu_preamp.sch "
                "and internal_breakout/internal_breakout.sch, "
                "silk 'INTERNAL BREAKOUT V2.5'")

# The capsule has two connectors, at opposite ends of its PCB. Cycfi part
# names are H2 and H1; both are 2.00 mm male through-hole headers.
#
#   H2, 3-pin power. Pin 1 goes to the anode of D1, a Schottky whose cathode
#   is the capsule's VCC1 rail -- so pin 1 is V+ and it is already protected
#   against reverse polarity on the capsule itself. Pins 2 AND 3 are both GND.
#
#   H1, 2-pin signal. Pin 1 is the far side of C3, a 10 uF coupling capacitor
#   from the TLV170's output, with R2 (10k) to ground as the bleed. Pin 2
#   is GND.
#
# The capsule also decouples its own supply: C1 (100 nF) and C2 (4.7 uF) sit
# across VCC1 to GND, at the capsule. That is the reason this board has no
# capacitors on it -- see NO_COMPONENTS.
CAPSULE = {
    "power":  {1: "V+", 2: "GND", 3: "GND"},      # Cycfi H2, 3P-2MM-TH
    "signal": {1: "OUT", 2: "GND"},               # Cycfi H1, 2P-2MM-TH
}
CAPSULE_DECOUPLING = "100 nF (C1) + 4.7 uF (C2) across VCC1, on the capsule"

# Internal Breakout J3, silkscreened "NU MULTI INPUT 1". A 2x5 on a 2.00 mm
# grid from Cycfi's own headers(2mm) Eagle library, numbered in pairs across
# the two rows -- 1 and 2 are a pair, then 3 and 4, and so on -- which is the
# same convention KiCad's PinHeader_2x05 uses, and the reason a straight
# one-to-one cable works.
#
# Two things about this table are load-bearing.
#
# Pins 1 and 2 are CH7 and CH8, and those two nets are *shared* with J4 pins 7
# and 8 -- the second Nu Multi input. Leaving them out of the cable is not
# merely tidy: driving them from here would contend with anything plugged into
# J4.
#
# And leaving them out is what makes a reversed cable harmless. A 2x5 rotated
# in its own plane maps pin n to pin 11-n, so the two empty positions land on
# pins 10 and 9 -- GND and V+. Plugged in backwards the hub simply receives no
# supply: the capsules stay dark and nothing is powered hard enough to damage
# anything. That is worth knowing before anyone is tempted to add a shroud.
#
# J3 is mounted on the *underside* of the breakout (its Eagle placement is
# mirrored). That changes nothing electrically, but it is why the two ends of
# the cable do not look alike in the instrument.
BREAKOUT_J3 = {
    1: "CH7",   2: "CH8",     # not connected here -- see above
    3: "CH5",   4: "CH6",
    5: "CH3",   6: "CH4",
    7: "CH1",   8: "CH2",
    9: "V+",   10: "GND",
}
BREAKOUT_UNUSED = (1, 2)

# ---------------------------------------------------------------------------
# The 19-pin output jack, for the `direct` variant
# ---------------------------------------------------------------------------
#
# On the breakout, the jack lands on two 2x5 headers, J10 and J11. Twenty
# positions carrying CH1-CH15, three grounds and two VIN -- a nineteen-pin jack
# with one position spare. The `direct` hub presents the same two headers, so
# the instrument's existing jack loom plugs into it unmodified and the breakout
# comes out of the chain entirely.
#
# The load-bearing fact is what sits between the two on the breakout: nothing.
# Every channel net in Cycfi's internal_breakout.sch has exactly two pins on
# it, the Nu Multi input and the jack --
#
#     CH1  ( 2)  J10.2, J3.7          CH4  ( 2)  J10.3, J3.6
#     CH2  ( 2)  J10.1, J3.8          CH5  ( 2)  J10.6, J3.3
#     CH3  ( 2)  J10.4, J3.5          CH6  ( 2)  J10.5, J3.4
#
# -- no buffer, no filter, no protection. Copper joining the same two points
# replaces the breakout for audio exactly, which is the whole basis of this
# variant. See docs/cycfi-sources.md.
#
# Numbered in pairs across the rows, the same convention as J3 and the same as
# KiCad's PinHeader_2x05, which is what lets the loom be one-to-one.
#
# THIS IS THE v2.5 MAPPING. It was read out of the Eagle sources; the v2.6.1
# datasheet's jack diagram carries the same label set, so the jack's *content*
# did not change, but the ordering has only been confirmed against v2.5.
JACK_J10 = {
    1: "CH2",   2: "CH1",
    3: "CH4",   4: "CH3",
    5: "CH6",   6: "CH5",
    7: "CH8",   8: "CH7",     # channels this hub does not carry
    9: "GND",  10: "CH9",     # ditto pin 10
}
JACK_J11 = {
    1: "CH11",  2: "CH10",    # none of the first six positions are carried
    3: "CH13",  4: "CH12",
    5: "CH15",  6: "CH14",
    7: "VIN",   8: "VIN",
    9: "GND",  10: "GND",
}

# Six capsules, so nine of the fifteen channel positions go unfitted. They are
# named rather than blanked because the names are what check_against_cycfi()
# uses to prove the six that *are* fitted landed on the right pins.
JACK_UNUSED = {
    "J10": (7, 8, 10),
    "J11": (1, 2, 3, 4, 5, 6),
}

# What a reversed loom does, and it is worse than on the breakout board.
#
# A 2x5 rotated in its own plane maps pin n to 11-n. On J1 that lands the two
# unfitted positions on V+ and GND, so the hub simply receives no supply -- the
# reversal is harmless by construction. Here it is not: on a reversed J10, pin
# 2 (CH1) meets pin 9 (GND) and the capsule outputs are shorted to ground.
# Recoverable, because the TLV170 output is current-limited and sits behind a
# 10 uF coupling cap, but no longer safe by geometry. A reversed J11 puts VIN
# on unfitted channel positions and delivers no power, which is benign.
#
# The mitigation is keying, and the housings belong to Cycfi's loom rather than
# to this board, so this is recorded and checked rather than designed away.
JACK_REVERSAL_NOTE = (
    "a reversed J10 shorts the capsule outputs to ground -- unlike J1 on the "
    "breakout variant, this reversal is not harmless. Check before powering.")

# V+ is not a fixed rail. On the breakout, J14 is a three-pin jumper
# silkscreened "PWR SELECT" that ties V+ to either the unregulated input or
# the LP2985 output. This board passes whichever it is straight through, which
# is why nothing here depends on the voltage -- but the cable and the six
# capsules do, so it is stated on the silkscreen rather than assumed.
SUPPLY_NOTE = "V+ passed through from breakout J3 pin 9 (PWR SELECT)"

# The one sentence that has to survive onto both the schematic PDF and the
# silkscreen, because it is the only thing a person building the cable can get
# catastrophically wrong by reading the board instead of the documentation.
# verify.check_annotations() asserts it reaches both.
SILK_NOTE = "J1 IS 1:1 WITH BREAKOUT J3 - PINS 1-2 NOT FITTED"

# The same job on the `direct` board, but a different sentence, because the
# thing most worth warning about changed. There, the pin map is not what will
# hurt you -- a reversed J10 is. See JACK_REVERSAL_NOTE.
JACK_SILK_NOTE = "REVERSED J10 SHORTS CH1-6 TO GND"

# Whichever of the two this board carries. verify.check_annotations() asserts
# it reached the schematic and the silkscreen, so the generators must both
# read it from here rather than writing the sentence out.
BOARD_NOTE = SILK_NOTE if VARIANT == "breakout" else JACK_SILK_NOTE

# ---------------------------------------------------------------------------
# The board
# ---------------------------------------------------------------------------

# Channel 1 is the low E. The six capsule header pairs are laid out in string
# order across the board, CH1 at the west end and CH6 nearest the breakout
# connector, so reading the board left to right reads the strings low to high.
STRINGS = {1: "low E (6th)", 2: "A (5th)", 3: "D (4th)",
           4: "G (3rd)", 5: "B (2nd)", 6: "high E (1st)"}

LIBS = {
    "Connector_Generic:Conn_01x02": ("Connector_Generic", "Connector_Generic", "Conn_01x02", None),
    "Connector_Generic:Conn_01x03": ("Connector_Generic", "Connector_Generic", "Conn_01x03", None),
    "Connector_Generic:Conn_02x05_Odd_Even": ("Connector_Generic", "Connector_Generic", "Conn_02x05_Odd_Even", None),
    "Connector:TestPoint": ("Connector", "Connector", "TestPoint", None),
    "Mechanical:MountingHole": ("Mechanical", "Mechanical", "MountingHole", None),
    "power:GND": ("power", "power", "GND", None),
    "power:PWR_FLAG": ("power", "power", "PWR_FLAG", None),
}
if VARIANT == "direct":
    LIBS["Device:Polyfuse"] = ("Device", "Device", "Polyfuse", None)
    LIBS["Device:C"] = ("Device", "Device", "C", None)

# All three headers are plain 2.00 mm vertical male, to match the capsules'
# own H1/H2 and the breakout's J3. Nothing is shrouded: at 2.00 mm the stock
# libraries have no boxed header, keying would mean a different crimp system
# at each end of the cable, and reversal is harmless anyway -- see BREAKOUT_J3.
FP_2X5 = "Connector_PinHeader_2.00mm:PinHeader_2x05_P2.00mm_Vertical"
FP_1X03 = "Connector_PinHeader_2.00mm:PinHeader_1x03_P2.00mm_Vertical"
FP_1X02 = "Connector_PinHeader_2.00mm:PinHeader_1x02_P2.00mm_Vertical"
# 2.0 x 2.0 mm pad on a 1.0 mm hole: big enough to take a cable screen, a
# shielding-foil tail or a bridge earth in stripped wire up to about 18 AWG.
FP_PAD = "TestPoint:TestPoint_THTPad_2.0x2.0mm_Drill1.0mm"
# M2, not M2.5, and 2.2 mm rather than 2.7: the hole pattern is Cycfi's, taken
# off internal_breakout.brd -- see MOUNTING_PATTERN. The `direct` variant keeps
# M2 for the screws' sake but not the pattern, which has nothing left to match.
FP_HOLE = "MountingHole:MountingHole_2.2mm_M2"

# The two parts on the `direct` board. 0805 rather than 1206 because they live
# in a 2.5 mm band between the jack and power rows and a 1206 courtyard does
# not fit it; plain land patterns rather than HandSolder for the same reason.
FP_FUSE = "Fuse:Fuse_0805_2012Metric"
FP_CAP = "Capacitor_SMD:C_0805_2012Metric"

# Pins deliberately left unconnected. verify.py treats every other floating
# pin as an error, so this is where an intentional one is declared -- next to
# the circuit rather than buried in the checker.
if VARIANT == "breakout":
    NO_CONNECT = tuple(("J1", str(pin)) for pin in BREAKOUT_UNUSED)
else:
    # Nine of the jack's fifteen channel positions, because this hub carries
    # six. Every one of them is a deliberate omission rather than a miss --
    # driving CH7 or CH8 from here would contend with whatever else is on the
    # jack, exactly as it would on the breakout's J3.
    NO_CONNECT = tuple((ref, str(pin))
                       for ref, pins in JACK_UNUSED.items()
                       for pin in pins)

# The board carries no components, and this is the statement of that rather
# than an accident of nobody having added one. The capsules decouple
# themselves -- CAPSULE_DECOUPLING -- so a capacitor here would be a second
# bypass 200 mm of cable away from the rail it was bypassing, which is what
# the six on the previous revision were: parts that measured as wire.
#
# check_no_components() enforces it against the parts list.
NO_COMPONENTS = """
Nothing on this board is a component.

Every Nu capsule already carries 100 nF and 4.7 uF across its own supply pins,
at the pin, on the capsule PCB. Decoupling added here sits at the far end of a
cable from every load it could serve, and does nothing that the capsule's own
pair does not already do better.

Nor is there anything to protect: pin 1 of the capsule's power header goes
through a Schottky on the capsule, so reverse polarity is already handled
where it matters, and a reversed 2x5 delivers no supply at all rather than the
wrong one.

So this permits, permanently: connectors, mounting holes and one grounding
pad. If a resistor or a capacitor appears in the parts list, either the
circuit has changed or something has been added on instinct rather than on
evidence, and check_no_components() will say so.
"""
COMPONENT_FREE_LIBS = frozenset({
    "Connector_Generic:Conn_01x02",
    "Connector_Generic:Conn_01x03",
    "Connector_Generic:Conn_02x05_Odd_Even",
    "Connector:TestPoint",
    "Mechanical:MountingHole",
    "power:PWR_FLAG",
})

# The `direct` board is allowed exactly two parts, and the reason NO_COMPONENTS
# does not cover them is worth stating rather than assuming.
#
# That rule rejects *shunt* parts: a capacitor here sits a cable's length from
# every load it could serve, and does nothing the capsule's own 100 nF and
# 4.7 uF do not already do better, at the pin. Neither part below is that.
#
#   F1  is in *series* with the supply, so what it protects is the run it is
#       in, and there is no other place on the board that run passes through.
#       It is the only thing standing between a shorted capsule cable and
#       whatever feeds the 19-pin jack, because the breakout that used to
#       carry that job is what this variant deletes.
#
#   C1  is bulk at the point power enters the board, not decoupling at a load.
#       Its job is the ~200 mm of loom back to the jack, which the capsule's
#       own pair cannot see past.
#
# The distinction is series-versus-shunt and at-the-source-versus-at-the-load.
# Anything that does not clear both bars belongs on the capsule, not here.
DIRECT_ALLOWED_LIBS = COMPONENT_FREE_LIBS | {"Device:Polyfuse", "Device:C"}

ALLOWED_LIBS = (COMPONENT_FREE_LIBS if VARIANT == "breakout"
                else DIRECT_ALLOWED_LIBS)

# Four corner holes on the breakout-shaped board; two on the centreline of the
# small one, because a 30 mm connector block in a 33 mm board leaves no corner
# for a 4.9 mm courtyard. See the layout module for where they go and why the
# middle band is the only place they fit.
MOUNTING_HOLES = (("H1", "H2", "H3", "H4") if VARIANT == "breakout"
                  else ("H1", "H2"))

# Which rails need a PWR_FLAG, in the order the flags are numbered. Declared
# here rather than in each generator because the schematic has to draw exactly
# the flags the netlist declares, and #FLG02 meaning different things in the
# two files is the kind of drift verify.py would report as a missing part.
PWR_FLAG_RAILS = (("V+", "GND") if VARIANT == "breakout"
                  else ("VIN", "V+", "GND"))

# The board's outline and hole pattern are the Internal Breakout's, so one
# mount, one cavity and one enclosure pocket take either board. Measured off
# Cycfi's own internal_breakout.brd -- layer 20, the Eagle dimension layer --
# rather than read off a drawing:
#
#     outline    50.0 x 35.0 mm, corners rounded
#     holes      4 x 2.2 mm at 45.0 x 30.0 mm centres, 2.5 mm in from each edge
#
# Two things about that are approximations rather than transcriptions, and both
# are deliberate.
#
# Cycfi's four hole centres are not quite a rectangle -- the left pair are
# 29.9 mm apart and the right pair 30.0, and the four insets run 2.52 to 2.55.
# That is Eagle rounding, not intent, so this board uses the clean symmetric
# pattern every one of their holes is within 0.06 mm of. On a 2.2 mm hole
# taking an M2 screw that is a fifth of the clearance the screw already has.
#
# Their four corner arcs do not share a radius either: three work out at about
# 1.77 mm and one at 1.63. BOARD_R in gen_pcb.py is a true fillet at 1.75.
#
# THIS IS THE v2.5 OUTLINE. It is the only breakout geometry Cycfi have
# published in any form -- the v2.6.1 datasheet is a pinout document and
# carries no dimensions at all, and the 2023 redesign announcement carries
# none either. See docs/cycfi-sources.md.
MOUNTING_PATTERN = {
    "source": "cycfi/nu internal_breakout/internal_breakout.brd, Eagle layer 20",
    "outline": (50.0, 35.0),
    "hole_drill": 2.2,
    "hole_screw": "M2",
    "hole_centres": (45.0, 30.0),
    "hole_inset": 2.5,
}


class Part:
    def __init__(self, ref, value, lib_id, footprint, units=1,
                 datasheet="~", description="", dnp=False, mpn=""):
        self.ref = ref
        self.value = value
        self.lib_id = lib_id
        self.footprint = footprint
        self.units = units
        self.datasheet = datasheet
        self.description = description
        self.dnp = dnp
        self.mpn = mpn


class Design:
    def __init__(self, variant=None):
        self.variant = variant or VARIANT
        self.parts = {}
        self.nets = {}

    def add(self, part):
        assert part.ref not in self.parts, f"duplicate reference {part.ref}"
        self.parts[part.ref] = part
        return part

    def connect(self, net, *pins):
        """Attach (ref, pin) pairs to a net."""
        entries = self.nets.setdefault(net, [])
        for ref, pin in pins:
            assert ref in self.parts, f"{net}: unknown part {ref}"
            entry = (ref, str(pin))
            assert entry not in entries, f"{net}: {ref}.{pin} attached twice"
            entries.append(entry)

    def pin_owner(self):
        """Map (ref, pin) -> net, checking nothing is connected twice."""
        owner = {}
        for net, entries in self.nets.items():
            for entry in entries:
                assert entry not in owner, (
                    f"{entry} on both {owner[entry]} and {net}")
                owner[entry] = net
        return owner

    def check(self):
        self.pin_owner()
        for net, entries in self.nets.items():
            assert len(entries) >= 2, f"net {net} has only {entries}"
        self.check_no_components()
        self.check_against_cycfi()

    def check_no_components(self):
        """Enforce the parts allowance for this variant.

        `breakout` permits connectors, holes and a pad, nothing else.
        `direct` additionally permits F1 and C1 and nothing beyond them -- see
        DIRECT_ALLOWED_LIBS for why those two clear a bar that a decoupling
        capacitor here would not.
        """
        allowed = (COMPONENT_FREE_LIBS if self.variant == "breakout"
                   else DIRECT_ALLOWED_LIBS)
        offenders = sorted(ref for ref, part in self.parts.items()
                           if part.lib_id not in allowed)
        if offenders:
            raise AssertionError(
                f"{offenders} are not permitted on the {self.variant} board "
                f"-- see NO_COMPONENTS and DIRECT_ALLOWED_LIBS")
        if self.variant == "direct":
            extra = sorted(ref for ref, part in self.parts.items()
                           if part.lib_id not in COMPONENT_FREE_LIBS)
            if extra != ["C1", "F1"]:
                raise AssertionError(
                    f"the direct board carries {extra}, and the allowance is "
                    f"exactly ['C1', 'F1'] -- a third part means the "
                    f"series/shunt argument in DIRECT_ALLOWED_LIBS has been "
                    f"stretched rather than met")

    def check_against_cycfi(self):
        """The two pin maps, checked against the transcribed Cycfi tables.

        This is the whole design. Everything else on the board is copper
        joining these pins up, so if this passes and DRC passes, the board is
        right; and if this is wrong, nothing downstream would notice. ERC, the
        netlist comparison and DRC would all pass a hub wired to the wrong
        channels, because a wrong-but-consistent pin map is still consistent.
        """
        owner = self.pin_owner()

        if self.variant == "breakout":
            # -- the breakout end: J1 must be J3, pin for pin --------------
            for pin, net in BREAKOUT_J3.items():
                found = owner.get(("J1", str(pin)))
                if pin in BREAKOUT_UNUSED:
                    if found is not None:
                        raise AssertionError(
                            f"J1.{pin} is on {found}, but breakout J3.{pin} "
                            f"is {net}, which is shared with J4 -- it must "
                            f"stay unconnected, and it is also what makes a "
                            f"reversed cable harmless. See BREAKOUT_J3")
                    continue
                if found != net:
                    raise AssertionError(
                        f"J1.{pin} is on {found}, breakout J3.{pin} is {net} "
                        f"-- the cable is one-to-one, so these must be "
                        f"identical")
        else:
            # -- the jack end: J10 and J11 must be the breakout's, pin for
            # pin, because the loom that plugs into them is unchanged ------
            for ref, table in (("J10", JACK_J10), ("J11", JACK_J11)):
                for pin, net in table.items():
                    found = owner.get((ref, str(pin)))
                    if pin in JACK_UNUSED[ref]:
                        if found is not None:
                            raise AssertionError(
                                f"{ref}.{pin} is on {found}, but this hub "
                                f"carries six channels and {net} is not one "
                                f"of them -- driving it would contend with "
                                f"whatever else is on the jack. See "
                                f"JACK_UNUSED")
                        continue
                    if found != net:
                        raise AssertionError(
                            f"{ref}.{pin} is on {found}, the breakout has "
                            f"{net} there -- the loom is one-to-one, so these "
                            f"must be identical. See JACK_J10")

            # V+ must reach the capsules through F1 and not around it. A
            # spur from VIN straight to a power header would pass every other
            # check here: the nets would still be named right and every pin
            # would still be on one.
            if owner.get(("F1", "1")) != "VIN" or owner.get(("F1", "2")) != "V+":
                raise AssertionError(
                    f"F1 is not in series between VIN and V+ "
                    f"({owner.get(('F1', '1'))} -> {owner.get(('F1', '2'))}) "
                    f"-- the capsule supply must pass through it")
            for pin in ("7", "8"):
                if owner.get(("J11", pin)) != "VIN":
                    raise AssertionError(
                        f"J11.{pin} is not on VIN, so the supply does not "
                        f"enter through the jack")

        # -- the capsule end: every header must mirror H2 and H1 -----------
        for index in range(1, CHANNELS + 1):
            for ref, table, signal in (("P", CAPSULE["power"], None),
                                       ("S", CAPSULE["signal"], f"CH{index}")):
                for pin, capsule_net in table.items():
                    wanted = signal if capsule_net == "OUT" else capsule_net
                    found = owner.get((f"{ref}{index}", str(pin)))
                    if found != wanted:
                        raise AssertionError(
                            f"{ref}{index}.{pin} is on {found}, but the "
                            f"capsule's own header has {capsule_net} there "
                            f"(expected {wanted}) -- see CAPSULE")


def breakout_connector(design):
    """J1: the one connector that goes to the Internal Breakout.

    Wired one-to-one with breakout J3, which is the entire reason the cable
    can be a straight eight-way with nothing crossed in it. Positions 1 and 2
    are left out at both ends.
    """
    design.add(Part("J1", "TO BREAKOUT J3", "Connector_Generic:Conn_02x05_Odd_Even",
                    FP_2X5,
                    description="2x5 2.00mm to Internal Breakout J3 "
                                "(NU MULTI INPUT 1); pins 1-2 not fitted"))
    for pin, net in BREAKOUT_J3.items():
        if pin in BREAKOUT_UNUSED:
            continue
        design.connect(net, ("J1", pin))


def jack_connectors(design):
    """J10 and J11: the two 2x5s the instrument's 19-pin loom plugs into.

    Both are present even though J11 carries no channel this board drives,
    because the loom is Cycfi's and its two housings are a fixed pair. J11 is
    here for VIN and two of the three grounds; its six channel positions stay
    empty, as do three of J10's.
    """
    for ref, table, note in (("J10", JACK_J10, "channels 1-6 and a ground"),
                             ("J11", JACK_J11, "VIN and two grounds")):
        design.add(Part(ref, f"JACK {ref[1:]}",
                        "Connector_Generic:Conn_02x05_Odd_Even", FP_2X5,
                        description=f"2x5 2.00mm to the 19-pin output jack "
                                    f"loom -- {note}; wired one-to-one with "
                                    f"the breakout's {ref}"))
        for pin, net in table.items():
            if pin in JACK_UNUSED[ref]:
                continue
            design.connect(net, (ref, pin))


def power_conditioning(design):
    """The two parts on the board, and the only two permitted.

    VIN arrives from the jack, passes through F1, and leaves as V+ to the six
    capsule power headers. There is no regulator: Cycfi deleted theirs in
    breakout v2.6 because the Nu capsules run anywhere from 5 V to 18 V, so
    there is nothing here to regulate *to*.

    F1's hold current is the one number with a decision in it. Cycfi's 500 mA
    has to pass aux loads and fifteen channels; six capsules draw about 1 mA
    each -- a TLV170's quiescent plus roughly 200 uA of tail through the input
    pair -- so a 500 mA part would trip on nothing this board can do. See
    docs/DESIGN.md; measure before committing to a value.
    """
    design.add(Part("F1", "50mA", "Device:Polyfuse", FP_FUSE,
                    description="Polyfuse, 50 mA hold -- series protection "
                                "for the six capsule supplies"))
    design.connect("VIN", ("F1", 1))
    design.connect("V+", ("F1", 2))

    design.add(Part("C1", "10uF", "Device:C", FP_CAP,
                    description="Bulk across V+ at the point power enters the "
                                "board; not decoupling -- see NO_COMPONENTS"))
    design.connect("V+", ("C1", 1))
    design.connect("GND", ("C1", 2))


def capsule(design, index):
    """One capsule's pair of headers, mirroring the capsule's own H2 and H1.

    Two connectors and not one, because the capsule has two: power at one end
    of its PCB and signal at the other. Pin 1 is the west-most pad on both, so
    the whole board has one rule for which way round a housing goes.
    """
    string = STRINGS[index]

    design.add(Part(f"P{index}", f"CH{index} PWR", "Connector_Generic:Conn_01x03",
                    FP_1X03,
                    description=f"Capsule {index}, {string} -- power, to "
                                f"capsule H2: 1=V+, 2=GND, 3=GND"))
    design.connect("V+", (f"P{index}", 1))
    # Both of the capsule's ground pins, not just one. The capsule commits two
    # of its three power positions to ground, so carrying both fills the
    # housing -- which is worth as much for retention as it is for the halved
    # return resistance.
    design.connect("GND", (f"P{index}", 2), (f"P{index}", 3))

    design.add(Part(f"S{index}", f"CH{index} SIG", "Connector_Generic:Conn_01x02",
                    FP_1X02,
                    description=f"Capsule {index}, {string} -- signal, to "
                                f"capsule H1: 1=OUT, 2=GND"))
    design.connect(f"CH{index}", (f"S{index}", 1))
    design.connect("GND", (f"S{index}", 2))


def grounding(design):
    """One pad to land a ground tail on.

    Not a circuit feature -- GND is already poured across both layers. This is
    simply the one place the mask is open and the pad is big enough to solder
    a wire to, which is what stops somebody abrading the pour instead.

    Its designed job is the trunk cable's screen: docs/CABLES.md grounds that
    screen at one end only, and this is that end. Cavity foil is the second
    use and could equally go anywhere on the system ground. A bridge earth is
    a distant third -- the mechanism it defends against is largely handled by
    the capsules already being active and low-impedance, and it conventionally
    belongs at the system's main ground point rather than on a leaf board.
    """
    design.add(Part("E1", "SHIELD/GND", "Connector:TestPoint", FP_PAD,
                    description="Solder pad to GND: trunk cable screen, "
                                "cavity foil, optionally bridge earth"))
    design.connect("GND", ("E1", 1))


def mounting(design):
    """Four M2 clearance holes on the Internal Breakout's own pattern.

    The size and the spacing are not this board's to choose: they are Cycfi's,
    so that a mount or an enclosure pocket made for a breakout takes a hub
    too. See MOUNTING_PATTERN for where the numbers come from and what in them
    is measured rather than assumed.

    Not on the ground net. A hub screwed to a cavity floor has no defined
    chassis to bond to, and a plated, grounded hole would make the mounting
    hardware part of the audio ground the moment somebody used a metal screw
    into a shielded cavity -- a second ground path in parallel with the cable,
    which is exactly the loop the single-point pad at E1 exists to avoid.
    """
    for ref in MOUNTING_HOLES:
        design.add(Part(ref, "M2", "Mechanical:MountingHole", FP_HOLE,
                        description="M2 clearance hole, unplated"))


def flags(design):
    """PWR_FLAGs so ERC knows the rails arrive from a connector.

    There is no supply on this board and no part that drives anything, so
    without these ERC reports the rails as undriven. They are drawing
    annotations, not parts: they carry no footprint and never reach the board.

    The `direct` board needs three rather than two. V+ is not merely arriving
    from a connector there -- it arrives through F1, and a polyfuse is a
    passive, so ERC sees nothing driving the far side of it either.
    """
    for index, net in enumerate(PWR_FLAG_RAILS, start=1):
        ref = f"#FLG{index:02d}"
        design.add(Part(ref, "PWR_FLAG", "power:PWR_FLAG", ""))
        design.connect(net, (ref, 1))


def build(variant=None):
    variant = variant or VARIANT
    design = Design(variant)
    if variant == "breakout":
        breakout_connector(design)
    else:
        jack_connectors(design)
    for index in range(1, CHANNELS + 1):
        capsule(design, index)
    if variant == "direct":
        power_conditioning(design)
    grounding(design)
    mounting(design)
    flags(design)
    design.check()
    return design


DESIGN = build()
PARTS = DESIGN.parts
NETS = DESIGN.nets


def build_footprint(ref):
    """Footprint assigned to a reference, for the schematic writer."""
    return PARTS[ref].footprint


if __name__ == "__main__":
    d = build()
    print(f"{len(d.parts)} parts, {len(d.nets)} nets")
    for net in sorted(d.nets):
        print(f"  {net:6s} {len(d.nets[net]):3d} pins  "
              f"{', '.join(f'{r}.{p}' for r, p in d.nets[net])}")
