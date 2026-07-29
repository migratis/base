#!/usr/bin/env bash
#
# Rasterise the Migratis brand SVGs into the PNG/ICO assets the app ships.
#
#   bash frontend/src/img/brand/export_raster.sh
#
# Sources are the SVGs in this directory (regenerate them with build_brand.py
# first if the geometry changed).  Outputs:
#
#   frontend/src/img/logo.png            512px mark, transparent  (MenuLeft/Header)
#   frontend/public/favicon.svg          the mark, for modern browsers
#   frontend/public/favicon.ico          16/32/48/64 badge, for legacy browsers
#   frontend/public/apple-touch-icon.png 180px badge on the ink tile
#   frontend/public/logo192.png          192px badge  (PWA manifest)
#   frontend/public/logo512.png          512px badge  (PWA manifest)
#
set -euo pipefail

BRAND="$(cd "$(dirname "$0")" && pwd)"
IMG="$(cd "$BRAND/.." && pwd)"
PUBLIC="$(cd "$BRAND/../../../public" && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

# Rasterise <svg> <out.png> <size> — transparent background, square canvas.
raster() {
  local svg="$1" out="$2" size="$3"
  cat > "$TMP/page.html" <<EOF
<!doctype html><meta charset="utf-8">
<style>html,body{margin:0;padding:0;background:transparent}
img{display:block;width:${size}px;height:${size}px}</style>
<img src="file://$svg">
EOF
  google-chrome --headless=new --disable-gpu --no-sandbox --hide-scrollbars \
    --default-background-color=00000000 \
    --user-data-dir="$TMP/profile" \
    --window-size="${size},${size}" \
    --screenshot="$out" "file://$TMP/page.html" >/dev/null 2>&1
}

raster "$BRAND/mark.svg"  "$IMG/logo.png"                 512
raster "$BRAND/badge.svg" "$PUBLIC/apple-touch-icon.png"  180
raster "$BRAND/badge.svg" "$PUBLIC/logo192.png"           192
raster "$BRAND/badge.svg" "$PUBLIC/logo512.png"           512

cp "$BRAND/mark.svg" "$PUBLIC/favicon.svg"

for s in 16 32 48 64; do raster "$BRAND/badge.svg" "$TMP/ico-$s.png" "$s"; done
# Pack the ICO by hand so every size is a true render of the SVG at that size
# rather than a downscale of one bitmap.  Entries embed the PNGs verbatim,
# which every browser since IE9 reads.
python3 - "$TMP" "$PUBLIC/favicon.ico" <<'PY'
import struct, sys

tmp, out = sys.argv[1], sys.argv[2]
sizes = [16, 32, 48, 64]
blobs = [open(f'{tmp}/ico-{s}.png', 'rb').read() for s in sizes]

header = struct.pack('<HHH', 0, 1, len(sizes))
offset = len(header) + 16 * len(sizes)
entries, payload = b'', b''
for size, blob in zip(sizes, blobs):
    entries += struct.pack('<BBBBHHII', size % 256, size % 256, 0, 0,
                           1, 32, len(blob), offset)
    payload += blob
    offset += len(blob)

with open(out, 'wb') as fh:
    fh.write(header + entries + payload)
PY

echo "brand raster export complete"
