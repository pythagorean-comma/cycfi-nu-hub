# Cycfi Nu Hub

A 6-channel hub board for wiring six individual **Cycfi Nu v2 capsules** into a v2.6
**Cycfi Internal Breakout** on channels 1–6.

Built against Cycfi's published Eagle sources at
<https://github.com/cycfi/nu>

61 × 24 mm, two layers, and **no components** — thirteen connectors, a
grounding pad and some copper. The capsules already decouple themselves, so
there is nothing left for this board to do but join things up correctly.

## Everything is generated

`design.py` is the single source of truth for the circuit. `gen_sch.py` draws
the schematic from it, `gen_pcb.py` places and routes the board from it, and
`verify.py` reads KiCad's own netlist back and compares it net by net.

```bash
./build.sh
```

That regenerates schematic *and* board, runs ERC, checks both against
`design.py`, runs DRC, and writes `fab/cycfi-nu-hub-pcbway.zip`, but **only
when DRC is clean**, so a board with known faults cannot reach a fab by
accident.

> **Anything changed in the KiCad GUI is destroyed by the next build.** Use the
> editor to inspect, measure and try things out; changes that should survive
> belong in the generator.

`design.py` also holds the two pin maps transcribed from Cycfi's schematics
and asserts the board against them at import, so a hub wired to the wrong
channels fails to load rather than fails on the bench.

## Requirements

**KiCad 10.x.** Install with `brew install --cask kicad`, or from
<https://www.kicad.org/download/>. The file formats written are version
specific: KiCad 9 will not open the generated schematic.

**No Python packages.** There is no virtual environment and no
`requirements.txt`, because there is nothing to install: the generators are
pure standard library. The one exception is `pcbnew`, which ships inside KiCad,
so `build.sh` runs `gen_pcb.py` under KiCad's own bundled interpreter and
everything else under `python3`. Set `PYTHON` to override which one.

`kicad.py` finds the installation. It checks `$KICAD_APP`, then
`/Applications/KiCad/KiCad.app`, then `~/Applications/KiCad/KiCad.app`, then
`kicad-cli` on `PATH`. If yours lives somewhere else:

```bash
export KICAD_APP=/path/to/KiCad.app
```

Run `python3 kicad.py` to see what it found.

## Where to read next

| | |
| --- | --- |
| [`docs/DESIGN.md`](docs/DESIGN.md) | What the board does and why, what must not be got wrong when wiring it, how it came out, and what is still open. **Start here.** |
| [`docs/CABLES.md`](docs/CABLES.md) | How to make the thirteen cables: parts, suppliers, position-by-position tables, and the continuity checks to run before anything is powered. |
| [`fab/ORDER.md`](fab/ORDER.md) | How to order it, including the four requirements that are invisible in the gerbers, and what to buy alongside it. It lives beside the gerbers rather than in `docs/` because `build.sh` copies it into the fabrication zip and `verify.py` checks the board against its figures. |
| [`docs/cycfi-sources.md`](docs/cycfi-sources.md) | What Cycfi's own files say, at a recorded commit, and how to re-extract it. Records, not specifications — where they and `docs/DESIGN.md` differ, `docs/DESIGN.md` is right. |

## Status

Generated, checked and clean: ERC 0, DRC 0 — **warnings included, not just
errors** — and the schematic matches `design.py` across 8 nets and 39 pin
connections. A fabrication package is written.

**Nothing has been made yet.** No board has been fabricated, no cable crimped
and nothing measured, so every claim in this repository comes from Cycfi's
sources and from the generators — not from a bench.

Two things to settle before ordering, both in the last section of
[`docs/DESIGN.md`](docs/DESIGN.md): Cycfi publish sources for breakout **v2.5** and this
targets **v2.6**, which is three continuity readings on J3 to confirm; and the
breakout's `PWR SELECT` jumper decides what voltage six capsules will see.
