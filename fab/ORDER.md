# Ordering the Cycfi Nu hub

Upload `cycfi-nu-hub-pcbway.zip`. It holds the gerbers, the Excellon drill file
and this document, and it is only written when DRC is clean, so a board with
known errors cannot reach a fab from this repository by accident.

This is about as easy a board as gets made: two layers, no components, nothing
finer than a 0.30 mm track. Every stock process at every low-cost fab covers
it. What follows is the handful of things the gerbers do not say.

## The board

| | |
| --- | --- |
| **Layers** | **2**, 1 oz copper |
| **Board size** | **61.0 × 24.0 mm**, rectangular |
| Thickness | 1.6 mm |
| Soldermask | any colour |
| Silkscreen | white, top only — the bottom carries nothing |
| Surface finish | lead-free HASL is fine |
| Quantity | whatever the minimum is; you want one |

## The four things that are not in the gerbers

**1. The four mounting holes must not be plated.** They are 2.70 mm M2.5
clearance holes at the corners and they are deliberately off the ground net.
A hub screwed into a shielded cavity with metal screws and *plated* holes
would bond the audio ground to the cavity foil through the mounting hardware,
in parallel with the cable — a second ground path, which is the loop the
single-point pad at E1 exists to avoid. The drill file marks them NPTH. Some
fabs merge PTH and NPTH by default; do not let this one.

**2. Nothing is fitted.** This is a bare-board order. The board carries no
components at all, by design — see `DESIGN.md`. The parts list below is for
whoever builds the instrument, not for the fab.

**3. Route to the outline, no panel tabs inside it.** It is a plain rectangle
and there is copper 0.50 mm from every edge.

**4. Both layers are poured.** The large ground areas on F.Cu and B.Cu are
intentional and are not floods left over from routing.

## Holes

40 header holes at 0.80 mm, 1 pad hole at 1.00 mm and 6 vias at 0.40 mm, so
47 plated holes in total. Plus 4 unplated holes at 2.70 mm for mounting.

**18 placements**, all through-hole, none of them fitted at the fab.

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
H1/H2 and the breakout's J3:

| Qty | Part | Where |
| --- | --- | --- |
| 1 | 2×5 way | J1, to the Internal Breakout |
| 6 | 1×3 way | P1–P6, capsule power |
| 6 | 1×2 way | S1–S6, capsule signal |

A single 2.00 mm male header strip snapped to length covers all three; you
need 40 pins of it plus the 2×5.

Also 4 × M2.5 screws and standoffs, and — if you want it — a short length of
wire for E1.

### Cable

Everything on the board mates with **2.00 mm female crimp housings** on
0.50 mm square posts. Pick one connector family and stay inside it; Harwin's
M20/M22 range and Molex's Milli-Grid both cover 2.00 mm in single and dual
row, which means one crimp terminal and one tool for the whole loom.

| Cable | Housings | Positions each |
| --- | --- | --- |
| Hub → breakout, ×1 | 2 × 10-way (2×5) | 8 of 10 populated |
| Capsule power, ×6 | 2 × 3-way | 3 |
| Capsule signal, ×6 | 2 × 2-way | 2 |

That is 76 crimp terminals in total, and it is worth buying half as many
again: the first few are practice.

**The hub → breakout cable is wired straight through, position n to position
n, with positions 1 and 2 left empty at both ends.** Nothing crosses in it.
`DESIGN.md` has the pin table and explains why the two empty positions are
also what makes a reversed cable harmless.
