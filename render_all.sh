#!/bin/bash
# Render all four VF1 scenes in parallel, as MP4 and/or GIF.
#
# Usage:
#   bash render_all.sh [quality] [format]
#   quality : l (low, default), m (medium), h (high)
#   format  : mp4 (default), gif, both
#
# Examples:
#   bash render_all.sh          # low-quality MP4
#   bash render_all.sh l gif    # low-quality GIF
#   bash render_all.sh h both   # high-quality MP4 + GIF

QUALITY=${1:-l}
FORMAT=${2:-mp4}
SCRIPT="vf1_polyhedron.py"
SCENES=(VF1Polyhedron VF1Convergence VF1HalfSpace VF1VaryNM)

cd "$(dirname "$0")"

run_scene() {
    local scene=$1
    local fmt=$2
    local log="render_${scene}_${fmt}.log"
    if [ "$fmt" = "gif" ]; then
        manim -q"$QUALITY" --format gif "$SCRIPT" "$scene" >"$log" 2>&1
    else
        manim -q"$QUALITY" "$SCRIPT" "$scene" >"$log" 2>&1
    fi
    echo $?
}

launch() {
    local fmt=$1
    echo "Rendering ${#SCENES[@]} scenes as $(echo "$fmt" | tr '[:lower:]' '[:upper:]') at quality=${QUALITY}..."
    local pids=()
    for scene in "${SCENES[@]}"; do
        run_scene "$scene" "$fmt" &
        pids+=($!)
        echo "  started $scene ($fmt, pid=${pids[-1]})"
    done

    local failed=()
    for i in "${!SCENES[@]}"; do
        wait "${pids[$i]}"
        if [ $? -ne 0 ]; then
            failed+=("${SCENES[$i]}")
            echo "  FAILED  ${SCENES[$i]} ($fmt) — see render_${SCENES[$i]}_${fmt}.log"
        else
            echo "  done    ${SCENES[$i]} ($fmt)"
        fi
    done

    if [ ${#failed[@]} -ne 0 ]; then
        echo "Failed: ${failed[*]}"
        return 1
    fi
}

case "$FORMAT" in
    both)
        launch mp4 && launch gif
        ;;
    gif|mp4)
        launch "$FORMAT"
        ;;
    *)
        echo "Unknown format '$FORMAT'. Use mp4, gif, or both."
        exit 1
        ;;
esac

echo ""
echo "Done. Output in: media/videos/vf1_polyhedron/"
