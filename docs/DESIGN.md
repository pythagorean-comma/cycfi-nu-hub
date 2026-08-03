# The Cycfi Nu hub

Six individual **Cycfi Nu v2 capsules** onto channels 1–6 of a v2.6 **Cycfi
Internal Breakout**, so that wiring them up is thirteen crimped connectors
instead of a bundle of flying leads into a connector that was designed for a
pre-assembled Nu Multi.

The board is 61 × 24 mm, two layers, and **carries no components at all**. It
is thirteen connectors, one solder pad, four holes and some copper. That is
not minimalism for its own sake — see [No components](#no-components).

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

**E1** is a 2.0 × 2.0 mm pad on a 1.0 mm hole, on GND, for a bridge earth or a
cavity-shielding tail. It is optional. Fitting the pad does not commit you to
using it, and in an all-active instrument some builders deliberately leave the
bridge floating — that is the path that puts the player at mains potential if
something upstream fails. Use it for foil and decide about the bridge
separately.

The objection to landing bridge earth here is that it makes the hub the ground
meeting point, so string-borne hum shares the single GND wire in the cable
with six signal returns. At microamps through tens of milliohms that is
nanovolts. It is not a real mechanism at these levels.

**The four mounting holes are unplated and off the ground net**, deliberately.
A hub screwed into a shielded cavity with metal screws and plated holes would
bond the audio ground to the foil through the mounting hardware, in parallel
with the cable — a second ground path, which is the loop the single-point pad
exists to avoid.

## How the board came out

A 61 × 24 mm strip. Signal headers along the north edge, power headers along
the south, the 2×5 at the east end, six channel columns on a 7 mm pitch with
**CH1 (low E) at the west**, so reading the board left to right reads the
strings low to high. The two cable bundles leave on opposite edges.

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
  Put the lanes south of the header row and the drops cross them; put them
  north and the headers sit on the boundary, where the three paths nest.

I got the second one wrong twice before checking it as a planarity problem
rather than by eye.

### Everything else

- The power row has no gaps: six 1×3 footprints on a 7 mm pitch leave 0.78 mm
  between silk outlines, which is why nothing crosses it and why the power
  designators are printed above the row instead of beside it.
- The two eastern mounting holes set the board width. Their courtyards are
  6 mm across because they have to clear a screw head, and they have to sit
  clear of the three descents to J1's far row.
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
is position 1, and the v2.6 board is a different shape from the v2.5 one
(Cycfi list it as 27 × 38 mm against the 50 × 35 mm in the Eagle files), so
the connector may well sit differently. That is still one meter reading to
settle: **pin 9 to the supply rail, pin 10 to ground, pin 7 to channel 1.**
[`CABLES.md`](CABLES.md) has it as a numbered step.

**What voltage the capsules will see.** On v2.5 the Nu Multi input's supply
pin is a net called V+, fed from `J14`, a jumper silkscreened `PWR SELECT`
that chooses between the unregulated input and the LP2985 output. On v2.6.1
the same pin is labelled simply **10V**. The hub passes through whatever it
is, so the board does not care — but six capsules do. Measure it at the hub
with no capsules connected before fitting any.

**Nothing has been fabricated yet.** No board has been made, no cable crimped
and nothing measured. Every claim here is from the sources and the generators.
