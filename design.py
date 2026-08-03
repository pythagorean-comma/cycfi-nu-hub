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

CHANNELS = 6

# Shared by the schematic, the board and the project scaffolding. The
# schematic's symbol UUIDs are derived from this name, and the board's
# footprints are linked back to those UUIDs, so the two generators must agree
# on it exactly -- hence one constant rather than three string literals.
PROJECT = "cycfi-nu-hub"

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
FP_HOLE = "MountingHole:MountingHole_2.7mm_M2.5"

# Pins deliberately left unconnected. verify.py treats every other floating
# pin as an error, so this is where an intentional one is declared -- next to
# the circuit rather than buried in the checker.
NO_CONNECT = tuple(("J1", str(pin)) for pin in BREAKOUT_UNUSED)

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

MOUNTING_HOLES = ("H1", "H2", "H3", "H4")


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
    def __init__(self):
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
        """Enforce NO_COMPONENTS: connectors, holes and a pad, nothing else."""
        offenders = sorted(ref for ref, part in self.parts.items()
                           if part.lib_id not in COMPONENT_FREE_LIBS)
        if offenders:
            raise AssertionError(
                f"{offenders} are not connectors, mounting holes or the "
                f"grounding pad -- see NO_COMPONENTS")

    def check_against_cycfi(self):
        """The two pin maps, checked against the transcribed Cycfi tables.

        This is the whole design. Everything else on the board is copper
        joining these pins up, so if this passes and DRC passes, the board is
        right; and if this is wrong, nothing downstream would notice. ERC, the
        netlist comparison and DRC would all pass a hub wired to the wrong
        channels, because a wrong-but-consistent pin map is still consistent.
        """
        owner = self.pin_owner()

        # -- the breakout end: J1 must be J3, pin for pin ------------------
        for pin, net in BREAKOUT_J3.items():
            found = owner.get(("J1", str(pin)))
            if pin in BREAKOUT_UNUSED:
                if found is not None:
                    raise AssertionError(
                        f"J1.{pin} is on {found}, but breakout J3.{pin} is "
                        f"{net}, which is shared with J4 -- it must stay "
                        f"unconnected, and it is also what makes a reversed "
                        f"cable harmless. See BREAKOUT_J3")
                continue
            if found != net:
                raise AssertionError(
                    f"J1.{pin} is on {found}, breakout J3.{pin} is {net} -- "
                    f"the cable is one-to-one, so these must be identical")

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
    """Four M2.5 clearance holes, one per corner.

    Not on the ground net. A hub screwed to a cavity floor has no defined
    chassis to bond to, and a plated, grounded hole would make the mounting
    hardware part of the audio ground the moment somebody used a metal screw
    into a shielded cavity -- a second ground path in parallel with the cable,
    which is exactly the loop the single-point pad at E1 exists to avoid.
    """
    for ref in MOUNTING_HOLES:
        design.add(Part(ref, "M2.5", "Mechanical:MountingHole", FP_HOLE,
                        description="M2.5 clearance hole, unplated"))


def flags(design):
    """PWR_FLAGs so ERC knows V+ and GND arrive from the connector.

    There is no supply on this board and no part that drives anything, so
    without these ERC reports the two rails as undriven. They are drawing
    annotations, not parts: they carry no footprint and never reach the board.
    """
    for index, net in enumerate(("V+", "GND"), start=1):
        ref = f"#FLG{index:02d}"
        design.add(Part(ref, "PWR_FLAG", "power:PWR_FLAG", ""))
        design.connect(net, (ref, 1))


def build():
    design = Design()
    breakout_connector(design)
    for index in range(1, CHANNELS + 1):
        capsule(design, index)
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
