# Application icons

The SVG files are the editable sources for the approved B1 identity.
All tiles share a 256-unit grid, a rounded dark brown (#241D19) container,
cream (#FFF8EB) foreground and orange (#FF4C20) accents. Home uses the
asymmetric flowing-roof house, Helper uses the directional keypad, and
Updater uses paired rotating arrows. Root variants use the same symbols without letter badges; the edition is shown in the application title.
See [brand masters and guidelines](../brand/README.md).

| Source | Display name | Packaged PNG files |
| --- | --- | --- |
| home.svg | Home | launcher/brand-v2-icon.png (80), launcher/brand-v2-largeIcon.png (130), launcher/icon.png (80) |
| helper.svg | Home Helper | native/app/brand-v2-icon.png (80), native/app/brand-v2-largeIcon.png (130), native/app/icon.png (80) |
| updater.svg | Home Updater | updater-app/icon.png (80), updater-app/largeIcon.png (130) |
| home-root.svg | Home Root | root-edition/assets/home.png (80), home-large.png (130) |
| updater-root.svg | Root Updater | root-edition/assets/updater.png (80), updater-large.png (130) |
| installer.svg | Clean Your TV | assets/icons/installer.png (1024), installer-256.png (256), installer.ico (16/32/48/256) |

PNG dimensions are square, in pixels. Render SVGs at high resolution and
resample to each target size. With Sharp available to Node, run
`node scripts/render-app-icons.cjs` from the repository root to regenerate all PNGs.
The renderer also copies the unmodified mobile house master and generates Android launcher/monochrome notification vector resources from the same paths. Keep the PNGs checked in; TV packaging does not require an SVG renderer.
The renderer also regenerates both transparent themed README PNGs and the Windows ICO.
Root staging uses home-root-icon.png and home-root-largeIcon.png in its manifest to avoid reusing cached artwork at the old brand-v2 URLs. Root Updater likewise uses root-updater-icon.png and root-updater-largeIcon.png.
The Root application ID retains its historical `preview` suffix for upgrades;
its visible title is **Home Root**.
