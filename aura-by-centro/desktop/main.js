// Aura (by Centro) — Electron shell.
// A lightweight, Centro-branded desktop client you can install on every PC.
// It does NOT run the LLM locally — it connects to the central Aura backend
// (your AWS deployment). Point it at that URL via the AURA_URL env var.

const { app, BrowserWindow, Tray, Menu, shell, globalShortcut } = require("electron");
const path = require("path");

const AURA_URL = process.env.AURA_URL || "http://localhost:3000";
const CENTRO_PRUSSIAN = "#004A59";

let win = null;
let tray = null;

function createWindow() {
  win = new BrowserWindow({
    width: 440,
    height: 720,
    minWidth: 360,
    minHeight: 520,
    title: "Aura by Centro",
    backgroundColor: CENTRO_PRUSSIAN,
    icon: path.join(__dirname, "assets", "icon.png"),
    show: false,
    webPreferences: {
      preload: path.join(__dirname, "preload.js"),
      contextIsolation: true,
      nodeIntegration: false,
    },
  });

  win.loadURL(AURA_URL);
  win.once("ready-to-show", () => win.show());

  // Open external links in the system browser, keep app links in-app.
  win.webContents.setWindowOpenHandler(({ url }) => {
    if (!url.startsWith(AURA_URL)) {
      shell.openExternal(url);
      return { action: "deny" };
    }
    return { action: "allow" };
  });

  // Hide to tray instead of quitting (popup behaviour).
  win.on("close", (e) => {
    if (!app.isQuitting) {
      e.preventDefault();
      win.hide();
    }
  });
}

function toggleWindow() {
  if (!win) return;
  win.isVisible() ? win.hide() : (win.show(), win.focus());
}

function createTray() {
  tray = new Tray(path.join(__dirname, "assets", "tray.png"));
  tray.setToolTip("Aura by Centro");
  tray.setContextMenu(
    Menu.buildFromTemplate([
      { label: "Open Aura", click: toggleWindow },
      { label: "Reload", click: () => win && win.reload() },
      { type: "separator" },
      { label: "Quit", click: () => { app.isQuitting = true; app.quit(); } },
    ])
  );
  tray.on("click", toggleWindow);
}

app.whenReady().then(() => {
  createWindow();
  createTray();
  // Global hotkey to summon the assistant from anywhere.
  globalShortcut.register("CommandOrControl+Shift+A", toggleWindow);

  app.on("activate", () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on("window-all-closed", () => {
  // Stay alive in the tray on Windows/Linux; standard on macOS.
});

app.on("will-quit", () => globalShortcut.unregisterAll());
