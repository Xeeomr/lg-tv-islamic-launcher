# Clean Your TV — B1 identity

Approved direction: B1, an asymmetric house with a flowing orange roof.
The project lockup reads **clean your tv / FOR LG webOS**.

## Masters

- `logo-light.svg`, `logo-dark.svg`: horizontal signature, including compatibility subtitle.
- `logo-stacked-light.svg`, `logo-stacked-dark.svg`: vertically arranged signature.
- `symbol-color.svg`, `symbol-reversed.svg`: standalone house for light/dark backgrounds.
- `symbol-black.svg`, `symbol-white.svg`: true single-colour house marks.
- `wordmark.svg`: custom lettering only, converted from the approved study into smoothed vector contours.
- `readme-logo.png`, `readme-logo-dark.png`: transparent README headers for light/dark themes.
- `downloads/*.svg`: linked README download cards with locally drawn Windows window, Apple, Linux penguin (Tux) and Android robot platform identifiers. Cream/muted brown vectors retain the quiet charcoal card styling; labels identify the Windows GUI ZIP and Android ARM64 preview APK. These platform identifiers are separate from the project’s B1 house identity.
- `brand-overview.svg`, `brand-overview.png`: identity and application-family preview.

Identity SVG masters contain vector paths, no raster images, filters, external fonts or live text. Download cards use live system-font labels for legibility and local vector platform symbols; they make no external asset requests.
The subtitle and Root R were outlined from Outfit (SIL OFL; see `../../launcher/fonts/OFL.txt`).
The principal lettering preserves the custom forms from the approved generated study.

## Palette

| Role | HEX | RGB |
| --- | --- | --- |
| Warm dark brown | #241D19 | 36, 29, 25 |
| Orange roof/accent | #FF4C20 | 255, 76, 32 |
| Cream | #FFF8EB | 255, 248, 235 |

Use cream/brown for text; orange is an identifying accent rather than small body text.
The `FOR LG webOS` line describes compatibility; no LG corporate symbol is used.

## Usage

Keep at least 24 units of clear space around the 256-unit symbol. Do not stretch,
rotate, outline, add effects, or independently rearrange parts of the signature.
Use the provided reversed variant on dark backgrounds. Use the symbol alone below
360 px horizontal signature width; keep standalone symbols at least 16 px.
The 80/130 px TV tiles use their own generous internal padding.
README uses standard Markdown image syntax with GitHub's `#gh-light-mode-only`
and `#gh-dark-mode-only` fragments. GitHub displays the matching transparent
image for its active theme. Brown lettering is used on light backgrounds and
cream lettering on dark backgrounds; neither image has an opaque backing.

Root and No-root tiles share the same symbols without letter badges. Application titles identify the edition.
Helper is the directional pad with orange centre; Updater is the paired rotating arrow.
Installer uses the project Home symbol. See `../icons/README.md` for package mappings.

## Validation

Inspected the signature on cream and dark brown and the house at 16/32/80/130 px.
Inspected the complete application family and smaller menu previews.
SVG audits identify expected complexity in custom lettering and tiny subtitle
components: the full signature is for headers, while the standalone symbol is the
small-size artwork. This is a visual reference check, not trademark clearance.

## Installer interfaces

Android, desktop and console CYTV share this approved identity. Keep the house mark and app icons in their original B1 colours. Installer working surfaces are quiet warm charcoal with cream text, muted brown-grey controls and restrained borders; do not use bright orange button fills or large cream panels. Orange remains a small identifying accent. Terminal output keeps the user’s default background and respects `NO_COLOR` and redirected plain-text output.

No-root and Root have equal standing. Labels describe Developer Mode or existing root SSH requirements, without recommendation badges or promotional ranking. A connection-derived current choice is a convenience, not a compatibility guarantee.
