# Aura (by Centro) — Brand System

Derived directly from the **Centro Brand Book (by Pomelli)** and applied across
the whole product (web chat, embed widget, admin dashboard, desktop client,
CTO collateral).

## Colors
| Token | Hex | Use |
|-------|-----|-----|
| Prussian Blue | `#004A59` | Primary — headers, buttons, logo chip, accents |
| Onyx Black | `#32373C` | Body text, user message bubbles |
| Pure White | `#FFFFFF` | Surfaces, assistant bubbles |
| Mist (derived) | `#E8EEF0` | Borders, subtle backgrounds |
| Accent (derived) | `#1A7A9E` | Section labels, links |

Tokens live in `frontend/tailwind.config.ts` (`centro.*`) and
`backend/config.py` (`Brand`). Use the tokens — never hard-code hex in
components.

## Typography
**Roboto** (primary typeface from the brand book), loaded in
`frontend/src/app/globals.css` and set as the Tailwind `sans` default. Weights
300/400/500/700.

## Logo & favicon — files to replace
To rebrand, replace these files (they're the single sources of truth):

| Asset | Path | Used for |
|-------|------|----------|
| In-app logo (inline SVG) | `frontend/src/components/logo.tsx` | chat header, empty-state hero, assistant avatars (uses `currentColor`) |
| Favicon / browser tab | `frontend/src/app/icon.svg` | auto-served by Next.js as the favicon |
| Public mark | `frontend/public/aura-mark.svg` | OG/social + standalone reference |
| API docs favicon | inline `_BRAND_ICON_SVG` in `backend/main.py` | the `/docs` tab icon |

Just drop in your own SVG at those paths (keep the same filenames). The current
mark is the Aura "A" monogram on Prussian Blue `#004A59`. Minimum size ~16px.

## Voice & tone
Friendly, helpful, concise — a supportive colleague. Professional and precise,
never cheesy or robotic. Aura answers **only** from approved knowledge and never
fabricates company information.

## Brand strings
Single source of truth: `frontend/src/lib/brand.ts` (`BRAND.*`) and
`backend/config.py` (`Brand`). Name: **Aura**. Full name: **Aura by Centro**.

> Note: there is no `/centro-branding` slash command/skill in this environment —
> branding is applied directly in code using the system above.
