# Ordering the Cycfi Nu hub — direct variant

Upload `cycfi-nu-hub-direct-pcbway.zip`. It holds the gerbers, the Excellon
drill file and this document, and it is only written when DRC is clean, so a
board with known errors cannot reach a fab from this repository by accident.

**This is not the breakout-facing hub.** That board is
[`ORDER.md`](ORDER.md), 50 × 35 mm, no components. This one deletes the
Internal Breakout from the chain and drives the instrument's 19-pin output jack
itself. Read [`../docs/DESIGN.md`](../docs/DESIGN.md) before ordering it: it
depends on an assumption about the v2.6 breakout's jack interface that has not
been confirmed against hardware.

Still an easy board — two layers, two components, nothing finer than a 0.30 mm
track — but a smaller and busier one than the other variant. What follows is
the handful of things the gerbers do not say.

## The board

| | |
| --- | --- |
| **Layers** | **2**, 1 oz copper |
| **Board size** | **35.0 × 24.5 mm**, corners rounded to R1.50 |
| Thickness | 1.6 mm |
| Soldermask | any colour |
| Silkscreen | white, top only — the bottom carries nothing |
| Surface finish | lead-free HASL is fine |
| Quantity | whatever the minimum is; you want one |

## The four things that are not in the gerbers

**1. The two mounting holes must not be plated.** They are 2.20 mm M2
clearance holes and they are deliberately off the ground net. A hub screwed
into a shielded cavity with metal screws and *plated* holes would bond the
audio ground to the cavity foil through the mounting hardware, in parallel with
the loom — a second ground path, which is the loop the single-point pad at E1
exists to avoid. The drill file marks them NPTH. Some fabs merge PTH and NPTH
by default; do not let this one.

**2. Two components, both 0805, both on the top.** `F1` is a polyfuse and `C1`
is a capacitor — see the parts list below. This is still a bare-board order
unless you are having it assembled; the parts are for whoever builds the
instrument.

**3. Route to the outline, no panel tabs inside it.** It is a rectangle with
1.50 mm radius corners, and there is copper 0.50 mm from every edge. The pours
follow the corner radii in, so a tab breaking into one takes copper with it.

**4. Both layers are poured.** The large ground areas on F.Cu and B.Cu are
intentional and are not floods left over from routing.

## Holes

50 header holes at 0.80 mm, 1 pad hole at 1.00 mm and 8 vias at 0.40 mm, so
59 plated holes in total. Plus 2 unplated holes at 2.20 mm for mounting.

Six of the eight vias are not stitching. They carry CH2, CH4 and CH6 between
layers halfway along their run — see `layout_direct.py` for why that detour
cannot be done on one layer.

**19 placements**, 17 through-hole and 2 SMD.

## Design rules

Every number here comes from `rules.py`, which is also what `gen_project.py`
writes into the KiCad project for DRC to enforce, so the board was laid out to
exactly these and checked against exactly these.

| | |
| --- | --- |
| Min track width | 0.30 mm |
| Power track width | 0.60 mm |
| Min clearance | 0.25 mm |
| Min drill | 0.40 mm |
| Min annular ring | 0.20 mm |
| Via pad / drill | 0.80 / 0.40 mm |
| Board edge clearance | 0.50 mm |

The annular ring is the only figure with real arithmetic behind it: a
fabricator's cumulative drill and registration error runs to about 0.003"
(0.076 mm), which leaves 0.124 mm of ring in the worst case against an
IPC-2221 Class 2 minimum of 0.05 mm.

## What to buy alongside it

Headers, all **2.00 mm pitch vertical male**, to match the Nu capsules' own
H1/H2 and the breakout's J10/J11:

| Qty | Part | Where |
| --- | --- | --- |
| 2 | 2×5 way | J10, J11, to the 19-pin jack loom |
| 6 | 1×3 way | P1–P6, capsule power |
| 6 | 1×2 way | S1–S6, capsule signal |

A single 2.00 mm male header strip snapped to length covers the single-row
positions; you need 30 pins of it plus the two 2×5s.

### The two components

| Ref | Value | Package | Notes |
| --- | --- | --- | --- |
| F1 | 50 mA hold polyfuse | 0805 | **Confirm the value.** See below. |
| C1 | 10 µF | 0805 | Rated for VIN with margin — measure VIN first |

**F1's hold current is a decision, not a transcription.** Cycfi's breakout uses
500 mA, but that has to pass aux loads and up to fifteen channels. Six capsules
draw roughly 1 mA each, so a 500 mA part would never trip on anything this
board can do. 50 mA is the honest figure for six capsules — but measure the
actual draw before committing, and size C1's voltage rating once you know what
VIN is in your instrument. The capsules run anywhere from 5 V to 18 V.

Also 2 × M2 screws and standoffs, and — if you want it — a short length of
wire for E1.

### Cable

The twelve capsule cables are unchanged from the other variant:
[`../docs/CABLES.md`](../docs/CABLES.md) has the part numbers, suppliers and a
position table for every one.

What changes is the trunk. There is no hub → breakout cable, because there is
no breakout: `J10` and `J11` present the same two 2×5 headers the breakout
does, so the instrument's existing 19-pin jack loom plugs straight into this
board.

**That is the assumption this variant rests on, and it is not yet confirmed
against a v2.6 board.** If the v2.6 presents its jack differently, this board
is wrong and the breakout-facing variant is the one to order.

**Check the loom's orientation before powering anything.** Unlike the other
board, a reversed connector here is not harmless: rotating a 2×5 maps pin *n*
to pin 11−*n*, which on J10 puts pin 2 (CH1) onto pin 9 (GND) and shorts the
capsule outputs to ground. Recoverable, but worth a continuity check first —
the silkscreen says so too.
