#!/bin/bash
# Regenerate the whole project from design.py and check it.
#
# The schematic writer is plain Python; the board needs KiCad's own bundled
# interpreter for pcbnew, which is why the two are kept apart below.
set -euo pipefail
cd "$(dirname "$0")"

# Everything except gen_pcb.py is pure standard library -- there is no venv and
# no requirements.txt, because there is nothing to install. Any Python 3 will
# do; the only real dependency of this repository is KiCad itself.
PY="${PYTHON:-python3}"
if ! command -v "$PY" >/dev/null 2>&1; then
    echo "no '$PY' on PATH. Set PYTHON to a Python 3 interpreter." >&2
    exit 1
fi

# Where KiCad lives is decided in one place, by kicad.py. Set KICAD_APP to
# override. Doing the lookup up front means a missing install is reported
# before anything is generated, with instructions rather than a path error.
if ! "$PY" kicad.py >/dev/null 2>&1; then
    "$PY" kicad.py || true
    exit 1
fi
KICAD_PY="$("$PY" kicad.py python)"
KICAD_CLI="$("$PY" kicad.py cli)"
export KICAD10_SYMBOL_DIR="$("$PY" kicad.py symbols)"
export KICAD10_FOOTPRINT_DIR="$("$PY" kicad.py footprints)"
"$PY" -c 'import kicad,sys; w=kicad.check_version(); w and sys.stderr.write(w+"\n")'

if [ -z "$KICAD_PY" ]; then
    echo "This KiCad has no bundled Python, so pcbnew is not available to" >&2
    echo "gen_pcb.py. On Linux, install the system python3-pcbnew package" >&2
    echo "and run gen_pcb.py with the interpreter that provides it." >&2
    exit 1
fi

# Which board to build. Two exist and they share every generator; see
# design.VARIANT for what differs. Everything downstream -- the project
# directory, the fab filenames, the ORDER.md verify.py checks -- follows from
# the name design.py derives, so it is asked for rather than assumed here.
export CYCFI_HUB_VARIANT="${1:-${CYCFI_HUB_VARIANT:-breakout}}"
NAME="$("$PY" -c 'import design; print(design.PROJECT)')"
ORDER="$("$PY" -c 'import design; print("ORDER.md" if design.VARIANT == "breakout" else f"ORDER-{design.VARIANT}.md")')"
PROJECT="$NAME/$NAME"
mkdir -p build fab
echo "== $CYCFI_HUB_VARIANT ($NAME) =="

echo "== schematic and project =="
"$PY" gen_sch.py
"$PY" gen_project.py

echo "== board =="
"$KICAD_PY" gen_pcb.py 2>&1 | grep -v "assert" || true

# Again, and not redundantly. pcbnew.SaveBoard() writes the .kicad_pro too,
# through KiCad's settings manager, and what it writes is KiCad's defaults --
# no Power net class, no netclass patterns, min_track_width back to 0.20 and
# clearance back to 0.20. Run DRC without this and every rule the layout was
# drawn to has been quietly replaced by a looser one.
#
# It has to run before the board the first time as well: gen_sch.py and
# gen_pcb.py both need the library tables it writes.
#
# verify.py checks the file again after this, so if some later step learns to
# clobber it too, the build says so instead of quietly passing.
"$PY" gen_project.py >/dev/null

# After the board, not before: this checks the drawing against design.py and
# the board's footprint linkage against the drawing, so both must be current.
echo "== checking the drawing and the board against design.py =="
"$PY" verify.py

echo "== ERC / DRC =="
"$KICAD_CLI" sch erc --severity-error --severity-warning -o build/$NAME-erc.rpt "$PROJECT.kicad_sch" | tail -1
# Warnings as well as errors, and the fab gate counts both. Asking only for
# errors hid twenty-seven violations of this project's own rules: every
# silkscreen legend was under the minimum text height written into the
# .kicad_pro, and six designators overlapped their own footprint outlines.
# None of it would have scrapped a board, and all of it would have reached
# one. If a warning is ever genuinely acceptable, exclude it explicitly
# rather than by lowering what the build looks at.
"$KICAD_CLI" pcb drc --severity-error --severity-warning -o build/$NAME-drc.rpt "$PROJECT.kicad_pcb" | tail -2
DRC_ERRORS=$(grep -cE '^\[' build/$NAME-drc.rpt || true)

echo "== documentation outputs =="
"$KICAD_CLI" sch export pdf -o fab/$NAME-schematic.pdf "$PROJECT.kicad_sch" >/dev/null
"$KICAD_CLI" sch export bom --group-by Value,Footprint \
    --fields 'Reference,Value,Footprint,${QUANTITY},Description' \
    -o fab/$NAME-bom.csv "$PROJECT.kicad_sch" >/dev/null
"$KICAD_CLI" pcb export pos --format csv --units mm \
    -o fab/$NAME-pos.csv "$PROJECT.kicad_pcb" >/dev/null
# The layout asset a reviewer can actually comment on. One page per copper
# layer, each carrying the board outline and the reference designators, so
# every page is a drawing you can read on its own.
#
# Three settings here are load-bearing. --bg-color: without it KiCad paints no
# page background, so the PDF is transparent and renders on whatever the
# viewer puts behind it. --theme: left alone the colours come from the local
# PCB editor's theme, so the same board plots differently on another machine;
# "KiCad Classic" is built in and plots silkscreen dark enough to read on
# white. And not --black-and-white, which looks like the safe choice and turns
# the designators into the same ink as the pads beneath them.
"$KICAD_CLI" pcb export pdf --mode-multipage \
    --theme "KiCad Classic" --bg-color "#FFFFFF" \
    --layers F.Cu,B.Cu \
    --common-layers Edge.Cuts,F.SilkS --scale 0 \
    -o fab/$NAME-layout.pdf "$PROJECT.kicad_pcb" >/dev/null
# Decorative, and the one artefact that reads at a glance to someone who has
# not opened a CAD tool. Deliberately not --quality high: the raytracer
# samples stochastically, so it returns a different file byte for byte on
# every run even from an identical board. `basic` is reproducible to the byte.
"$KICAD_CLI" pcb render --side top --quality basic --background opaque \
    --width 2400 --height 1200 \
    -o fab/$NAME-top.png "$PROJECT.kicad_pcb" >/dev/null

# The set a fab actually gets: copper, mask, silk, outline, drill -- and
# nothing else. A blanket export also writes Fab, Courtyard and User layers,
# and F.Fab carries a second closed board outline; if CAM picks that one up
# instead of Edge.Cuts the board comes back the wrong shape.
echo "== fab package =="
if [ "$DRC_ERRORS" -ne 0 ]; then
    rm -f fab/$NAME-pcbway.zip
    echo "SKIPPED: $DRC_ERRORS DRC error(s) outstanding -- see build/$NAME-drc.rpt."
    echo "No fabrication package is written while the board has known errors."
    exit 0
fi
rm -rf "fab/$NAME-pcbway"
"$KICAD_CLI" pcb export gerbers \
    --layers F.Cu,B.Cu,F.Mask,B.Mask,F.SilkS,B.SilkS,Edge.Cuts \
    -o "fab/$NAME-pcbway/" "$PROJECT.kicad_pcb" >/dev/null
# Omitting --excellon-separate-th gives one combined PTH/NPTH file, which is
# what fabs expect; it is a bare flag, not a key=value. The four mounting
# holes are marked unplated inside it, which is the thing ORDER.md asks the
# fab not to override.
"$KICAD_CLI" pcb export drill --format excellon \
    -o "fab/$NAME-pcbway/" "$PROJECT.kicad_pcb" >/dev/null
cp "fab/$ORDER" "fab/$NAME-pcbway/"
(cd "fab/$NAME-pcbway" && zip -q -r "../$NAME-pcbway.zip" .)
echo "wrote fab/$NAME-pcbway.zip -- upload this, and see fab/$ORDER"
