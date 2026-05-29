import type { Config } from "tailwindcss";

/**
 * Centro Brand Book (Pomelli) tokens.
 * Prussian Blue #004A59 · Pure White #FFFFFF · Onyx Black #32373C · Roboto
 */
const config: Config = {
  content: [
    "./src/app/**/*.{ts,tsx}",
    "./src/components/**/*.{ts,tsx}",
    "./src/hooks/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        centro: {
          prussian: "#004A59",
          "prussian-700": "#063b47",
          "prussian-900": "#042830",
          white: "#FFFFFF",
          onyx: "#32373C",
          "onyx-800": "#262a2e",
          "onyx-900": "#1b1e21",
          mist: "#E8EEF0",
          accent: "#1A7A9E",
        },
      },
      fontFamily: {
        sans: ["Roboto", "system-ui", "Arial", "sans-serif"],
      },
      boxShadow: {
        card: "0 8px 30px rgba(0, 74, 89, 0.12)",
      },
      keyframes: {
        "fade-up": {
          "0%": { opacity: "0", transform: "translateY(6px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        blink: { "0%, 100%": { opacity: "1" }, "50%": { opacity: "0" } },
      },
      animation: {
        "fade-up": "fade-up 0.25s ease-out",
        blink: "blink 1s step-start infinite",
      },
    },
  },
  plugins: [],
};

export default config;
