---
name: centro-branding
description: Apply Centro brand identity (colors, Roboto, logo, favicon) to the Aura app. Use when the user asks to (re)brand, fix the logo/favicon, or "apply centro branding". Places the real logo + favicon assets into the frontend and verifies they are in place each run.
---

# Centro Branding

Applies the **Centro Brand Book (Pomelli)** identity to Aura (by Centro).

## Brand tokens
- Prussian Blue `#004A59` (primary) · Onyx `#32373C` (text) · Pure White · Roboto.
- Voice: friendly, professional, precise. Never cheesy or robotic.

## Assets (single source of truth)
Drop the official files in this skill's `assets/` folder (keep these names):
- `assets/logo.svg`    — the brand mark (the "A" monogram; uses currentColor)
- `assets/favicon.svg` — the browser-tab / app icon (solid background)

> If the user uploaded their own logo/favicon, put them here first. If `assets/`
> is empty, the existing placeholders in the repo are kept.

## Apply (run every time)
```bash
bash .claude/skills/centro-branding/apply_branding.sh
```
This copies the assets to the frontend and **verifies they are in place**:
- `frontend/src/components/logo.tsx`  ← derived from `assets/logo.svg`
- `frontend/src/app/icon.svg`         ← `assets/favicon.svg` (Next.js favicon)
- `frontend/public/aura-mark.svg`     ← `assets/favicon.svg`

## LEARNING — checklist to run EVERY time (don't skip)
1. **Place assets:** ensure all three target files above exist and are non-empty.
   A missing/zero-byte favicon or logo is the most common branding regression.
2. **Verify the favicon path:** Next.js App Router serves `src/app/icon.svg`
   automatically — confirm the file is valid SVG (opens without error).
3. **Verify the in-app logo:** `logo.tsx` must export `<Logo>` and be imported
   by `chat-interface.tsx` and `message-bubble.tsx`.
4. **Compile check:** the frontend must still build — run `npm run typecheck`
   (or `next build`) in `aura-by-centro/frontend`. A branding edit that breaks
   the build is worse than no branding.
5. **API docs:** the FastAPI `/docs` favicon is the inline `_BRAND_ICON_SVG` in
   `backend/main.py` — update it if the favicon changes.

> Background: the chat once silently failed because an unrelated backend change
> deadlocked the socket; treat "looks branded" and "actually compiles/works" as
> two separate checks — always confirm both.
