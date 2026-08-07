# The Cycfi Nu hub

Six individual **Cycfi Nu v2 capsules** onto channels 1–6 of a v2.6 **Cycfi
Internal Breakout**, so that wiring them up is thirteen crimped connectors
instead of a bundle of flying leads into a connector that was designed for a
pre-assembled Nu Multi.

The board is 50 × 35 mm — **the Internal Breakout's own outline and hole
pattern**, so the two mount the same way — two layers, and **carries no
components at all**. It is thirteen connectors, one solder pad, four holes and
some copper. That is not minimalism for its own sake — see
[No components](#no-components).

---

## What this replaces

Cycfi's breakout expects a **Nu Multi**: a pre-built assembly of capsules that
arrives on one 2×5 ribbon. If you have six separate capsules instead, you have
twelve connectors to get to that one 2×5, and each capsule contributes two of
them, at opposite ends of its own PCB.

    six capsules                    this board              breakout
    ------------                    ----------              --------
    H2  3-pin power  -- cable -->  P1..P6                \
    H1  2-pin signal -- cable -->  S1..S6                 >-- J1 --> J3
                                                         /   2x5

## Verified, not assumed

Everything about the two mating connectors was read out of Cycfi's Eagle
sources, at a recorded commit, and is transcribed in
[`cycfi-sources.md`](cycfi-sources.md). The three facts the board
depends on:

1. **The capsule has two connectors, not one.** A 3-pin 2.00 mm header for
   power at one end of its PCB, pin 1 = V+ through a reverse-polarity
   Schottky — and separately a 2-pin 2.00 mm header for signal at the other
   end, pin 1 = OUT through a 10 µF coupling cap.
2. **Pins 2 *and* 3 of the power header are ground.** The capsule commits two
   of its three power positions to it.
3. **The capsule decouples itself**: 100 nF and 4.7 µF across its own supply,
   on the capsule, at the pin.

These are not comments. `design.py` holds them as `CAPSULE` and
`BREAKOUT_J3`, and `Design.check_against_cycfi()` asserts the whole board's
pin map against them at import — so a hub wired to the wrong channels fails
to load rather than fails on the bench.

That check exists because nothing else would catch it. A wrong-but-consistent
pin map is still consistent: ERC passes, the netlist comparison passes, DRC
passes, and the first symptom is six strings coming out of the wrong outputs.

## The pin map — this *is* the design

`J1` is wired **one-to-one with breakout J3**. Position *n* on the cable goes
to position *n* at both ends; nothing crosses inside it.

| J1 / J3 pin | Net | Goes to |
| --- | --- | --- |
| 1 | *CH7* | **not fitted** |
| 2 | *CH8* | **not fitted** |
| 3 | CH5 | S5 pin 1 |
| 4 | CH6 | S6 pin 1 |
| 5 | CH3 | S3 pin 1 |
| 6 | CH4 | S4 pin 1 |
| 7 | CH1 | S1 pin 1 |
| 8 | CH2 | S2 pin 1 |
| 9 | V+ | P1–P6 pin 1 |
| 10 | GND | everything |

And at the capsule end, each channel *n*:

| Header | Pin | Net | Capsule |
| --- | --- | --- | --- |
| `Pn` (1×3) | 1 | V+ | H2 pin 1 |
| | 2, 3 | GND | H2 pins 2, 3 |
| `Sn` (1×2) | 1 | CH*n* | H1 pin 1 |
| | 2 | GND | H1 pin 2 |

**Pin 1 is the west-most pad on every header on the board**, including the
2×5. One rule, printed on the silkscreen, and asserted in
`gen_pcb.check_placement()` against the real pad coordinates rather than
trusted to a rotation convention.

## What must not be got wrong

### Leave positions 1 and 2 out of the cable

They are CH7 and CH8, and those nets are **shared with J4 pins 7–8** — the
breakout's second Nu Multi input. Driving them from here contends with
anything plugged in there.

### Reversal is harmless, and that is why

A 2×5 rotated in its own plane maps pin *n* to pin **11 − *n***. So a cable
plugged in backwards puts the two *empty* positions onto pins 10 and 9 — GND
and V+ — and the hub receives no supply at all. The capsules stay dark, the
hub's own V+ and GND land on CH8 and CH7 where nothing is driving them hard,
and nothing is damaged.

This is worth stating because it is the reason the board has a **plain,
unshrouded** 2×5. Shrouding at 2.00 mm means committing to a keyed family —
JST PHD or Hirose DF11 are the stock options whose pin numbering matches
Cycfi's — and that puts a *different crimp terminal at each end of the same
cable*, since the breakout end still has to mate with a plain header. Paying
that to protect against a failure whose entire consequence is "it does not
turn on" is a bad trade.

If the cable ever works loose under vibration, the answer is a tie or a dab of
hot glue, not a respin.

### The two 2.00 mm systems are not interchangeable

Everything here mates with **2.00 mm female crimp housings on 0.50 mm square
posts**. Pick one connector family and stay in it for the whole loom, so there
is one terminal and one tool. This is not the same as JST PH, which is also
2.00 mm and will not fit.

## No components

`design.py` states this as `NO_COMPONENTS` and enforces it in
`Design.check_no_components()`, which rejects any part that is not a
connector, a mounting hole or the grounding pad.

The previous revision of this board had six decoupling capacitors on it. They
were doing nothing, and the reason is worth keeping: **every Nu capsule
already carries 100 nF and 4.7 µF across its own supply pins, at the pin, on
the capsule PCB.** A capacitor on the hub sits at the far end of a cable from
every load it could serve. It is not decoupling; it is a part that measures as
wire.

There is nothing to protect either. Pin 1 of the capsule's power header goes
through a Schottky *on the capsule*, so reverse polarity is handled where it
matters, and — per above — a reversed 2×5 delivers no supply rather than the
wrong one.

So the board permits, permanently: connectors, mounting holes, one grounding
pad. If a resistor or capacitor appears in the parts list, either the circuit
has genuinely changed or something was added on instinct, and the build says
so.

## Grounding

GND is poured on **both** layers. On a two-layer board that is mostly air the
copper is free, and what it buys is a return directly under every signal trace
and a reference plane between the six of them. Against a Nu's low-impedance
op-amp output that is worth little — but it is worth nothing against it
either, and it costs the same to fabricate. Six stitching vias tie the pours
together, on top of the nineteen through-hole GND pads that already do.

### E1

A 2.0 × 2.0 mm pad on a 1.0 mm hole, on GND, silkscreened SHIELD / GND.

**It is not a circuit feature.** GND is already poured across both layers, so
E1 adds no connection — it is simply the one place where the mask is open and
the pad is big enough to solder a wire to. That is its whole point: without
it, somebody eventually abrades the pour or hangs a tail off an occupied
connector pin. It costs one hole and no board area, since the west margin it
sits in is set by the mounting holes and would be empty anyway.

It has three jobs, and only the first is designed in.

**The trunk cable's screen.** [`CABLES.md`](CABLES.md) specifies screened cable
for the hub → breakout run with the screen grounded **at one end only**, so it
cannot become a second ground path in parallel with the GND conductor in
position 10. E1 is that end. Use screened cable and the pad stops being
optional — there is nowhere else for the drain to go.

**Cavity foil.** Shielding does nothing unless it is tied to circuit ground,
and left floating it can couple slightly worse than none. But foil carries
only displacement currents, so it can be grounded anywhere on the system —
the hub is convenient, not required.

**A bridge earth, distantly.** Weaker here than the convention suggests. The
mechanism it defends against — the player's body coupling mains hum into a
high-impedance circuit — is largely handled already by every Nu output being
an op-amp behind a 10 µF capacitor into low-impedance cabling. Against that,
it is the connection that puts the player at circuit ground through the
strings, which in an upstream fault is a path toward mains potential, and it
conventionally belongs at the system's main ground point rather than on a leaf
board at the far end of a cable. Fitting the pad does not commit you to using
it for this, and the silkscreen deliberately does not say BRIDGE.

One objection that does *not* stand up: that landing a tail here makes the hub
a ground meeting point, so its return shares the single GND wire in the cable
with six signal returns. At microamps through tens of milliohms that is
nanovolts. It is not a real mechanism at these levels.

**The four mounting holes are unplated and off the ground net**, deliberately.
A hub screwed into a shielded cavity with metal screws and plated holes would
bond the audio ground to the foil through the mounting hardware, in parallel
with the cable — a second ground path, which is the loop the single-point pad
exists to avoid.

## How the board came out

**50 × 35 mm with 1.75 mm corners and four M2 holes on 45 × 30 mm centres —
the Internal Breakout's own outline**, so one mount, one cavity cut-out or one
enclosure pocket takes either board. The numbers were measured off Cycfi's
`internal_breakout.brd` (Eagle layer 20) and live in `design.MOUNTING_PATTERN`;
`gen_pcb.py` derives every dimension from there and asserts the hole centres
against it, so the outline cannot drift away from the board it is copying.

Read [the outline is v2.5's](#the-outline-is-v25s) before cutting anything
that has to fit a real breakout.

Inside it the board is three bands: signal headers across the north, power
headers across the south, and between them a middle band carrying the 2×5 at
its east end, the fan-in to it, the V+ bus and the grounding pad. Six channel
columns on a 7 mm pitch with **CH1 (low E) at the west**, so reading the board
left to right still reads the strings low to high, and the two capsule bundles
still leave on opposite edges with the trunk leaving east.

Six columns at 7 mm plus a 1×3's courtyard at each end is 42 mm of the 50
available. There is no slack in the width: `gen_pcb.py` asserts the columns
are centred, and moving them costs the fan-in its margin at the east edge.

`verify.check_string_order()` reads the string order back off the built
copper. Nothing electrical would notice it being wrong.

### The one hard part: reaching the far row of J1

The 2×5's pads are 1.35 mm on a 2.00 mm pitch. The clear gap between two of
them is **0.65 mm**, and a 0.30 mm track with 0.25 mm either side needs
**0.80 mm**. Nothing can be routed between the pads of a 2.00 mm header, so
the far row cannot be reached from the near side at all. `rules.py` asserts
this rather than leaving it as folklore, because the whole layout is shaped by
it.

So the near row — J1's odd pins, CH5/CH3/CH1 — is reached directly from the
west on F.Cu, and the far row — even pins, CH6/CH4/CH2 — goes **north of the
signal headers on B.Cu, east above the whole row, down the outside of the
connector, and back in from the east**, where nothing is in the way. Three
concentric L-shaped paths around the north-east corner.

Two placement decisions make that fan-in planar, and both are the opposite of
what looks natural:

- **CH1 at the west, J1 at the east.** The connector puts CH1/CH2 on its
  southern pair and CH5/CH6 on its northern one, so a channel's target *y*
  falls as its number falls. With CH1 furthest from the connector, the
  westmost channel wants the deepest lane, and every drop clears every lane
  already laid. Mirror the board and all three cross.
- **The detour goes north of the signal headers, not between them and J1.**
  Each lane is reached by a drop out of its own header, and each descent
  begins at its own lane. So the outermost path needs the lane furthest from
  the header row *and* a lane outside every descent — and those are the same
  direction only on the side the descents run away from. North, they coincide
  and the three paths nest. South, they oppose: the outermost lane clears the
  drops and then crosses CH4's descent on its way east.

I got the second one wrong twice on the 61 × 24 strip before checking it as a
planarity problem rather than by eye, and wrong once more on this outline —
the middle band here is wide enough to look like the obvious home for the
lanes, and DRC reported the crossing within a minute. `check_placement()` now
asserts that the lane order and the descent order are reverses of each other,
which is the property that was being violated each time.

### Everything else

- The power row has no gaps: six 1×3 footprints on a 7 mm pitch leave 0.78 mm
  between silk outlines, which is why nothing crosses it and why the power
  designators are printed above the row instead of beside it.
- The mounting holes no longer set the board width — the breakout does — but
  they became harder to route around, not easier. At 2.5 mm in from all four
  edges, H3 sits in the same north-east margin the three descents run down,
  and CH2's lane passes 1.95 mm from its centre against a 1.35 mm minimum. An
  unplated hole has no pad, no net and no courtyard, so it is invisible to
  every other check in `gen_pcb.py`: `check_holes_clear()` exists because a
  track laid straight across one would build clean, match the netlist and
  arrive as a board with a screw hole through a signal.
- The corners are rounded to 1.75 mm because the breakout's are. A square
  corner is *more* material than a round one, so matching the outline and
  leaving the corners sharp would give a board that measures right and will
  not drop into the pocket. The pours follow the radii in as well —
  inset as a plain rectangle their corners poke 0.02 mm past the arc.
- V+ runs as one bus on F.Cu between J1's bottom pair and the power row.
  0.60 mm, which is not about current — six capsules draw single-figure
  milliamps between them — but about keeping the run stiff and inspectable.
- The build gates on DRC **warnings as well as errors**. It did not at first,
  and asking only for errors hid twenty-seven violations of this project's own
  rules: every legend was under the minimum silk text height written into the
  `.kicad_pro`, and six designators overlapped their own footprint outlines.
  None of it would have scrapped a board and all of it would have reached one.
  `rules.MIN_SILK_TEXT` is now the single place that height is declared, so
  the generator and the checker cannot disagree about it again.

## Still open

**The breakout revision — mostly resolved.** Cycfi's published *sources* are
silkscreened *INTERNAL BREAKOUT V2.5* and this hub targets **v2.6**. They have
not published 2.6 Eagle files, but they do publish a
[v2.6.1 datasheet](https://www.cycfi.com/assets/Internal-Breakout-2.6.pdf),
and its "Nu Multi Inputs Ch 1-8" diagram gives the two rows as

    Ch8  Ch6  Ch4  Ch2  Gnd
    Ch7  Ch5  Ch3  Ch1  10v

which pairs **exactly** as the v2.5 sources do — CH7/CH8, CH5/CH6, CH3/CH4,
CH1/CH2, supply/ground. The pin map this board is built on survives the
revision.

What a printed pin map cannot tell you is which physical end of the connector
is position 1, and v2.6 is a physical redesign, so the connector may well sit
differently. That is still one meter reading to settle: **pin 9 to the supply
rail, pin 10 to ground, pin 7 to channel 1.** [`CABLES.md`](CABLES.md) has it
as a numbered step.

### The outline is v2.5's

This board is 50 × 35 mm because that is what Cycfi's `internal_breakout.brd`
measures, and that file is **v2.5**. No dimension for v2.6 has ever been
published: the v2.6.1 datasheet is a pinout document with no measurements in
it, and the 2023 announcement of the redesign gives none either. So the
outline this board copies is the only breakout outline that exists in
measurable form, and it is a revision behind the one the hub is wired for.

An earlier revision of these docs claimed Cycfi list v2.6 as 27 × 38 mm. That
was a misattribution — the figure is from the Nu Series **v1** page and names
no version. [`cycfi-sources.md`](cycfi-sources.md) records what happened.

Two consequences, and only the second one costs anything:

- **Electrically, nothing.** The outline is not part of the circuit. The pin
  map is what matters and it is cross-checked against the v2.6.1 datasheet
  above.
- **Mechanically, it is an assumption.** A pocket, bracket or cavity cut from
  `fab/cycfi-nu-hub-mechanical.json` fits a hub and a v2.5 breakout. Whether
  it fits a **v2.6** breakout is unknown. The JSON carries that caveat in an
  `outline_source` field so it crosses into the enclosure repository with the
  geometry rather than being remembered separately.

**Measure a v2.6 board before anything is cut to fit one.** Four numbers
settle it: overall width and height, hole diameter, and hole centres in both
axes. If they differ, `design.MOUNTING_PATTERN` is the one block that changes
and the layout re-derives from it.

**What voltage the capsules will see.** On v2.5 the Nu Multi input's supply
pin is a net called V+, fed from `J14`, a jumper silkscreened `PWR SELECT`
that chooses between the unregulated input and the LP2985 output. On v2.6.1
the same pin is labelled simply **10V**. The hub passes through whatever it
is, so the board does not care — but six capsules do. Measure it at the hub
with no capsules connected before fitting any.

**Nothing has been fabricated yet.** No board has been made, no cable crimped
and nothing measured. Every claim here is from the sources and the generators.
