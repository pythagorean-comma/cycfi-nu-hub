"""Build the PCB for the design in design.py.

Two layers, GND poured on both, and a handful of tracks -- there are only ever
eight or nine nets and almost nothing to route between.

This module is the machinery, not the geometry. Two boards are built from it
and they share no coordinates at all:

    layout_breakout   six capsules onto a Cycfi Internal Breakout, on the
                      breakout's own 50 x 35 mm outline
    layout_direct     the breakout deleted, driving the instrument's 19-pin
                      jack from a 33 x 24.5 mm board

`design.VARIANT` picks between them and load_layout() asserts the chosen module
provides the whole interface, because a layout missing one function would
otherwise fail deep inside main() with an AttributeError rather than a sentence.

What lives here is everything neither board gets to have an opinion about: the
Board wrapper over pcbnew, the rounded-rectangle outline in its three forms,
the pours, the fit and mounting-hole checks, and the mechanical export the
enclosure repository consumes.

What lives in a layout module is every number: the outline, the placements,
the routing waypoints, the silkscreen and the assertions that tie them
together. Those assertions are the point of the split -- each board's
check_placement() is written against its own rotation convention, and copying
one to the other is exactly the mistake it exists to catch.
"""

import json
import pathlib
import sys

import pcbnew

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import design as circuit  # noqa: E402
import kicad  # noqa: E402
import rules  # noqa: E402
# The schematic writer's UUID helper, so the board derives exactly the same
# symbol identifiers the schematic wrote rather than re-implementing the hash.
from kisch import _uuid as symbol_uuid  # noqa: E402

FOOTPRINT_DIR = kicad.FOOTPRINT_DIR

TRACK = rules.TRACK
POWER_TRACK = rules.POWER_TRACK
VIA_DIAMETER = rules.VIA_DIAMETER
VIA_DRILL = rules.VIA_DRILL
CLEARANCE = rules.CLEARANCE
KEEPOUT = rules.PAD_KEEPOUT

F = pcbnew.F_Cu
B = pcbnew.B_Cu


def to_mm(value):
    return pcbnew.ToMM(value)


# ---------------------------------------------------------------------------
# rounded rectangle
# ---------------------------------------------------------------------------
#
# Three views of the same shape, because three things consume it and none of
# them take the same form: Edge_Cuts wants segments and true arcs, a zone
# wants a closed polygon, and check_fits() wants to know whether a point is
# inside. Deriving all three from one (rectangle, radius) is what stops the
# pours and the outline drifting apart at the corners -- which they would do
# silently, as a sliver of copper hanging over a rounded edge.

def rounded_rectangle_segments(rectangle, radius):
    """The four straight edges, each stopping short of its corners."""
    left, top, right, bottom = rectangle
    r = radius
    return [((left + r, top), (right - r, top)),
            ((right, top + r), (right, bottom - r)),
            ((right - r, bottom), (left + r, bottom)),
            ((left, bottom - r), (left, top + r))]


def rounded_rectangle_arcs(rectangle, radius):
    """The four corners as (start, mid, end), clockwise on screen."""
    left, top, right, bottom = rectangle
    r = radius
    # How far the arc's midpoint sits in from the corner of the bounding box.
    k = r * (1 - 2 ** -0.5)
    return [((left, top + r), (left + k, top + k), (left + r, top)),
            ((right - r, top), (right - k, top + k), (right, top + r)),
            ((right, bottom - r), (right - k, bottom - k), (right - r, bottom)),
            ((left + r, bottom), (left + k, bottom - k), (left, bottom - r))]


def rounded_rectangle_polygon(rectangle, radius, steps=8):
    """The same outline as a closed polygon, for a zone.

    y is down, so the angles run clockwise on screen: a corner centred at
    (cx, cy) sweeping 180 to 270 degrees is the *top-left* one.
    """
    import math

    left, top, right, bottom = rectangle
    r = radius
    corners = (((right - r, top + r), -90, 0),
               ((right - r, bottom - r), 0, 90),
               ((left + r, bottom - r), 90, 180),
               ((left + r, top + r), 180, 270))
    points = []
    for (cx, cy), start, end in corners:
        for step in range(steps + 1):
            angle = math.radians(start + (end - start) * step / steps)
            points.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))
    return points


def point(x, y):
    return pcbnew.VECTOR2I_MM(float(x), float(y))


class Board:
    def __init__(self):
        self.board = pcbnew.BOARD()
        self.board.SetCopperLayerCount(2)
        self.nets = {}
        self.footprints = {}
        self._make_nets()

    # -- nets and parts ---------------------------------------------------
    def _make_nets(self):
        for name in sorted(circuit.NETS):
            net = pcbnew.NETINFO_ITEM(self.board, name)
            self.board.Add(net)
            self.nets[name] = net

    def net(self, name):
        return self.nets[name]

    def place(self, ref, x, y, rotation=0):
        part = circuit.PARTS[ref]
        library, name = part.footprint.split(":", 1)
        footprint = pcbnew.FootprintLoad(str(FOOTPRINT_DIR / f"{library}.pretty"), name)
        if footprint is None:
            raise SystemExit(f"could not load footprint {part.footprint} for {ref}")
        self.board.Add(footprint)
        # FootprintLoad returns the footprint under its bare name; without the
        # library nickname KiCad cannot tie it back to a library, so
        # "Update Footprints from Library" has nothing to work from.
        footprint.SetFPIDAsString(part.footprint)
        # Link back to the schematic symbol of the same reference. The UUIDs
        # are derived from the project name, so both generators compute the
        # same value independently -- this is what makes cross-probing work
        # and stops "Update PCB from Schematic" treating every footprint as
        # a new part.
        footprint.SetPath(pcbnew.KIID_PATH(
            f"/{symbol_uuid(f'{circuit.PROJECT}:part:{ref}:1')}"))
        footprint.SetSheetname("/")
        footprint.SetSheetfile(f"{circuit.PROJECT}.kicad_sch")
        footprint.SetPosition(point(x, y))
        if rotation:
            footprint.SetOrientationDegrees(rotation)
        footprint.SetReference(ref)
        footprint.SetValue(part.value)
        footprint.Reference().SetVisible(True)
        footprint.Value().SetVisible(False)
        self.footprints[ref] = footprint

        owner = circuit.DESIGN.pin_owner()
        for pad in footprint.Pads():
            key = (ref, pad.GetNumber())
            if key in owner:
                pad.SetNet(self.net(owner[key]))
        return footprint

    def pad(self, ref, number):
        """Absolute position of a pad, in millimetres."""
        for candidate in self.footprints[ref].Pads():
            if candidate.GetNumber() == str(number):
                position = candidate.GetPosition()
                return (round(to_mm(position.x), 4), round(to_mm(position.y), 4))
        raise KeyError(f"{ref} has no pad {number}")

    # -- copper -----------------------------------------------------------
    def track(self, net, points, layer=F, width=TRACK):
        for start, end in zip(points, points[1:]):
            if start == end:
                continue
            segment = pcbnew.PCB_TRACK(self.board)
            segment.SetStart(point(*start))
            segment.SetEnd(point(*end))
            segment.SetWidth(pcbnew.FromMM(width))
            segment.SetLayer(layer)
            segment.SetNet(self.net(net))
            self.board.Add(segment)

    def via(self, net, x, y):
        item = pcbnew.PCB_VIA(self.board)
        item.SetPosition(point(x, y))
        item.SetWidth(pcbnew.FromMM(VIA_DIAMETER))
        item.SetDrill(pcbnew.FromMM(VIA_DRILL))
        item.SetViaType(pcbnew.VIATYPE_THROUGH)
        item.SetLayerPair(F, B)
        item.SetNet(self.net(net))
        self.board.Add(item)

    def zone(self, net, layer, points, priority=0):
        item = pcbnew.ZONE(self.board)
        item.SetLayer(layer)
        item.SetNet(self.net(net))
        item.SetAssignedPriority(priority)
        item.SetLocalClearance(pcbnew.FromMM(CLEARANCE))
        item.SetMinThickness(pcbnew.FromMM(0.2))
        outline = item.Outline()
        outline.NewOutline()
        for x, y in points:
            outline.Append(pcbnew.FromMM(float(x)), pcbnew.FromMM(float(y)))
        self.board.Add(item)
        return item

    def outline(self, rectangle, radius):
        """Edge cuts: four segments and four corner arcs.

        The corners are rounded because the breakout's are, and a square
        corner is *more* material than a round one -- a square 50 x 35 does
        not go where a rounded 50 x 35 goes. Matching the outline and then
        leaving the corners sharp would give a board that measures right and
        will not drop into the pocket.
        """
        for start, end in rounded_rectangle_segments(rectangle, radius):
            shape = pcbnew.PCB_SHAPE(self.board)
            shape.SetShape(pcbnew.SHAPE_T_SEGMENT)
            shape.SetStart(point(*start))
            shape.SetEnd(point(*end))
            shape.SetLayer(pcbnew.Edge_Cuts)
            shape.SetWidth(pcbnew.FromMM(0.1))
            self.board.Add(shape)
        for start, middle, end in rounded_rectangle_arcs(rectangle, radius):
            shape = pcbnew.PCB_SHAPE(self.board)
            shape.SetShape(pcbnew.SHAPE_T_ARC)
            shape.SetArcGeometry(point(*start), point(*middle), point(*end))
            shape.SetLayer(pcbnew.Edge_Cuts)
            shape.SetWidth(pcbnew.FromMM(0.1))
            self.board.Add(shape)

    def reference(self, ref, x=None, y=None, size=rules.MIN_SILK_TEXT,
                  visible=True):
        """Move, resize or hide a footprint's reference designator.

        Left alone these inherit their footprint's rotation and its default
        offset, which on a strip this crowded puts half of them on top of
        their own neighbours and two of them over the board edge, where a fab
        clips them.
        """
        item = self.footprints[ref].Reference()
        item.SetVisible(visible)
        if not visible:
            return
        if x is not None:
            item.SetPosition(point(x, y))
        item.SetTextAngleDegrees(0)
        item.SetTextSize(pcbnew.VECTOR2I(pcbnew.FromMM(size), pcbnew.FromMM(size)))
        item.SetTextThickness(pcbnew.FromMM(size * 0.15))

    def text(self, body, x, y, size=1.0, layer=pcbnew.F_SilkS):
        item = pcbnew.PCB_TEXT(self.board)
        item.SetText(body)
        item.SetPosition(point(x, y))
        item.SetLayer(layer)
        item.SetTextSize(pcbnew.VECTOR2I(pcbnew.FromMM(size), pcbnew.FromMM(size)))
        item.SetTextThickness(pcbnew.FromMM(size * 0.15))
        self.board.Add(item)


def check_holes_clear(board, hole_xy, hole_drill):
    """No track or via may run into a mounting hole.

    Not ceremony on either board. On the breakout-shaped one the holes sit
    2.5 mm in from all four edges, which puts H3 in the same east margin the
    three descents run down -- CH2's lane passes 1.95 mm from its centre
    against a 1.35 mm minimum. On the small one the two holes sit *inside* the
    outline entirely, on the centreline beside the jack connectors, with the
    fan-in crossing the same band.

    Nothing else here would catch it. An unplated hole carries no pad and no
    net, so it is on no net's keepout and in no netlist; check_placement()
    runs before any copper exists; and check_fits() compares the hole's
    courtyard against the board outline, which says nothing about what is
    routed through it. A track laid straight across one would build, pass the
    netlist comparison and arrive as a board with a screw hole through a
    signal.
    """
    def distance_to_segment(px, py, ax, ay, bx, by):
        dx, dy = bx - ax, by - ay
        span = dx * dx + dy * dy
        if span == 0:
            return ((px - ax) ** 2 + (py - ay) ** 2) ** 0.5
        t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / span))
        return ((px - ax - t * dx) ** 2 + (py - ay - t * dy) ** 2) ** 0.5

    problems = []
    for ref, (hx, hy) in hole_xy.items():
        for item in board.board.GetTracks():
            half = to_mm(item.GetWidth()) / 2
            needed = hole_drill / 2 + rules.MIN_HOLE_CLEARANCE + half
            start, end = item.GetStart(), item.GetEnd()
            gap = distance_to_segment(hx, hy,
                                      to_mm(start.x), to_mm(start.y),
                                      to_mm(end.x), to_mm(end.y))
            if gap < needed:
                net = item.GetNetname() or "?"
                problems.append(
                    f"{net} passes {gap:.2f} mm from {ref} at ({hx}, {hy}); "
                    f"{needed:.2f} mm is the minimum")
    if problems:
        raise SystemExit("copper runs into a mounting hole:\n  "
                         + "\n  ".join(problems))


# ---------------------------------------------------------------------------
# copper, outline, silk
# ---------------------------------------------------------------------------

def add_copper(board, points):
    """GND poured on both layers.

    Free, on a two-layer board that is mostly air. What it buys is a return
    directly under every signal trace and a reference plane between the six
    of them -- worth little against a Nu's low-impedance output, but worth
    nothing against it either, and it costs the same to fabricate.
    """
    board.zone("GND", F, points)
    board.zone("GND", B, points)


def mechanical(board, rectangle, layout):
    """Describe the finished board for whatever has to be built around it.

    The enclosure lives in its own repository, because it needs CadQuery and
    this one deliberately needs nothing. That split is only safe if the
    dimensions cross the boundary as data rather than as numbers copied out of
    a PDF, so this writes the one file the enclosure consumes and verify.py
    checks it back against the board.

    Everything here is read off the placed footprints rather than off the
    layout module's constants. Those are what the board was asked to be; this
    is what it came out as.
    """
    left, top, right, bottom = rectangle

    def body(ref):
        """Courtyard bounding box -- the space the part actually claims."""
        box = board.footprints[ref].GetCourtyard(pcbnew.F_CrtYd).BBox()
        if box.GetWidth() == 0:
            return None
        return {"x_min": round(to_mm(box.GetLeft()), 3),
                "y_min": round(to_mm(box.GetTop()), 3),
                "x_max": round(to_mm(box.GetRight()), 3),
                "y_max": round(to_mm(box.GetBottom()), 3)}

    def placement(ref, group, note):
        footprint = board.footprints[ref]
        position = footprint.GetPosition()
        return {
            "ref": ref,
            "value": circuit.PARTS[ref].value,
            "group": group,
            "x": round(to_mm(position.x), 3),
            "y": round(to_mm(position.y), 3),
            "rotation": round(footprint.GetOrientationDegrees(), 1),
            "footprint": circuit.PARTS[ref].footprint,
            "body": body(ref),
            "note": note,
        }

    parts = layout.mechanical_parts(board, placement)

    holes = []
    for ref in circuit.MOUNTING_HOLES:
        position = board.footprints[ref].GetPosition()
        holes.append({
            "ref": ref,
            "x": round(to_mm(position.x), 3),
            "y": round(to_mm(position.y), 3),
            "drill": layout.HOLE_DRILL,
            "plated": False,
            "screw": layout.HOLE_SCREW,
            "body": body(ref),
        })

    return {
        "schema": "cycfi-nu-hub/mechanical",
        "schema_version": 1,
        "project": circuit.PROJECT,
        "generated_by": "gen_pcb.py -- do not edit; regenerate with ./build.sh",
        "units": "mm",
        # The sign of y is the classic way an enclosure comes out mirrored,
        # so it is stated rather than left to be inferred from the numbers.
        "variant": circuit.VARIANT,
        "axes": {
            "origin": "top-left corner of the board outline",
            "x": "increases east; CH1 is at the west end, CH6 at the east",
            "y": "increases SOUTH -- downward on the layout, KiCad's convention",
            "z": "increases up, out of the component side",
            "warning": "CAD tools normally put +Y up. Convert before modelling.",
            "to_y_up": "y_up = board.height - y",
        },
        "board": {
            "width": round(right - left, 3),
            "height": round(bottom - top, 3),
            "thickness": 1.6,
            "shape": "rounded rectangle",
            "corner_radius": layout.BOARD_R,
            "copper_layers": 2,
        },
        # Where the outline came from, carried across to the enclosure with
        # whatever caveat belongs to it rather than remembered separately.
        "outline_source": layout.OUTLINE_SOURCE,
        "mounting_holes": holes,
        "parts": parts,
        "component_height": {
            "known": False,
            "reason": "Header bodies are in the footprints, but the mated "
                      "crimp housing is not, and the 2x5 housing is not yet "
                      "chosen. Measure the tallest mated stack before "
                      "closing a lid over it.",
            "measure": [f"2x5 housing mated on {layout.TRUNK_REFS}",
                        "3-way housing mated on P1-P6",
                        "2-way housing mated on S1-S6",
                        "solder joints proud of the underside"],
        },
    }


def check_fits(board, rectangle, radius):
    """Nothing may stick out of the outline, corners included.

    board_extent() in the sibling project derives the outline from the parts;
    here the size is declared, because the whole point of this revision is
    that it is somebody else's size. That trade needs this check, or a part
    nudged east just quietly hangs over the edge.

    The corners count. A courtyard can sit inside the bounding rectangle on
    all four sides and still overhang a rounded corner, and on a board whose
    corners were rounded specifically so it would drop into a pocket, that is
    exactly the failure worth catching.
    """
    left, top, right, bottom = rectangle
    # A rounded rectangle is exactly the set of points within `radius` of the
    # rectangle inset by `radius`, so clamping a point into that inner
    # rectangle gives the nearest point on the shape and one comparison
    # settles both the edges and the corners.
    inner = (left + radius, top + radius, right - radius, bottom - radius)

    def overhang(px, py):
        cx = min(max(px, inner[0]), inner[2])
        cy = min(max(py, inner[1]), inner[3])
        return ((px - cx) ** 2 + (py - cy) ** 2) ** 0.5 - radius

    problems = []
    for ref, footprint in board.footprints.items():
        # The courtyard polygon, not its bounding box. The M2 mounting holes'
        # courtyards are circles that clear the board edge by 0.03 mm, and the
        # corners of a circle's bounding box are not on the circle -- testing
        # those reports all four holes as hanging 0.7 mm off a board they fit.
        courtyard = footprint.GetCourtyard(pcbnew.F_CrtYd)
        worst = None
        for index in range(courtyard.OutlineCount()):
            chain = courtyard.Outline(index)
            for vertex in range(chain.PointCount()):
                corner = chain.CPoint(vertex)
                beyond = overhang(to_mm(corner.x), to_mm(corner.y))
                if worst is None or beyond > worst[0]:
                    worst = (beyond, to_mm(corner.x), to_mm(corner.y))
        if worst is not None and worst[0] > 1e-6:
            problems.append(
                f"{ref} courtyard hangs {worst[0]:.3f} mm over the outline at "
                f"({worst[1]:.3f}, {worst[2]:.3f})")
    if problems:
        raise SystemExit("parts do not fit the board:\n  " + "\n  ".join(problems))


def load_layout():
    """The geometry module for the variant being built.

    Kept to an import rather than a registry because the two layouts share no
    numbers at all -- different outline, different rotation, different pin-1
    rule -- and the only thing they have in common is the interface below.
    """
    if circuit.VARIANT == "breakout":
        import layout_breakout as layout
    else:
        import layout_direct as layout
    for name in ("BOARD_W", "BOARD_H", "BOARD_R", "HOLE_XY", "HOLE_DRILL",
                 "HOLE_SCREW", "TRUNK_REFS", "OUTLINE_SOURCE", "place_all",
                 "check_placement", "route", "silkscreen", "designators",
                 "mechanical_parts"):
        assert hasattr(layout, name), (
            f"{layout.__name__} does not provide {name}; gen_pcb.py needs it")
    return layout


def main():
    layout = load_layout()

    board = Board()
    layout.place_all(board)
    layout.check_placement(board)
    vias = layout.route(board)
    check_holes_clear(board, layout.HOLE_XY, layout.HOLE_DRILL)

    rectangle = (0.0, 0.0, layout.BOARD_W, layout.BOARD_H)
    check_fits(board, rectangle, layout.BOARD_R)
    board.outline(rectangle, layout.BOARD_R)
    # The pours follow the rounded corners in as well. Inset as a plain
    # rectangle their corners would poke 0.02 mm outside a 1.75 mm arc -- not
    # much, but it is copper over the edge of the board, and it is the sort of
    # thing that survives review precisely because it is too small to see.
    inner = (rules.ZONE_INSET, rules.ZONE_INSET,
             layout.BOARD_W - rules.ZONE_INSET,
             layout.BOARD_H - rules.ZONE_INSET)
    add_copper(board, rounded_rectangle_polygon(
        inner, layout.BOARD_R - rules.ZONE_INSET))
    layout.silkscreen(board)
    layout.designators(board)

    here = pathlib.Path(__file__).parent
    destination = here / circuit.PROJECT / f"{circuit.PROJECT}.kicad_pcb"
    pcbnew.ZONE_FILLER(board.board).Fill(board.board.Zones())
    pcbnew.SaveBoard(str(destination), board.board)

    interface = here / "fab" / f"{circuit.PROJECT}-mechanical.json"
    interface.parent.mkdir(parents=True, exist_ok=True)
    interface.write_text(
        json.dumps(mechanical(board, rectangle, layout), indent=2) + "\n")

    print(f"wrote {destination}")
    print(f"  and {interface.name} for the enclosure")
    # "vias" and not "stitching vias": on the direct board most of them are
    # layer changes in the middle of a signal, not stitching.
    print(f"  {len(board.footprints)} footprints, {vias} vias, "
          f"{len(list(board.board.GetTracks()))} track/via items")
    print(f"  {circuit.VARIANT} board "
          f"{layout.BOARD_W:.1f} x {layout.BOARD_H:.1f} mm "
          f"= {layout.BOARD_W * layout.BOARD_H:.0f} mm2")


if __name__ == "__main__":
    main()
