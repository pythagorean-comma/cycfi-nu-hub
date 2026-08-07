# Making the cables

Thirteen cables connect six Nu capsules to the hub, and the hub to the
Internal Breakout. None of them is difficult. One of them — the capsule power
cable — has a way of going wrong that shorts the supply, and it is the exact
mistake that Cycfi's own cable guide will lead you into if you follow it
literally. That is [warning 1](#1-position-1-is-not-ground) below, and it is
the reason this document exists rather than a link.

Read Cycfi's guide for **technique**:
<https://www.cycfi.com/how-to-make-and-repair-pin-header-cables/>. It is
better than anything written here on how to actually hold the tool. Read this
for **which wire goes where**.

---

## What you are building

| # | Cable | Ends | Positions used | Qty |
| --- | --- | --- | --- | --- |
| 1 | Capsule power | 3-way ↔ 3-way | 3 of 3 | 6 |
| 2 | Capsule signal | 2-way ↔ 2-way | 2 of 2 | 6 |
| 3 | Hub → breakout | 2×5 ↔ 2×5 | **8 of 10** | 1 |

Two cables per capsule and not one, because the capsule has two connectors: a
3-pin power header at one end of its PCB and a 2-pin signal header at the
other. The hub mirrors that — `P1`–`P6` along its south edge, `S1`–`S6` along
its north edge, same channel in the same column.

> **If you are building the `direct` variant**, cables 1 and 2 below are
> unchanged — twelve capsule cables, same parts, same tables. Cable 3 does not
> exist: there is no hub → breakout run, because there is no breakout. The
> hub's `J10` and `J11` present the same two 2×5 headers the breakout does, so
> the instrument's existing 19-pin jack loom plugs straight into it.
>
> Two differences that matter at the bench. **Pin 1 is the north pad on every
> header** on that board, not the west one — the headers are turned 90° to make
> it small. And **check the loom's orientation before powering anything**: a
> reversed J10 shorts the capsule outputs to ground, which is not the harmless
> failure [Two positions on the 2×5 stay
> empty](#2-two-positions-on-the-2x5-stay-empty) describes below.

---

## Two warnings before you buy anything

### 1. Position 1 is not ground

Cycfi's guide says:

> "Make sure you insert all GND wires (black) into position 1, indicated by a
> small molded triangle in the crimp housing"

**That is for a different cable. Do not do it here.** On the Nu capsule's own
connectors, read out of Cycfi's Eagle schematic:

| Capsule connector | Position 1 is |
| --- | --- |
| H2, 3-pin power | **V+**, through a Schottky diode on the capsule |
| H1, 2-pin signal | **OUT**, through the 10 µF coupling capacitor |

Ground is on positions 2 and 3 of the power header, and position 2 of the
signal header. The hub mirrors the capsule exactly, so the same is true at
both ends of every capsule cable.

Get this backwards on a power cable and you connect the supply rail to the
capsule's ground: the Schottky blocks the reverse feed so the capsule never
powers up, and V+ sits shorted to ground through the capsule's ground pour.
The breakout's regulator will current-limit or shut down. Nothing here is
subtle enough to survive by luck — **check the triangle against the tables
below before you insert a single contact.**

The molded-triangle convention itself is right and worth using: the triangle
marks position 1 on the housing. On the hub, **position 1 is always the
west-most pad**, which is printed on the silkscreen.

### 2. Two positions on the 2×5 stay empty

Positions **1 and 2** of the hub → breakout cable are not crimped, at either
end. They are the breakout's CH7 and CH8, and those two nets are shared with
J4 pins 7–8 — the second Nu Multi input. Filling them would contend with
anything plugged in there.

Leaving them empty is also what makes a reversed cable harmless: a 2×5
rotated in its own plane maps position *n* to position 11 − *n*, so the two
empty positions land on V+ and GND and the hub receives no supply at all.
A backwards cable is a dead cable, not a dead capsule.

---

## Tools

| Tool | Notes |
| --- | --- |
| **Engineer PA-09 crimping pliers** | Cycfi's choice, and the right one. Four dies: 1.0 / 1.4 / 1.6 / 1.9 mm. [Amazon](https://www.amazon.com/ENGINEER-AWG32-AWG20-Connectors-Oil-Resistant-PA-09/dp/B002AVVO7K) · [The Pi Hut](https://thepihut.com/products/universal-micro-crimping-pliers-1-0-to-1-9mm-size-contacts) · [TME](https://www.tme.com/us/en-us/details/fut.pa-09/crimping-tools-for-terminals/engineer/pa-09/) |
| Wire strippers | Something that will do 28–30 AWG cleanly |
| Flush cutters | |
| Fine tweezers | For inserting contacts and for extraction during repair |
| **Multimeter with continuity beep** | Not optional. See [Verify](#verify-before-you-plug-anything-in). |
| Heat gun or lighter | |

**On the die size.** Cycfi write *"Use the 1/4″ cavity size for the 2 mm crimp
terminals."* The PA-09 has no 1/4-inch die — its four dies are metric, marked
1.0, 1.4, 1.6 and 1.9 mm — so read that as the **1.4 mm** die. Do not take my
word for it either: crimp one contact, look at it under magnification, and
pull on the wire hard. The wire should not come out and the insulation grip
should be closed on the jacket, not on bare conductor. Adjust a die size
either way if it is not right. You will make 76 of these; spend the first
three getting the setting right.

If you go the Hirose DF11 route for the 2×5 (below), Hirose's own hand tool is
[DF11-TA2428HC](https://www.newark.com/hirose-hrs/df11-ta2428hc/hand-crimp-tool-28-24awg-skt-contact/dp/49P5012).
It is far more expensive than the PA-09 and only worth it if you are making
these regularly.

---

## Parts

### Single-row housings and contacts — capsule cables

These are Hirose's 2.00 mm single-row crimp system, the same parts Cycfi
specify in their guide.

| Part | What | Qty needed | Where |
| --- | --- | --- | --- |
| **A4B-3S-2C** | 3-way housing, 2.00 mm | 12 | [DigiKey H2012-ND](https://www.digikey.com/en/products/detail/hirose-electric-co-ltd/A4B-3S-2C/141219) · [RS 7644761](https://uk.rs-online.com/web/p/wire-housings-plugs/7644761) |
| **A4B-2S-2C** | 2-way housing, 2.00 mm | 12 | [DigiKey 141216](https://www.digikey.com/en/products/detail/hirose-electric-co-ltd/A4B-2S-2C/141216) · [Mouser](https://www.mouser.com/ProductDetail/Hirose-Connector/A4B-2S-2C) |
| **A3B-2630SCC** | Crimp socket, gold, 26–30 AWG | 60 → **buy 90** | [Mouser](https://www.mouser.com/ProductDetail/Hirose-Connector/A3B-2630SCC) |

Twelve of each housing, not six: every cable has one at each end.

### The 2×5 — the one part I could not verify

**Both ends of this cable are the same interface, and that is deliberate.** The
hub's `J1` and the breakout's `J3` are both plain, unshrouded 2×5 headers on a
2.00 mm grid with 0.5 mm square posts — Cycfi's is the `2X5` package from their
`headers(2mm)` Eagle library, the hub's is KiCad's
`PinHeader_2x05_P2.00mm_Vertical`. The PCB hole sizes differ slightly, 0.75 mm
against 0.80 mm, but that is the board, not the pin: the same commodity header
strip fits both, and both number their pins in pairs across the rows, which is
what lets the cable be wired one-to-one.

Three consequences, and they are the whole reason to keep it that way:

- **One test-fit qualifies both ends.** Whatever you prove on the hub is
  equally true of the breakout, because it is the same part.
- **Whichever housing wins is used at both ends.** One housing, one contact,
  one crimp setting for the trunk, and the two ends are interchangeable.
- **If the first choice fails, nothing is stranded** except the sample. Swap
  routes and you are still symmetric.

It is tempting to fix this by fitting a keyed, shrouded connector at the hub —
a Hirose `DF11-10DP-2DSA` in place of the plain header. Don't. It buys
certainty about the end that was never in doubt, still leaves the breakout end
to be tested, and pays for it by making the cable asymmetric and committing
the hub to one connector family for good. The retention it adds is
half a fix that a cable tie does properly at both ends for nothing.

What you need, then, is a 10-way (2×5) socket housing that fits bare 0.5 mm
square posts. **I could not confirm a specific part for this from the
manufacturers' documentation, and I am not going to pretend otherwise.** Two
routes, and whichever you pick, **buy one housing and a few contacts first and
test-fit them on the hub** — that sample decides the whole trunk, so it is
worth having in your hand before the rest of the order goes in. Test on the
hub rather than the breakout: same interface, and you are not levering an
unproven connector onto Cycfi's board.

| Route | Parts | Trade-off |
| --- | --- | --- |
| **Hirose DF11** | [DF11-10DS-2C](https://www.futureelectronics.com/p/interconnect--pin-and-socket-connectors--socket-plug-wire-mount/df11-10ds-2c-hirose-electric-4329116) housing + [DF11-2428SCA](https://www.digikey.com/en/products/detail/hirose-electric-co-ltd/df11-2428sca/150215) contacts, 24–28 AWG gold | Better made, and there is real precedent: Cycfi's own guide puts Hirose **A4B** housings on the capsule's H1/H2, which are *generic* 2 mm headers — so a Hirose 2 mm socket is known to mate with a bare 2 mm post. Against it: that precedent is single-row, where A4B has no shroud in the first place. DF11's socket is designed against Hirose's own shrouded header, and I never found the post cross-section that decides it. Different contact from the capsule cables, so a second crimp setting. |
| **Generic 2.00 mm "Dupont"** | 2×5 10-way 2.0 mm socket housing + 2.0 mm crimp terminals | Explicitly made for bare square-post headers, so fit is correct *by design* rather than by luck — this is the technically conservative choice, not the cheap one. Cycfi's own guide calls these "2 mm Dupont" parts. Variable quality; buy from a supplier you have used before. |

A third possibility if you want **one contact type for the entire build**: two
`A4B-5S-2C` five-way housings side by side. The A4B housing body is 2.0 mm
wide and the row pitch is 2.0 mm, so two of them abutted should land on both
rows, and you would use A3B-2630SCC throughout. I have not tested this and the
housings would need bonding together — treat it as an experiment, not a plan.

#### Qualifying the sample

Ten minutes, and it settles the whole trunk. Two of these failure modes pass a
plain continuity check, which is why the wiggle and the re-insertion count
matter more than the beep.

1. Push the **bare housing, no contacts** onto `J1`. It should seat fully and
   square without forcing.
2. Crimp one contact, insert it, check continuity — then **press the cable
   sideways.** Intermittence here is the answer on its own.
3. Mate and unmate **ten times**, then check retention again. If it has gone
   slack, the contact beams are taking a permanent set: the connector works on
   the bench and degrades in the instrument.
4. Pull that contact back out and look at the beams under magnification.
   Splayed or flattened is a fail.
5. Confirm the moulded position-1 triangle lands on the pin you expect. A
   female housing seen from its mating face numbers the *mirror* of the male
   header seen from above, and this is where people get it backwards.

If it passes but retention feels marginal, that is a cable tie or a dab of
hot-melt at each end, not a different connector.

### Wire

Cycfi use 28–30 AWG shielded and link
[UL2547 28 AWG multi-core shielded on AliExpress](https://www.aliexpress.com/w/wholesale-UL2547-28AWG-shielded-cable.html).
Same family here:

| Cable | Stock | Why |
| --- | --- | --- |
| Capsule power ×6 | **2-core + shield, 28 AWG** | Red core = V+, black core = GND, shield = the *second* ground. See below. |
| Capsule signal ×6 | **1-core + shield, 28 AWG** | Core = OUT, shield = GND. A screened core is exactly right for an audio run. 2-core + shield works too — leave one core cut back. |
| Hub → breakout ×1 | **8-core + shield, 28 AWG** | 6 channels + V+ + GND on the cores; the shield lands on the hub's `E1` pad. |

If 8-core is hard to source, two 4-core shielded cables run side by side do the
same job.

Measure the runs in the instrument before cutting, then add 20%. A cable that
is 10 mm short is scrap.

### Heat-shrink

Cycfi's sizes, and they are the right ones:

- **3/64″ or 1/16″** — over each twisted shield tail, before crimping
- **1/8″** — over the cable jacket where it enters the housing

### Colour convention

Cycfi's, extended for the trunk:

| Colour | Net |
| --- | --- |
| Red | V+ |
| Black | GND |
| White | Signal (single-channel cables) |
| 6 distinct colours | CH1…CH6 in the hub → breakout cable |

Write down which trunk colour is which channel **before** you crimp, and keep
that note with the instrument. Channel order is not recoverable by looking at
the finished cable.

---

## Cable 1 — capsule power, ×6

3-way at both ends. Both ends are wired **identically**: position 1 to
position 1, and so on. Nothing crosses.

| Position | Net | Conductor | Capsule (H2) | Hub (`P1`–`P6`) |
| --- | --- | --- | --- | --- |
| **1** | **V+** | red core | V+ via Schottky | pin 1, west-most |
| 2 | GND | black core | GND | pin 2 |
| 3 | GND | **shield** | GND | pin 3 |

The capsule commits two of its three power positions to ground, so carry both.
Cycfi's trick is what makes this easy with a 2-core-plus-shield cable: split
the shield braid into two halves and twist each into its own tail. Here you
only need one shield tail per end — the black core covers position 2 and the
shield covers position 3.

Two independent ground conductors is not belt-and-braces for its own sake: it
halves the return resistance and it fills the housing, which is worth as much
for retention as it is electrically.

## Cable 2 — capsule signal, ×6

2-way at both ends, wired straight through.

| Position | Net | Conductor | Capsule (H1) | Hub (`S1`–`S6`) |
| --- | --- | --- | --- | --- |
| **1** | **OUT** | white core | output via 10 µF cap | pin 1, west-most |
| 2 | GND | shield | GND | pin 2 |

Keep these six cables away from the power bundle where you can. It costs
nothing to route them along opposite sides of the cavity, and the hub is laid
out so the two bundles leave on opposite edges for exactly that reason.

## Cable 3 — hub → breakout, ×1

2×5 at both ends, **8 of 10 positions crimped**, wired straight through:
position *n* to position *n*.

| Position | Net | Conductor | | Position | Net | Conductor |
| --- | --- | --- | --- | --- | --- | --- |
| **1** | *CH7* | **empty** | | **2** | *CH8* | **empty** |
| 3 | CH5 | colour 5 | | 4 | CH6 | colour 6 |
| 5 | CH3 | colour 3 | | 6 | CH4 | colour 4 |
| 7 | CH1 | colour 1 | | 8 | CH2 | colour 2 |
| 9 | **V+** | red | | 10 | **GND** | black |

Note the channel order: the pairs run CH7/CH8, CH5/CH6, CH3/CH4, CH1/CH2 —
**descending**, with CH1 nearest the supply end. That is Cycfi's numbering, not
a mistake, and it is why the hub places CH1 furthest from its own connector.

**The shield does not go in the housing.** Solder it to the hub's `E1` pad and
leave it unconnected at the breakout end. Grounding a screen at one end only
is what stops it becoming a second ground path in parallel with position 10.
`E1` is the 2.0 mm square pad on the west edge, silkscreened SHIELD / GND;
it is on GND and it will take the shield tail and a cavity-foil wire together.

---

## Crimping

Cycfi's procedure, which works:

1. **Strip.** Hold the unstripped wire against the contact to judge the strip
   length. The contact has two pairs of tabs — the inner pair grips bare
   conductor, the outer pair grips the jacket. Both should close on the right
   thing.
2. **Prepare shield tails.** Gather the braid to one side, twist it tight, and
   slide 3/64″ or 1/16″ heat-shrink over it, leaving bare wire proud for the
   crimp. An untwisted shield tail will splay out inside the housing and short
   to its neighbour.
3. **Crimp**, 1.4 mm die (see above). Conductor tabs first, then jacket tabs.
4. **Pull-test every one.** A firm tug on the wire. Discard anything that
   moves — this is why you bought 50% spares.
5. **Insert** into the housing until it clicks. Tug the wire again: a properly
   seated contact will not back out.
6. **Check against the table** for that cable, using the molded triangle as
   position 1, *before* you heat-shrink anything.
7. **Sleeve** the jacket entry with 1/8″ heat-shrink, protruding slightly into
   the wires so the bundle cannot flex right at the housing.

---

## Verify before you plug anything in

Every one of these takes under a minute and one of them will eventually save
you six capsules. Do all of them.

### Step 1 — each cable, on the bench, nothing connected

- **Continuity, position *n* to position *n*** at the two ends. All of them.
- **No continuity between any two adjacent positions.** This is the one that
  catches a splayed shield tail or a whisker.
- On the trunk cable, confirm **positions 1 and 2 are empty at both ends** and
  that nothing beeps to them.

### Step 2 — the hub, before power

With the trunk cable plugged into the hub but **not** into the breakout:

- **V+ to GND at the far end of the trunk: must be open.** If this beeps, stop
  — something is shorted and it will land straight across the breakout's
  regulator.
- Position 9 at the breakout end to pin 1 of every `P1`–`P6` on the hub:
  should beep, all six.
- Position 10 to pin 2 and pin 3 of every `P` header, and pin 2 of every `S`
  header: should beep.
- Position 7 to `S1` pin 1 (CH1). Position 8 to `S2` pin 1. Then check the
  other four against the table above.

### Step 3 — power, with no capsules connected

Plug the trunk into the breakout. Power the breakout **with the capsule cables
unplugged** and measure V+ to GND at each of `P1`–`P6` on the hub.

All six should read the breakout's Nu Multi rail. On the v2.6.1 breakout that
pin is silkscreened **10V**; on the published v2.5 sources it is a net called
V+ fed from the `PWR SELECT` jumper (`J14`), which chooses between the
unregulated input and the LP2985 output. Whichever your board does, **confirm
the number is what you expect before six capsules see it.**

### Step 4 — one capsule

Connect a single capsule, power up, confirm it works, then do the rest. If
something is wrong with your understanding of the pinout, it is much better to
find out with one capsule connected than six.

---

## Repair

Contacts can be removed and reused. Cycfi's method:

1. Use tweezers to bend the plastic crimp lock in the housing slightly
   outward. Gently — it snaps off if you overdo it.
2. Push the contact out from the mating face until you can pull it clear.
3. Press the lock lightly back to its original position.

To extend a wire that has broken too short to re-crimp: strip both the stub
and a length of 26–28 AWG, twist and solder the joint, cover it with
heat-shrink, then measure, strip and crimp as usual.

---

## Where these numbers came from

The capsule pinouts and the breakout J3 pinout were read out of Cycfi's Eagle
sources at a recorded commit — see [`cycfi-sources.md`](cycfi-sources.md)
for the extraction and [`DESIGN.md`](DESIGN.md) for what the board does with
them. `design.py` asserts the hub's pin map against those tables at import, so
the tables in this document and the copper on the board cannot disagree
without the build failing.

The one thing not derived from a file is which physical end of the breakout's
`J3` is position 1. Cycfi's v2.6.1 datasheet shows the two rows as
`Ch8 Ch6 Ch4 Ch2 Gnd` and `Ch7 Ch5 Ch3 Ch1 10v`, which pairs exactly as the
v2.5 sources do — but a printed pin map does not tell you which way round the
connector sits on your board. That is what Step 2 above is for.
