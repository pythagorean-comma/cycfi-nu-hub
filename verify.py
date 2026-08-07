"""Read the generated schematic back through KiCad and compare it to design.py.

The schematic is drawn from geometry -- wires meeting at coordinates -- so a
misplaced endpoint would silently produce a different circuit. This exports
KiCad's own netlist and checks that the connectivity it found is exactly the
connectivity design.py asked for, net by net.

On a board that is only a pin map, that check is most of the design review.
The rest is here too: that the board still points at the schematic, that the
string order on the copper is the one design.py declares, that the design
rules on disk are the ones the layout was drawn to, and that fab/ORDER.md is
still describing the board that was just built.
"""

import json
import pathlib
import re
import subprocess
import sys

import design as circuit
import gen_project
import kicad
import rules
import sexp

KICAD_CLI = kicad.KICAD_CLI


def export_netlist(schematic, destination):
    result = subprocess.run(
        [str(KICAD_CLI), "sch", "export", "netlist", "--format", "kicadsexpr",
         "-o", str(destination), str(schematic)],
        capture_output=True, text=True)
    if result.returncode != 0 or not destination.exists():
        raise SystemExit(f"netlist export failed:\n{result.stdout}\n{result.stderr}")
    return destination


def read_netlist(path):
    """net name -> set of (ref, pin), ignoring drawing-only power symbols."""
    tree = sexp.parse(path.read_text())
    found = {}
    for net in sexp.find_all(sexp.find(tree, "nets"), "net"):
        name = sexp.find(net, "name")[1]
        nodes = set()
        for node in sexp.find_all(net, "node"):
            ref = sexp.find(node, "ref")[1]
            pin = sexp.find(node, "pin")[1]
            if ref.startswith("#"):
                continue        # power symbols and flags name nets, they are not parts
            nodes.add((ref, str(pin)))
        found[name] = nodes
    return found


def compare(actual, expected):
    """Compare as partitions; report differences in both directions."""
    problems = []

    actual_by_nodes = {frozenset(nodes): name for name, nodes in actual.items() if nodes}
    expected_by_nodes = {frozenset(nodes): name for name, nodes in expected.items()}

    for nodes, name in expected_by_nodes.items():
        if nodes not in actual_by_nodes:
            # Find whatever the schematic did with these pins instead.
            landed = {}
            for pin in sorted(nodes):
                for actual_name, actual_nodes in actual.items():
                    if pin in actual_nodes:
                        landed.setdefault(actual_name, []).append(pin)
                        break
                else:
                    landed.setdefault("<nowhere>", []).append(pin)
            detail = "; ".join(f"{k}: {sorted(v)}" for k, v in landed.items())
            problems.append(f"net {name} not formed as drawn -> {detail}")

    for nodes, name in actual_by_nodes.items():
        if nodes not in expected_by_nodes and not name.startswith("unconnected-"):
            problems.append(f"unexpected net {name} = {sorted(nodes)}")

    # An unconnected pin is an error by default -- that is how a wire that
    # missed its target gets caught. design.NO_CONNECT lists the pins that are
    # supposed to float, so the exception is declared alongside the circuit
    # rather than hidden in here.
    for name in sorted(actual):
        if not name.startswith("unconnected-"):
            continue
        pins = actual[name]
        if pins and pins <= set(circuit.NO_CONNECT):
            continue
        problems.append(f"unconnected pin: {name}")

    # Names should line up too, for the nets the design names explicitly.
    for nodes, name in expected_by_nodes.items():
        actual_name = actual_by_nodes.get(nodes)
        if actual_name and actual_name != name and not actual_name.startswith("Net-"):
            problems.append(f"net {name} is called {actual_name} in the schematic")

    return problems


def _reference(node):
    for prop in sexp.find_all(node, "property"):
        if prop[1] == "Reference":
            return prop[2]
    return None


def _property(node, name):
    for prop in sexp.find_all(node, "property"):
        if prop[1] == name:
            return prop[2]
    return None


def read_schematic_symbols(path):
    """reference -> (uuid, value), for the first unit of each placed symbol."""
    tree = sexp.parse(path.read_text())
    found = {}
    for symbol in sexp.find_all(tree, "symbol"):
        unit = sexp.find(symbol, "unit")
        uuid_node = sexp.find(symbol, "uuid")
        reference = _reference(symbol)
        if unit is None or uuid_node is None or reference is None:
            continue
        if int(str(unit[1])) == 1 and not reference.startswith("#"):
            found[reference] = (uuid_node[1], _property(symbol, "Value"))
    return found


def read_board_footprints(path):
    """reference -> (schematic path, footprint identifier, (x, y))."""
    tree = sexp.parse(path.read_text())
    found = {}
    for footprint in sexp.find_all(tree, "footprint"):
        reference = _reference(footprint)
        if reference is None:
            continue
        path_node = sexp.find(footprint, "path")
        at = sexp.find(footprint, "at")
        found[reference] = (path_node[1] if path_node else None,
                            str(footprint[1]),
                            (float(at[1]), float(at[2])) if at else None)
    return found


def check_string_order(board):
    """The six channels must run in string order across the copper.

    design.STRINGS says channel 1 is the low E and the columns run low to
    high from the west end. That is a decision about the instrument, not
    about the circuit, so nothing electrical would notice it being wrong:
    the netlist would still match, ERC and DRC would still pass, and the
    first sign of trouble would be six strings coming out of the wrong
    outputs.
    """
    footprints = read_board_footprints(board)
    problems = []
    for prefix, what in (("S", "signal"), ("P", "power")):
        columns = []
        for channel in range(1, circuit.CHANNELS + 1):
            entry = footprints.get(f"{prefix}{channel}")
            if entry is None or entry[2] is None:
                problems.append(f"{prefix}{channel} is not on the board")
                break
            columns.append((channel, entry[2][0]))
        else:
            if [x for _, x in columns] != sorted(x for _, x in columns):
                problems.append(
                    f"the {what} headers are not in string order west to "
                    f"east: {columns} -- design.STRINGS says CH1 is "
                    f"{circuit.STRINGS[1]}")
    return problems


def check_annotations(schematic, board):
    """The cable warning must appear on both the sheet and the silkscreen.

    Both are generated from design.SILK_NOTE, so they cannot drift on their
    own -- but this is the one sentence that stops somebody crimping the two
    unused positions, and the schematic PDF and the bare board are the two
    places a person will read it. This catches an annotation edited by hand,
    leaving the constant behind.
    """
    problems = []
    for name, path in (("schematic", schematic), ("board", board)):
        if circuit.BOARD_NOTE not in path.read_text():
            problems.append(f"{name} does not carry the board's warning "
                            f"{circuit.BOARD_NOTE!r}")
    if circuit.CYCFI_SOURCE not in schematic.read_text():
        problems.append("the schematic does not say which Cycfi sources the "
                        "pin map came from")
    return problems


def check_project_rules(project):
    """The .kicad_pro on disk must still carry the rules gen_project.py wrote.

    DRC enforces whatever is in this file, and this file is the one artefact
    in the project that something other than the build writes: opening the
    project in the KiCad GUI rewrites it in KiCad's own expanded form,
    dropping `netclass_patterns` and resetting the constraint floors to
    KiCad's defaults. A build regenerates the file first, so the DRC in a
    build is always correct; this catches a project file edited out from
    under the geometry, before anyone trusts a DRC run made against it.
    """
    intent = gen_project.project_document("")["board"]["design_settings"]
    intent_nets = gen_project.project_document("")["net_settings"]
    try:
        actual = json.loads(project.read_text())
    except (OSError, ValueError) as error:
        return [f"cannot read {project.name}: {error}"]

    problems = []
    settings = actual.get("board", {}).get("design_settings", {})
    for name, wanted in sorted(intent["rules"].items()):
        found = settings.get("rules", {}).get(name)
        if found != wanted:
            problems.append(f"{project.name}: rule {name} is {found}, "
                            f"gen_project.py says {wanted}")

    nets = actual.get("net_settings", {})
    classes = {c["name"]: c for c in nets.get("classes", [])}
    for wanted in intent_nets["classes"]:
        found = classes.get(wanted["name"])
        if found is None:
            problems.append(f"{project.name}: net class {wanted['name']!r} is "
                            f"missing -- DRC would fall back to Default")
            continue
        for key in ("track_width", "clearance", "via_diameter", "via_drill"):
            if found.get(key) != wanted[key]:
                problems.append(
                    f"{project.name}: {wanted['name']}.{key} is "
                    f"{found.get(key)}, gen_project.py says {wanted[key]}")

    wanted_patterns = {(p["netclass"], p["pattern"])
                       for p in intent_nets["netclass_patterns"]}
    found_patterns = {(p.get("netclass"), p.get("pattern"))
                      for p in nets.get("netclass_patterns") or []}
    for netclass, pattern in sorted(wanted_patterns - found_patterns):
        problems.append(f"{project.name}: {pattern!r} is not assigned to "
                        f"{netclass!r} -- that rail is being checked as Default")

    return problems


def board_figures(board):
    """The numbers fab/ORDER.md quotes, read back off the built board.

    Parsed with sexp rather than pcbnew, because verify.py runs under plain
    python3 and only gen_pcb.py gets KiCad's bundled interpreter. Everything
    needed is in the board file as text.
    """
    tree = sexp.parse(board.read_text())

    copper = [layer for layer in sexp.find(tree, "layers")[1:]
              if str(layer[1]).endswith(".Cu")]

    xs, ys = [], []
    for line in sexp.find_all(tree, "gr_line"):
        for end in ("start", "end"):
            corner = sexp.find(line, end)
            xs.append(float(corner[1]))
            ys.append(float(corner[2]))

    vias = list(sexp.find_all(tree, "via"))
    via_drills = {float(sexp.find(v, "drill")[1]) for v in vias}

    # Holes by drill, and plated separately from not. The mounting holes are
    # the only unplated ones and the fab needs to be told so; everything else
    # is a pad the cable or a via depends on.
    plated, unplated = {}, {}
    footprints = list(sexp.find_all(tree, "footprint"))
    for footprint in footprints:
        for pad in sexp.find_all(footprint, "pad"):
            kinds = {str(item) for item in pad[:4]}
            drill = sexp.find(pad, "drill")
            if drill is None:
                continue
            size = float(drill[1])
            table = unplated if "np_thru_hole" in kinds else plated
            table[size] = table.get(size, 0) + 1

    return {
        "layers": len(copper),
        "width": round(max(xs) - min(xs), 1),
        "height": round(max(ys) - min(ys), 1),
        "vias": len(vias),
        "via_drill": via_drills.pop() if len(via_drills) == 1 else None,
        "header_holes": plated.get(0.8, 0),
        "pad_holes": plated.get(1.0, 0),
        "plated": sum(plated.values()) + len(vias),
        "unplated": sum(unplated.values()),
        "unplated_drill": (set(unplated).pop() if len(unplated) == 1 else None),
        "placements": len(footprints),
    }


def check_mechanical(board, interface):
    """The mechanical interface file must still describe the built board.

    This file is the whole reason the enclosure can live in a separate
    repository: it carries the outline, the hole centres and every part
    position across the boundary as data. If it drifts, an enclosure is
    modelled to a board that no longer exists, and nothing finds out until
    a printed part will not accept a PCB.

    Positions are re-derived from the .kicad_pcb here rather than trusted,
    because gen_pcb.py writes both files and a single wrong assumption would
    otherwise agree with itself.
    """
    try:
        stated = json.loads(interface.read_text())
    except (OSError, ValueError) as error:
        return [f"cannot read {interface.name}: {error} -- the enclosure has "
                f"nothing to build against"]

    problems = []
    tree = sexp.parse(board.read_text())
    figures = board_figures(board)

    if stated.get("schema") != "cycfi-nu-hub/mechanical":
        problems.append(f"{interface.name}: not a mechanical interface file")
        return problems

    # -- the outline and the stackup ------------------------------------
    outline = stated.get("board", {})
    for key, actual in (("width", figures["width"]),
                        ("height", figures["height"])):
        if round(float(outline.get(key, -1)), 1) != actual:
            problems.append(f"{interface.name}: board {key} says "
                            f"{outline.get(key)}, the board is {actual}")
    general = sexp.find(tree, "general")
    thickness = sexp.find(general, "thickness") if general else None
    if thickness is not None and float(thickness[1]) != outline.get("thickness"):
        problems.append(f"{interface.name}: thickness says "
                        f"{outline.get('thickness')}, the board says "
                        f"{thickness[1]}")

    # -- every placement, against the footprint it claims to describe ---
    placed = read_board_footprints(board)
    declared = {p["ref"]: p for p in stated.get("parts", [])}
    declared.update({h["ref"]: h for h in stated.get("mounting_holes", [])})

    for ref in sorted(set(placed) - set(declared)):
        problems.append(f"{interface.name}: {ref} is on the board but not in "
                        f"the interface -- the enclosure would not know it is "
                        f"there")
    for ref in sorted(set(declared) - set(placed)):
        problems.append(f"{interface.name}: {ref} is in the interface but not "
                        f"on the board")

    for ref in sorted(set(placed) & set(declared)):
        actual = placed[ref][2]
        entry = declared[ref]
        if actual is None:
            continue
        if (round(entry.get("x", -1), 3), round(entry.get("y", -1), 3)) != \
                (round(actual[0], 3), round(actual[1], 3)):
            problems.append(
                f"{interface.name}: {ref} at ({entry.get('x')}, "
                f"{entry.get('y')}), the board has it at {actual}")

    # -- bodies must be sane: containing their own origin, inside the board
    width, height = figures["width"], figures["height"]
    for ref, entry in sorted(declared.items()):
        box = entry.get("body")
        if box is None:
            continue
        if not (box["x_min"] <= entry["x"] <= box["x_max"]
                and box["y_min"] <= entry["y"] <= box["y_max"]):
            problems.append(f"{interface.name}: {ref}'s body does not contain "
                            f"its own origin")
        if (box["x_min"] < 0 or box["y_min"] < 0
                or box["x_max"] > width or box["y_max"] > height):
            problems.append(f"{interface.name}: {ref}'s body {box} falls "
                            f"outside the {width} x {height} outline")

    # The axis convention is the one field a modeller cannot check by eye,
    # and getting it wrong mirrors the enclosure. Refuse to ship it unstated.
    axes = stated.get("axes", {})
    if "to_y_up" not in axes or "SOUTH" not in axes.get("y", ""):
        problems.append(f"{interface.name}: the y-axis convention is not "
                        f"stated -- that is how an enclosure comes out "
                        f"mirrored")

    return problems


def check_order_figures(board, order):
    """fab/ORDER.md must still be describing the board that was just built.

    ORDER.md carries a dozen numbers that are all derivable -- the board size,
    the layer count, every design rule, the hole counts. They are written by
    hand, because the prose around them is worth more than a generated table,
    and build.sh copies this file into the fabrication zip. A stale figure is
    a wrong number in front of the contractor, in the one document whose whole
    job is to carry what the gerbers cannot.

    So the numbers are asserted rather than generated: write the prose freely,
    and the build refuses to package a board the document no longer describes.
    """
    text = order.read_text()
    figures = board_figures(board)
    problems = []

    def show(values):
        return " / ".join(f"{v:g}" for v in values)

    def compare_figure(pattern, what, *expected):
        found = re.search(pattern, text)
        if found is None:
            problems.append(f"{order.name}: cannot find the {what} figure -- "
                            f"the wording moved, so this check stopped "
                            f"checking it")
            return
        actual = tuple(float(g) for g in found.groups())
        if actual != tuple(float(e) for e in expected):
            problems.append(
                f"{order.name}: {what} says {show(actual)}, "
                f"the board says {show(float(e) for e in expected)}")

    compare_figure(r"\| \*\*Layers\*\* \| \*\*(\d+)\b", "layer count",
                   figures["layers"])
    compare_figure(r"\| \*\*Board size\*\* \| \*\*([\d.]+) × ([\d.]+) mm",
                   "board size", figures["width"], figures["height"])
    compare_figure(r"(\d+) header holes at ([\d.]+) mm", "header hole count",
                   figures["header_holes"], 0.8)
    compare_figure(r"(\d+) pad hole at ([\d.]+) mm", "grounding pad hole",
                   figures["pad_holes"], 1.0)
    compare_figure(r"(\d+) vias at ([\d.]+) mm", "via count",
                   figures["vias"], figures["via_drill"])
    compare_figure(r"(\d+) plated holes in total", "plated hole total",
                   figures["plated"])
    compare_figure(r"(\d+) unplated holes at ([\d.]+) mm", "unplated holes",
                   figures["unplated"], figures["unplated_drill"])
    # Just the count. It used to also require the words "all through-hole",
    # which was true of the only board that existed then and is not true of
    # the direct variant's two 0805 parts.
    compare_figure(r"\*\*(\d+) placements\*\*",
                   "placement count", figures["placements"])

    # The design rules come from rules.py, which gen_project.py writes into
    # the .kicad_pro for DRC to enforce -- so this closes the loop from the
    # rule, through the checker, to what the fab is told.
    for pattern, what, expected in (
            (r"\| Min track width \| ([\d.]+) mm", "min track width", rules.TRACK),
            (r"\| Power track width \| ([\d.]+) mm", "power track width",
             rules.POWER_TRACK),
            (r"\| Min clearance \| ([\d.]+) mm", "min clearance", rules.CLEARANCE),
            (r"\| Min drill \| ([\d.]+) mm", "min drill", rules.VIA_DRILL),
            (r"\| Min annular ring \| ([\d.]+) mm", "min annular ring",
             rules.ANNULAR_RING),
            (r"\| Board edge clearance \| ([\d.]+) mm", "board edge clearance",
             rules.MIN_COPPER_EDGE_CLEARANCE)):
        compare_figure(pattern, what, expected)
    compare_figure(r"\| Via pad / drill \| ([\d.]+) / ([\d.]+) mm",
                   "via pad / drill", rules.VIA_DIAMETER, rules.VIA_DRILL)

    return problems


def check_board_linkage(schematic, board):
    """Every footprint must point at its schematic symbol and name its library.

    Without the path KiCad cannot associate the two, so cross-probing dies and
    'Update PCB from Schematic' offers to add every footprint again as a new
    part. Without the library prefix it cannot update a footprint from its
    library. Both are silent -- nothing else in the build would notice.
    """
    symbols = read_schematic_symbols(schematic)
    footprints = read_board_footprints(board)
    problems = []

    # Values are set in three places -- design.py, the schematic and the BOM
    # that KiCad derives from it -- so check the drawing still agrees with the
    # design. A stale literal here is invisible until it reaches a BOM.
    for reference, (_, value) in sorted(symbols.items()):
        wanted = circuit.PARTS[reference].value
        if value != wanted:
            problems.append(f"{reference}: schematic says {value!r}, "
                            f"design.py says {wanted!r}")

    for reference, (path, identifier, _) in sorted(footprints.items()):
        expected = symbols.get(reference)
        if expected is None:
            problems.append(f"{reference}: on the board but not the schematic")
        elif path != f"/{expected[0]}":
            problems.append(f"{reference}: path {path} does not match "
                            f"schematic symbol /{expected[0]}")
        if ":" not in identifier:
            problems.append(f"{reference}: footprint {identifier!r} has no library")

    for reference in sorted(set(symbols) - set(footprints)):
        if not circuit.PARTS[reference].footprint:
            continue        # power flags are schematic-only, by design
        problems.append(f"{reference}: in the schematic but not on the board")

    return problems, len(footprints)


def main():
    here = pathlib.Path(__file__).parent
    schematic = here / circuit.PROJECT / f"{circuit.PROJECT}.kicad_sch"
    netlist = here / "build" / "verify.net"
    netlist.parent.mkdir(parents=True, exist_ok=True)

    export_netlist(schematic, netlist)
    actual = read_netlist(netlist)
    expected = {name: {n for n in nodes if not n[0].startswith("#")}
                for name, nodes in circuit.NETS.items()}

    problems = compare(actual, expected)
    if problems:
        print(f"{len(problems)} problem(s):")
        for problem in problems[:60]:
            print(f"  - {problem}")
        if len(problems) > 60:
            print(f"  ... and {len(problems) - 60} more")
        return 1

    print(f"schematic matches design.py: {len(expected)} nets, "
          f"{sum(len(v) for v in expected.values())} pin connections")

    board = here / circuit.PROJECT / f"{circuit.PROJECT}.kicad_pcb"
    if not board.exists():
        print("board not generated yet; skipping linkage check")
        return 0
    problems, count = check_board_linkage(schematic, board)
    problems += check_string_order(board)
    problems += check_annotations(schematic, board)
    problems += check_project_rules(
        here / circuit.PROJECT / f"{circuit.PROJECT}.kicad_pro")
    # Each board gets its own ORDER.md, because the figures in it are asserted
    # against the board and no two of them agree.
    order = ("ORDER.md" if circuit.VARIANT == "breakout"
             else f"ORDER-{circuit.VARIANT}.md")
    problems += check_order_figures(board, here / "fab" / order)
    problems += check_mechanical(
        board, here / "fab" / f"{circuit.PROJECT}-mechanical.json")
    if problems:
        print(f"{len(problems)} board problem(s):")
        for problem in problems[:20]:
            print(f"  - {problem}")
        return 1
    print(f"board linked to schematic: {count} footprints")
    print(f"channels in string order: CH1 = {circuit.STRINGS[1]} at the west "
          f"end, CH{circuit.CHANNELS} = {circuit.STRINGS[circuit.CHANNELS]}")
    print(f"design rules intact: {gen_project.TRACK_WIDTH}mm signal, "
          f"{gen_project.POWER_TRACK_WIDTH}mm power, "
          f"{gen_project.VIA_DIAMETER}/{gen_project.VIA_DRILL}mm vias, "
          f"{gen_project.CLEARANCE}mm clearance")
    figures = board_figures(board)
    print(f"fab/{order} still describes this board: "
          f"{figures['width']} x {figures['height']}mm, "
          f"{figures['layers']} layers, {figures['placements']} placements, "
          f"{figures['plated']} plated and {figures['unplated']} unplated holes")
    print(f"mechanical interface matches: {figures['placements']} placements "
          f"and {len(circuit.MOUNTING_HOLES)} holes, in a stated axis "
          f"convention")
    return 0


if __name__ == "__main__":
    sys.exit(main())
