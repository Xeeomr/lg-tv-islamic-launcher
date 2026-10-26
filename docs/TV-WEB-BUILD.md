# TV web compatibility build

The web frontend targets **Chromium 38**, the engine documented for webOS 3.x.
The same compiled assets run on later Chromium-based webOS engines. This is a
frontend build target, not a claim that Home Helper, input devices or firmware
services work on every TV. webOS 1.x/2.x WebKit engines are outside this target.

Source builds require Node.js **20.19+** (Node 22 is used in CI) and npm:

```sh
npm ci --ignore-scripts --no-audit --no-fund
npm run lint:compat
npm run test:compat
```

All production TV web packages pass through `scripts/tv_web_build.py`:
No-root Home, Root Home, Home Updater and Root Updater. Desktop and Android
installers embed these compiled packages. Native executables, TV Node services
and Python code retain their own runtimes. Helper JavaScript has a separate
Node-targeted build described below; other TV Node services are not transformed.
The installed cytv apps do not require Node/npm on the user's computer.

## Processing and validation

- Babel preset-env transforms modern JavaScript syntax into ES5. Acorn checks
  every emitted script against ES5, including scripts embedded in HTML.
- A bundled core-js runtime loads before application scripts and supplies missing
  ECMAScript built-ins. It is packaged locally, with licenses, without a CDN.
  It does not supply platform-specific Luna APIs or every modern browser API.
- PostCSS preset-env/Autoprefixer target the same Browserslist entry in
  `package.json`. For example, `inset` becomes physical offsets and alpha hex
  colors become compatible color notation. CSS files, `<style>` elements and
  `style` attributes all pass through this step.
- doiuse checks the **transformed** CSS. Unsupported features left after PostCSS,
  including CSS Grid and flexbox gap, fail the build. Use compatible layouts and
  margins for those cases; do not globally disable the checks. An extra value
  check rejects `overflow-wrap: anywhere`, which doiuse misses.

There are two narrow, documented allowances: original `overflow` values
(`visible`, `hidden`, `auto`, `scroll`) are accepted despite doiuse's broad
partial-support warning; an optional `prefers-reduced-motion` override has a
scoped source comment because older engines safely ignore that media query.
Newer overflow values are still rejected. The linter uses compatibility data;
it is not an exhaustive proof of browser behavior.

Scripts remain separate classic scripts so the existing globals and UMD
wrappers keep their behavior. Compatible ES5 sources keep their original bytes.
No webpack or application-module migration is needed. Build products are staged
separately; the compiler never overwrites a developer's app configuration,
inventory or icons in the source tree.

## Regression checks

`npm run test:compat` verifies syntax conversion, missing built-ins, polyfill
ordering, inline assets, rejected unsupported CSS and repeatable HTML injection.
`scripts/test.sh` runs it and the compatibility linter. CI also runs the browser
regression on the compiled Home frontend:

```sh
python3 scripts/tv_web_build.py --input launcher --output build/legacy-ui
npx playwright install chromium
BROWSER_CHANNEL=chromium TV_WEB_DIR=build/legacy-ui npm run test:legacy-ui
```

The browser test disables `inset` and selected JS APIs to reproduce issue #20.
It checks actual card hit-testing, dimensions, icon fallback, scrolling,
launch/navigation and full-screen dialogs. This models the reported engine
limitations in a current browser; it is not an emulator of an entire old TV.
Hardware confirmation is still required on the original webOS 3.5 device.

## Helper Node compatibility

`scripts/helper_build.py` and `scripts/compile-helper.cjs` target **Node 0.12**
independently of Browserslist. Both `build-cytv.py` and `build.sh` compile the
Helper app and its status/inventory service, including vendored JS. Every
emitted `.js` file passes an ES5 parse check. Babel always runs, including on
sources that parse as ES5: strict block function declarations still fail in
Node 0.12 without transformation. Each top-level module loads local
core-js and safe-buffer before importing application dependencies. The original
Buffer constructor is preserved; only missing safe Buffer methods are added.
A Node 0.x shim also forwards callback arguments through `process.nextTick`.

`websocket.js` selects ws 6.2.4 below Node 10 and ws 8.21.0 on newer TV Node.
The legacy tree includes async-limiter and the pure JS UTF-8 validator from
ws 7.5.11; see its retained source notes. SSAP clients disable compression and
keep their handshake/payload limits. TV-provided webos-service remains external.
Published historical Helper baselines retain their original bytes.

Run `node tests/helper-compat.cjs` with current Node, or set `NODE012` to a
Node 0.12.2 executable. The regression compiles the actual Helper sources,
exercises controller startup/error handling with TV hardware/Luna substitutes,
and service status/listApps, and performs a real local WSS register/subscribe,
fragmented text, ping/pong and close exchange. Invalid UTF-8 and oversized
payloads must be rejected. CI downloads a SHA-256-pinned official Linux x64
Node 0.12.2 archive. Packaged service tests also use that runtime when available.
This verifies Node compatibility, not access to a TV's evdev devices.

References: [LG engine versions](https://webostv.developer.lge.com/develop/specifications/web-api-and-web-engine),
[Babel preset-env](https://babeljs.io/docs/babel-preset-env),
[PostCSS preset-env](https://preset-env.cssdb.org/),
[doiuse](https://github.com/anandthakker/doiuse).
