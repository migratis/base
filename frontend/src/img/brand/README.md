# migratis.ai — brand assets

The mark is an ascending, asymmetric **M**: two chevrons in migration formation,
the leading one flying higher than the one it follows. It is one unbroken
polyline through five points on a 64-unit grid, stroke 8.5, round caps and
joins. The wordmark is a custom geometric monoline lowercase drawn as outlines —
it depends on no installed font. Colours are the tokens already declared in
`common/styles/_variables.scss`: ink `#141413`, cream `#faf9f5`, terracotta
`#d97757`.

## Regenerating

All geometry lives once, in `build_brand.py`. Nothing in this directory should
be hand-edited — change a coordinate in the script and re-run it:

```bash
python3 frontend/src/img/brand/build_brand.py   # rewrites every SVG here
bash   frontend/src/img/brand/export_raster.sh  # re-cuts the PNG/ICO exports
```

`export_raster.sh` rasterises via headless Chrome and packs the ICO with
Pillow; it writes outside this directory, to `../logo.png` and
`../../../public/`.

## What is where

| File | Use |
|------|-----|
| `logo.svg` | Primary horizontal lockup. Also `-light` (on ink), `-mono-ink`, `-mono-cream` |
| `logo-stacked.svg` | Vertical lockup, for narrow columns and square crops. Also `-light` |
| `wordmark.svg` | Wordmark alone. Also `-light`, `-mono-ink`, `-mono-cream` |
| `mark.svg` | The mark, terracotta on transparency — **this is the one the app imports** |
| `mark-ink.svg`, `mark-cream.svg` | Single-colour cuts of the mark |
| `badge.svg`, `badge-accent.svg` | The mark on a rounded tile, for icons below 32px |

Generated outside this directory:

| File | Use |
|------|-----|
| `../logo.png` | 512px mark, transparent — fallback raster |
| `../../../public/favicon.svg` | Tab icon for modern browsers |
| `../../../public/favicon.ico` | Tab icon, packs 16/32/48/64 |
| `../../../public/apple-touch-icon.png` | 180px, iOS home screen |
| `../../../public/logo192.png`, `logo512.png` | PWA manifest icons |

## Rules

- Terracotta `mark.svg` is legible on both the cream page and the ink sidebar,
  so it needs no light/dark pair. Use it as the default.
- Clear space on all four sides of a lockup equals the wordmark's x-height —
  the height of the `m`.
- Minimum size for the full lockup is 120px wide; below that use the mark alone.
  Below 32px prefer `badge.svg`.
- Do not recolour outside the four palette tokens, add shadows or gradients, or
  scale either axis independently.
- Do not put the mark on an ink tile when it already sits on a dark surface.
