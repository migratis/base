#!/usr/bin/env python3
"""
Generate the Migratis brand asset set from a single geometric source.

The mark is an ascending, asymmetric ``M`` — two chevrons in migration
formation, the leading one flying higher than the one it follows.  The
wordmark is a custom monoline geometric lowercase built on the same
construction (one stroke weight, circular bowls, round terminals), so mark
and wordmark share a single drawing language.

Everything is expressed as stroke centrelines; nothing depends on a font
being installed.  Run this file to rewrite every SVG in this directory:

    python3 frontend/src/img/brand/build_brand.py

Raster exports (frontend/src/img/logo.png, frontend/public/favicon.*) are
produced by export_raster.sh, which rasterises these SVGs.
"""

import os

OUT = os.path.dirname(os.path.abspath(__file__))

# ── Palette ───────────────────────────────────────────────────────────────────
INK = '#141413'      # $color-dark
CREAM = '#faf9f5'    # $color-light
ORANGE = '#d97757'   # $color-orange / $color-primary

# ── The mark ──────────────────────────────────────────────────────────────────
# Drawn in a 64x64 box.  Optical bounds: x 3.75-60.25, y 9.25-54.75.
MARK_PATH = 'M8,50.5 L20,25.5 L31,42.5 L43,13.5 L56,42.5'
MARK_W = 8.5
MARK_BOX = 64

# ── The wordmark ──────────────────────────────────────────────────────────────
# Baseline y=56, x-height top y=16, ascender y=4, descender to y=69.5.
# Bowls are true circles of the x-height diameter (r=20).  Stroke 8.
WORD_W = 8
DOT_R = 4

# "migratis" — drawn in ink (or whatever colour the variant asks for).
WORD_STROKES = [
    # m — stem, semicircular arch, stem, arch, stem
    'M0,56 L0,31 A15,15 0 0 1 30,31 L30,56',
    'M30,31 A15,15 0 0 1 60,31 L60,56',
    # i
    'M78,56 L78,16',
    # g — bowl + descender with a left-sweeping tail
    'M134,36 A20,20 0 1 1 94,36 A20,20 0 1 1 134,36',
    'M134,16 L134,58 C134,66 127,71 118,69.5',
    # r — stem + quarter shoulder
    'M150,56 L150,16',
    'M150,30 C150,21.5 156.5,16 166,16',
    # a — bowl + full-height right stem
    'M212,36 A20,20 0 1 1 172,36 A20,20 0 1 1 212,36',
    'M212,16 L212,56',
    # t — crossbar + stem with a short right tail
    'M225,16 L252,16',
    'M239,4 L239,50 C239,55.5 243,58 248.5,56.5',
    # i
    'M266,56 L266,16',
    # s — double curve on the x-height circle
    ('M310,23 C310,18 304,16 295,16 C286,16 280,20 280,26 '
     'C280,32 286,36 295,36 C304,36 310,40 310,46 '
     'C310,52 304,56 295,56 C286,56 280,54 280,49'),
]
WORD_DOTS = [(78, 4), (266, 4)]

# ".ai" — the suffix, normally set in the accent colour.
SUFFIX_STROKES = [
    'M378,36 A20,20 0 1 1 338,36 A20,20 0 1 1 378,36',
    'M378,16 L378,56',
    'M396,56 L396,16',
]
SUFFIX_DOTS = [(328, 56), (396, 4)]

WORD_LEFT, WORD_RIGHT = -4.0, 400.0   # optical extents including stroke
WORD_TOP, WORD_BOTTOM = 0.0, 73.5

# ── Lockup metrics ────────────────────────────────────────────────────────────
# The mark is scaled so its optical height fills the wordmark's ascender-to-
# baseline band (y 0 to 60) and is centred on it, so the two sit as equals.
LOCK_SCALE = 1.35
LOCK_TY = 30 - 32 * LOCK_SCALE          # centre on the ascender/baseline band
LOCK_TX = -3.75 * LOCK_SCALE            # flush the mark's optical left to 0
MARK_RIGHT = 60.25 * LOCK_SCALE + LOCK_TX
GAP = 32                                # clear space between mark and wordmark
WORD_TX = MARK_RIGHT + GAP - WORD_LEFT
LOCK_TOP = 9.25 * LOCK_SCALE + LOCK_TY  # topmost ink in the lockup

HEADER = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="{vb}" '
          'width="{w}" height="{h}" fill="none" role="img" '
          'aria-label="{label}">\n')
STROKE_ATTRS = ('fill="none" stroke="{c}" stroke-width="{sw}" '
                'stroke-linecap="round" stroke-linejoin="round"')


def _strokes(paths, colour, width, indent='  '):
    out = [f'{indent}<g {STROKE_ATTRS.format(c=colour, sw=width)}>']
    out += [f'{indent}  <path d="{d}"/>' for d in paths]
    out.append(f'{indent}</g>')
    return out


def _dots(dots, colour, indent='  '):
    if not dots:
        return []
    out = [f'{indent}<g fill="{colour}">']
    out += [f'{indent}  <circle cx="{x}" cy="{y}" r="{DOT_R}"/>' for x, y in dots]
    out.append(f'{indent}</g>')
    return out


def mark_svg(colour, box=MARK_BOX, badge=None, radius=14):
    """The mark alone, optionally set on a rounded-square badge."""
    body = []
    if badge:
        body.append(f'  <rect width="{box}" height="{box}" rx="{radius}" fill="{badge}"/>')
    body += _strokes([MARK_PATH], colour, MARK_W)
    return (HEADER.format(vb=f'0 0 {box} {box}', w=box, h=box,
                          label='Migratis') + '\n'.join(body) + '\n</svg>\n')


def wordmark_svg(word_colour, suffix_colour):
    vb = f'{WORD_LEFT} {WORD_TOP} {WORD_RIGHT - WORD_LEFT} {WORD_BOTTOM - WORD_TOP}'
    body = _strokes(WORD_STROKES, word_colour, WORD_W)
    body += _dots(WORD_DOTS, word_colour)
    body += _strokes(SUFFIX_STROKES, suffix_colour, WORD_W)
    body += _dots(SUFFIX_DOTS, suffix_colour)
    return (HEADER.format(vb=vb, w=round(WORD_RIGHT - WORD_LEFT),
                          h=round(WORD_BOTTOM - WORD_TOP), label='migratis.ai')
            + '\n'.join(body) + '\n</svg>\n')


def lockup_svg(mark_colour, word_colour, suffix_colour):
    """Horizontal lockup: mark, clear space, wordmark."""
    width = WORD_TX + WORD_RIGHT
    body = [f'  <g transform="translate({LOCK_TX:.2f},{LOCK_TY:.2f}) '
            f'scale({LOCK_SCALE})">']
    body += _strokes([MARK_PATH], mark_colour, MARK_W, indent='    ')
    body.append('  </g>')
    body.append(f'  <g transform="translate({WORD_TX:.2f},0)">')
    body += _strokes(WORD_STROKES, word_colour, WORD_W, indent='    ')
    body += _dots(WORD_DOTS, word_colour, indent='    ')
    body += _strokes(SUFFIX_STROKES, suffix_colour, WORD_W, indent='    ')
    body += _dots(SUFFIX_DOTS, suffix_colour, indent='    ')
    body.append('  </g>')
    top = min(0.0, LOCK_TOP)
    return (HEADER.format(vb=f'0 {top:.0f} {width:.0f} {WORD_BOTTOM - top:.0f}',
                          w=round(width), h=round(WORD_BOTTOM - top),
                          label='migratis.ai') + '\n'.join(body) + '\n</svg>\n')


def stacked_svg(mark_colour, word_colour, suffix_colour):
    """Vertical lockup: mark centred above the wordmark."""
    scale = 1.9
    mark_w = 56.5 * scale
    width = WORD_RIGHT - WORD_LEFT
    mark_tx = (width / 2) - (mark_w / 2) - 3.75 * scale
    gap = 34
    word_ty = 54.75 * scale + gap        # mark's optical baseline + clear space
    height = word_ty + WORD_BOTTOM
    body = [f'  <g transform="translate({mark_tx:.2f},0) scale({scale})">']
    body += _strokes([MARK_PATH], mark_colour, MARK_W, indent='    ')
    body.append('  </g>')
    body.append(f'  <g transform="translate({-WORD_LEFT:.2f},{word_ty:.2f})">')
    body += _strokes(WORD_STROKES, word_colour, WORD_W, indent='    ')
    body += _dots(WORD_DOTS, word_colour, indent='    ')
    body += _strokes(SUFFIX_STROKES, suffix_colour, WORD_W, indent='    ')
    body += _dots(SUFFIX_DOTS, suffix_colour, indent='    ')
    body.append('  </g>')
    return (HEADER.format(vb=f'0 0 {width:.0f} {height:.0f}', w=round(width),
                          h=round(height), label='migratis.ai')
            + '\n'.join(body) + '\n</svg>\n')


FILES = {
    # ── Mark ──────────────────────────────────────────────────────────────────
    # Accent-orange mark on transparency: the universal one — legible on both
    # the cream page background and the ink sidebar.
    'mark.svg':            lambda: mark_svg(ORANGE),
    'mark-ink.svg':        lambda: mark_svg(INK),
    'mark-cream.svg':      lambda: mark_svg(CREAM),
    # Badge: ink tile + cream mark, for light surfaces and app icons.
    'badge.svg':           lambda: mark_svg(CREAM, badge=INK),
    'badge-accent.svg':    lambda: mark_svg(CREAM, badge=ORANGE),

    # ── Wordmark ──────────────────────────────────────────────────────────────
    'wordmark.svg':        lambda: wordmark_svg(INK, ORANGE),
    'wordmark-light.svg':  lambda: wordmark_svg(CREAM, ORANGE),
    'wordmark-mono-ink.svg':   lambda: wordmark_svg(INK, INK),
    'wordmark-mono-cream.svg': lambda: wordmark_svg(CREAM, CREAM),

    # ── Horizontal lockup (primary logo) ──────────────────────────────────────
    'logo.svg':            lambda: lockup_svg(ORANGE, INK, ORANGE),
    'logo-light.svg':      lambda: lockup_svg(ORANGE, CREAM, ORANGE),
    'logo-mono-ink.svg':   lambda: lockup_svg(INK, INK, INK),
    'logo-mono-cream.svg': lambda: lockup_svg(CREAM, CREAM, CREAM),

    # ── Stacked lockup ────────────────────────────────────────────────────────
    'logo-stacked.svg':       lambda: stacked_svg(ORANGE, INK, ORANGE),
    'logo-stacked-light.svg': lambda: stacked_svg(ORANGE, CREAM, ORANGE),
}


def main():
    for name, build in FILES.items():
        path = os.path.join(OUT, name)
        with open(path, 'w') as fh:
            fh.write(build())
        print(f'wrote {name}')


if __name__ == '__main__':
    main()
