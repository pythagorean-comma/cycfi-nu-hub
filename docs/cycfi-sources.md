# What Cycfi's files actually say

A record, not a specification. Where this and [`DESIGN.md`](DESIGN.md)
differ, `DESIGN.md` is right — but nothing here should differ, because
`design.py` asserts the pin maps below at import and the build fails if they
drift.

The pin maps below were read out of Cycfi's own Eagle sources — not from their
forum, not from a photograph of a board. The one exception is the v2.6.1
cross-check, which comes from their published datasheet and is labelled as
such.

| | |
| --- | --- |
| Repository | <https://github.com/cycfi/nu> |
| Commit | `dc334a32f05ff16e0e7419b5c41f4c18d135e86d`, 2021-12-14 |
| Branch note | "Merge branch 'master' into version_2.5" |
| Files | `nu_capsule/nu_preamp.sch`, `internal_breakout/internal_breakout.sch`, and the matching `.brd` for connector geometry |
| Format | Eagle 6.3 XML, parsed with `xml.etree` |
| Licence | CC BY-NC 4.0 — their schematics, quoted here for interoperability |

The breakout silkscreen in this commit reads **INTERNAL BREAKOUT V2.5**. The
hub targets a v2.6 breakout, for which Cycfi have not published Eagle files —
but they have published a datasheet, and it corroborates the pin map. See
[v2.6.1, cross-checked](#v261-cross-checked) at the end.

## v2.6.1, cross-checked

Second source: **<https://www.cycfi.com/assets/Internal-Breakout-2.6.pdf>**,
"Internal Breakout v2.6.1", 11 pages. Not schematics — a pinout datasheet. Its
page 3 diagram labels the two rows of the Nu Multi Ch 1-8 connector:

    Ch8  Ch6  Ch4  Ch2  Gnd
    Ch7  Ch5  Ch3  Ch1  10v

and the Ch 7-14 connector beside it:

    Ch14 Ch12 Ch10 Ch8  Gnd
    Ch13 Ch11 Ch9  Ch7  10v

Read as column pairs, that is CH7/CH8, CH5/CH6, CH3/CH4, CH1/CH2, supply/GND
— **identical to the v2.5 J3 table below**, including the CH7/CH8 overlap
between the two connectors. The hub's pin map holds across the revision.

Two differences worth recording:

- The supply pin is labelled **10V** on 2.6.1, where the v2.5 schematic calls
  the net `V+` and feeds it from the `PWR SELECT` jumper. Measure it rather
  than assuming which.
- **The v2.6 board's size is not published anywhere.** This datasheet carries
  no dimensions at all — it is a pinout document, eleven pages of connector
  diagrams — and neither does the
  [2023 redesign announcement](https://www.cycfi.com/2023/04/internal-breakout-redesign/)
  that introduced v2.6. So it is not known whether the connector sits where
  the Eagle files put it.

  An earlier revision of this document said Cycfi list v2.6 as 27 × 38 mm.
  **That was wrong.** The figure is real but it is not v2.6's: it comes from
  the prose on the [Nu Series **v1** project
  page](https://www.cycfi.com/projects/nu-series/) — "The small (27mm x 38mm)
  internal breakout board…" — a page Cycfi themselves head with a notice
  pointing to v2, and which names no breakout version at all. It was quoted
  here as a v2.6 specification, which it never was. The only measured
  breakout outline in existence is the 50 × 35 mm one in the Eagle files
  below.

The rest of this document is the v2.5 Eagle extraction, unchanged.

## The capsule — `nu_capsule/nu_preamp.sch`

Two connectors, and they are at opposite ends of the capsule PCB.

### H2, power — Eagle package `3P-2MM-TH`, library `CYCFI_Con`

Three pads at −2 / 0 / +2 mm, 0.75 mm drill, so 2.00 mm pitch.

| Pin | Net | Why |
| --- | --- | --- |
| 1 | `N$19` | Goes to `D1.A`. `D1` is a `D_SCHOTTKY` whose cathode is `VCC1`, so **pin 1 is V+ and the capsule protects itself against reverse polarity**. |
| 2 | `GND` | |
| 3 | `GND` | Both, not one. |

### H1, signal — Eagle package `2P-2MM-TH`, library `CYCFI_Con`

Two pads at −1 / +1 mm, 0.75 mm drill.

| Pin | Net | Why |
| --- | --- | --- |
| 1 | `N$1` | `C3.2` and `R2.2`. `C3` is 10 µF from `U1.OUT` (a TLV170), `R2` is 10 k to ground. So **pin 1 is the coupled output**. |
| 2 | `GND` | |

### The capsule decouples itself

    VCC1 : C1.1, C2.2, D1.C, R13.2, R15.2, R7.1, R8.2, R9.2, U1.V+
    GND  : C1.2, C2.1, ...

`C1` is `0.1uF` and `C2` is `4.7uF`, both across `VCC1`/`GND`, on the capsule.
This is the whole reason the hub carries no components.

## The breakout — `internal_breakout/internal_breakout.sch`

### J3 — silk `NU MULTI INPUT 1`, Eagle package `2X5`, library `headers(2mm)`

Pads at x ∈ {−4, −2, 0, 2, 4} and y ∈ {−1, +1}, 0.75 mm drill: **2.00 mm
pitch on both axes, numbered in pairs across the two rows.**

| Pin | Net | | Pin | Net |
| --- | --- | --- | --- | --- |
| 1 | CH7 | | 2 | CH8 |
| 3 | CH5 | | 4 | CH6 |
| 5 | CH3 | | 6 | CH4 |
| 7 | CH1 | | 8 | CH2 |
| 9 | V+ | | 10 | GND |

Three things follow, and all three shaped the hub:

**CH7 and CH8 are shared with J4.** The extracted nets are

    CH7 : J10.8, J15.3, J17.3, J3.1, J4.7
    CH8 : J10.7, J16.3, J17.1, J3.2, J4.8

so J3 pins 1–2 are the same two nets as J4 pins 7–8 — the second Nu Multi
input. Driving them from the hub would contend with anything plugged in there.

**J3 is on the underside.** Its Eagle placement is `rot="MR270"`; the `MR`
prefix is a mirrored element, which in Eagle means the bottom layer. So are
J4, J10 and J11. Electrically irrelevant, but it is why the two ends of the
cable do not look alike once they are in the instrument.

**V+ is not a fixed rail.** `J14` is a 3-pin header silkscreened `PWR SELECT`:

    VCC   : ... J13.3, J14.1, U1.ON/OFF, U1.VIN     (unregulated in)
    V+    : J1.1, J14.2, J15.1, ... J3.9, J4.9      (what J3 pin 9 carries)
    +10VA : C2.1, C3.1, C5.1, C6.1, J12.3, J14.3, U1.VOUT   (LP2985 out)

Whatever that jumper selects is what arrives at the hub, and the hub passes it
straight to six capsules. The board does not care; the capsules and the person
setting the jumper do.

### J4 — silk `NU MULTI INPUT 2`

Same package, carrying CH7–CH14, with pins 7–8 overlapping J3's pins 1–2 as
above. The hub does not use it. A second hub on J4 would give channels 9–14
and would need its own pin map, since J4's numbering is not J3's.

## Reproducing this

The tables above came from parsing the Eagle XML directly:

```bash
git clone --depth 1 https://github.com/cycfi/nu.git
python3 - <<'EOF'
import xml.etree.ElementTree as ET
for f in ['nu/nu_capsule/nu_preamp.sch',
          'nu/internal_breakout/internal_breakout.sch']:
    root = ET.parse(f).getroot()
    print(f)
    for net in root.find('.//sheets/sheet').findall('.//nets/net'):
        pins = sorted(f"{r.get('part')}.{r.get('pin')}"
                      for s in net.findall('segment')
                      for r in s.findall('pinref'))
        print(f"  {net.get('name'):8} : {', '.join(pins)}")
EOF
```

Swap `nets/net` for `elements/element` in the `.brd` files to get the
placements and rotations, and `packages/package` for the pad geometry.
