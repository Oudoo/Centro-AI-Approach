// Aura (by Centro) — preload bridge.
// Exposes a minimal, safe surface to the web app. Extend with native features
// (notifications, auto-update, SSO token handoff) as needed.
const { contextBridge } = require("electron");

contextBridge.exposeInMainWorld("aura", {
  platform: process.platform,
  isDesktop: true,
  version: process.env.npm_package_version || "0.1.0",
});
