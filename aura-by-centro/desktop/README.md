# Aura (by Centro) — Desktop Client

A lightweight, Centro-branded desktop app (Electron) you can install on every
company PC — a tray "popup" assistant like Zoho SalesIQ's widget, but native and
yours. It does **not** run the model locally; it's a thin client that connects to
the central Aura backend (your AWS deployment).

## How it fits
```
[ Desktop client (this) ]  --WebSocket-->  [ Aura backend on AWS ]  -->  [ Gemma on GPU ]
   installed per PC                              FastAPI                    vLLM
```

## Run in dev
```bash
cd desktop
npm install
AURA_URL=http://localhost:3000 npm start   # point at your running frontend
```
- Press **Ctrl/Cmd+Shift+A** anywhere to summon the window.
- Closing hides to the tray; quit from the tray menu.

## Build installers (.dmg / .exe / AppImage)
```bash
AURA_URL=https://aura.centro.example npm run dist        # current OS
npm run dist:win                                         # Windows .exe + portable
npm run dist:mac                                          # macOS .dmg (Intel + ARM)
```
Bake the production `AURA_URL` into the build (env at build time or a small
`config.json`) so installed clients point at AWS automatically.

## Branding
Drop your assets in `desktop/assets/`:
- `icon.png` (512×512) — app icon
- `tray.png` (16/32px) — menu-bar/tray icon

Window chrome uses Prussian Blue `#004A59` to match the Centro Brand Book.

## Alternatives
- **Tauri** (Rust) — much smaller binaries (~3–10MB vs ~150MB), but needs the
  Rust toolchain. Same model: wraps the web UI, talks to AWS.
- **PWA / "Install app"** — zero packaging: serve the frontend as an installable
  PWA and users "Install" from the browser. Least control, fastest rollout.
