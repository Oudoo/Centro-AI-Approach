# Per-PC Client — Packaging Options (DECISION REQUIRED)

> ⚠️ **ACTION ITEM (owner: you):** choose one of the three options below. Until
> you decide, the repo ships the **Electron** scaffold in `desktop/` as a working
> default. Tell me your pick and I'll fully wire it up (icons, build config,
> auto-update, baked-in AWS URL, code signing notes).

**What this is:** the app installed on every employee's PC. In all three options
it is a *thin client* — the Gemma model runs centrally on AWS, the client just
renders the chat UI and talks to the backend over WebSocket. They differ only in
*how the UI is packaged and delivered*.

---

## Option A — Electron  *(currently scaffolded)*

Wraps the existing Next.js UI in a Chromium shell. Tray "popup" + global hotkey.

**Pros**
- ✅ Cross-platform from one codebase: Windows `.exe`, macOS `.dmg` (Intel + ARM), Linux.
- ✅ Largest ecosystem — auto-update, code signing, notifications, deep-linking are all well-trodden.
- ✅ Reuses 100% of the web UI we already built; near-zero rework.
- ✅ Best fit for a **mixed Windows/Mac corporate fleet**.

**Cons**
- ❌ Large installers (~120–180 MB) and higher RAM per instance (bundles Chromium).
- ❌ Heavier to push as a fleet update.

**Effort to productionize:** Low (scaffold exists).
**Best when:** you want the safest, fastest path across a varied fleet and don't mind size.

---

## Option B — Tauri (Rust)

Same idea, but uses the OS's *native* webview instead of bundling Chromium.

**Pros**
- ✅ Tiny installers (~3–10 MB) and much lower memory footprint.
- ✅ More secure default posture; native performance.
- ✅ Still reuses the web UI.

**Cons**
- ❌ Requires the **Rust toolchain** + platform build deps in CI.
- ❌ Uses each OS's webview (WebView2 on Windows, WebKit on macOS) → slightly more cross-browser testing.
- ❌ I'd rewrite the `desktop/` shell (Electron → Tauri).

**Effort to productionize:** Medium (toolchain + shell rewrite).
**Best when:** you care about install size/RAM at 1,500 seats and are OK adding Rust to the build.

---

## Option C — PWA "Install app"

No packaging at all. Serve the frontend as an installable Progressive Web App;
users click **Install** in their browser to get an app-like window + icon.

**Pros**
- ✅ Zero build/distribution pipeline — ship the website, done.
- ✅ Instant updates (refresh = latest version); nothing to redeploy to PCs.
- ✅ No code signing, no MB-sized installers.

**Cons**
- ❌ Least native control: no global hotkey, limited tray, weaker offline/native integrations.
- ❌ Install UX varies by browser; some locked-down corporate browsers disable it.
- ❌ Not a "real" installed `.exe` for IT inventory/MDM in the traditional sense.

**Effort to productionize:** Lowest (add manifest + service worker).
**Best when:** you want the fastest rollout and are happy with a browser-based experience.

---

## Quick comparison

| Criteria              | Electron (A) | Tauri (B)      | PWA (C)        |
|-----------------------|--------------|----------------|----------------|
| Installer size        | ~120–180 MB  | ~3–10 MB       | none           |
| Memory per instance   | High         | Low            | Browser-shared |
| Cross-platform        | Excellent    | Excellent      | Good           |
| Native features (tray, hotkey) | Full | Full           | Limited        |
| Build complexity      | Low          | Medium (Rust)  | Lowest         |
| Fleet update          | Re-push build| Re-push build  | Instant        |
| IT/MDM packaging      | Standard     | Standard       | Browser-managed|
| Reuses our web UI     | ✅           | ✅             | ✅             |

## My recommendation (non-binding)
- **Pick A (Electron)** if you want it done fast and reliably across Windows + Mac — it's already scaffolded.
- **Pick B (Tauri)** if footprint at 1,500 seats matters and Rust in CI is acceptable.
- **Pick C (PWA)** if you'd rather avoid per-PC installs entirely and push updates instantly.

> Reply with **A**, **B**, or **C** and I'll complete the chosen path end-to-end.
