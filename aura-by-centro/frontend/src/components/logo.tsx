/**
 * Aura (by Centro) — brand logo mark.
 *
 * The "A" monogram from the Centro Brand Book palette. Uses `currentColor` so it
 * inherits text color (e.g. white inside a Prussian Blue chip). Single source of
 * truth for the brand mark across the app.
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
        d="M32 14c-1 0-1.9.6-2.3 1.5L18.4 41.7c-.7 1.6.5 3.3 2.2 3.3 1 0 1.9-.6 2.3-1.5l2.1-4.8h13.9l2.1 4.8c.4.9 1.3 1.5 2.3 1.5 1.8 0 2.9-1.7 2.2-3.3L34.3 15.5A2.5 2.5 0 0 0 32 14Zm-4.6 20.6L32 23.9l4.6 10.7h-9.2Z"
        fill="currentColor"
      />
      <circle cx="32" cy="50" r="2.4" fill="currentColor" />
    </svg>
  );
}
