/**
 * Aura (by Centro) — brand logo mark (the "A" monogram).
 *
 * Uses `currentColor`, so it inherits the surrounding text color (e.g. white
 * inside a Prussian Blue chip). Single source of truth for the in-app mark.
 * To rebrand, edit this file and/or the standalone assets:
 *   - Favicon:        frontend/src/app/icon.svg
 *   - Public mark:    frontend/public/aura-mark.svg
 */
export function Logo({ className = "h-5 w-5" }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 64 64"
      className={className}
      fill="none"
      role="img"
      aria-label="Aura by Centro"
    >
      <path
        d="M15 49 L32 15 L49 49"
        stroke="currentColor"
        strokeWidth="6.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <path
        d="M22 37 L42 37"
        stroke="currentColor"
        strokeWidth="6.5"
        strokeLinecap="round"
      />
    </svg>
  );
}
