#!/usr/bin/env bash
#
# Renders this deployment's legal documents (docs/legal/*.html) to the PDFs the
# frontend links to (frontend/src/documents/*.pdf).
#
# The HTML files are the editable source — never patch the PDFs directly.
#
# WHAT SHIPS HERE IS A PLACEHOLDER. The template cannot write your terms of sale
# or your privacy policy: they state who is selling, under what liability,
# before which court, who the data controller is and how a person exercises
# their rights — none of which can be guessed from the software. The pages this
# renders say exactly that, in the four languages the template ships, and they
# are linked from the footer and from the registration form. Replacing them is
# part of putting an application into service.
#
# Migratis' own terms and privacy policy live at https://migratis.ai and apply
# to migratis.ai alone. They are deliberately NOT copied here: a byte-copy would
# have this deployment publishing another company's binding documents as its
# own, which is why migratis' sync hook skips both this directory and
# common/components/Footer.js.
#
# Usage:  bash docs/legal/build.sh
#
# LibreOffice is confined to $HOME when installed as a snap, so both the source
# and the output have to live under the user's home directory (the repo does).

set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUT="$(cd "$HERE/../../frontend/src/documents" && pwd)"

SOFFICE="$(command -v soffice || echo /snap/bin/libreoffice)"

for src in "$HERE"/cguv_*.html "$HERE"/rgpd_*.html; do
  name="$(basename "$src" .html)"
  echo "→ $name.pdf"
  "$SOFFICE" --headless --convert-to pdf --outdir "$OUT" "$src" >/dev/null
done

echo "Done — PDFs written to $OUT"
