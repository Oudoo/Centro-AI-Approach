#!/usr/bin/env bash
# Apply Centro branding assets into the Aura frontend, then verify + build-check.
set -euo pipefail

SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SKILL_DIR/../../.." && pwd)"
FE="$REPO_ROOT/aura-by-centro/frontend"
A="$SKILL_DIR/assets"

ok() { printf "  \033[92m✓\033[0m %s\n" "$1"; }
err() { printf "  \033[91m✗\033[0m %s\n" "$1"; }

echo "▶ Applying Centro branding…"

# 1) Favicon + public mark from assets/favicon.svg
if [[ -s "$A/favicon.svg" ]]; then
  cp "$A/favicon.svg" "$FE/src/app/icon.svg"
  cp "$A/favicon.svg" "$FE/public/aura-mark.svg"
  ok "favicon -> src/app/icon.svg + public/aura-mark.svg"
else
  err "assets/favicon.svg missing — keeping existing favicon"
fi

# 2) In-app logo: regenerate logo.tsx body from assets/logo.svg inner paths.
if [[ -s "$A/logo.svg" ]]; then
  INNER="$(grep -oE '<path[^>]*/>' "$A/logo.svg" | sed 's/stroke-width/strokeWidth/g; s/stroke-linecap/strokeLinecap/g; s/stroke-linejoin/strokeLinejoin/g')"
  {
    echo '/** Auto-applied by .claude/skills/centro-branding. Edit assets/logo.svg + re-run. */'
    echo 'export function Logo({ className = "h-5 w-5" }: { className?: string }) {'
    echo '  return ('
    echo '    <svg viewBox="0 0 64 64" className={className} fill="none" role="img" aria-label="Aura by Centro">'
    echo "      $INNER"
    echo '    </svg>'
    echo '  );'
    echo '}'
  } > "$FE/src/components/logo.tsx"
  ok "logo -> src/components/logo.tsx"
else
  err "assets/logo.svg missing — keeping existing logo"
fi

# 3) Verify presence + non-empty (the #1 regression)
echo "▶ Verifying assets are in place…"
fail=0
for f in "$FE/src/app/icon.svg" "$FE/public/aura-mark.svg" "$FE/src/components/logo.tsx"; do
  if [[ -s "$f" ]]; then ok "$(basename "$f") present"; else err "$f MISSING/empty"; fail=1; fi
done

# 4) Build/type check so branding never breaks the app
if [[ -d "$FE/node_modules" ]]; then
  echo "▶ Type-checking frontend…"
  ( cd "$FE" && npm run typecheck ) && ok "frontend type-checks" || { err "typecheck failed"; fail=1; }
else
  echo "  (skip typecheck — run 'make setup' first)"
fi

[[ "$fail" == 0 ]] && echo "✅ Centro branding applied and verified." || { echo "⚠️  Branding issues above — fix before demo."; exit 1; }
