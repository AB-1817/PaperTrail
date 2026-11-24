import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./lib/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        // Semantic tokens — driven by CSS variables so dark mode is automatic
        canvas:    "var(--color-canvas)",
        surface:   "var(--color-surface)",
        ink:       "var(--color-ink)",
        stone:     "var(--color-stone)",
        ash:       "var(--color-ash)",
        mute:      "var(--color-mute)",
        hairline:  "var(--color-hairline)",
        primary:   "var(--color-primary)",
        // Static tokens (not theme-switched)
        "on-primary":    "#ffffff",
        "surface-grey":  "#ececec",
        "silver":        "#cccac7",
        "ink-band":      "#000000",
        "ink-band-soft": "#19191c",
        // Earth accents
        gold:       "#af751b",
        ochre:      "#bc924c",
        "gold-soft": "#ddaa61",
        clay:       "#6b443d",
        espresso:   "#39221e",
        forest:     "#224228",
        olive:      "#5c6f5d",
        sage:       "#849671",
        "sage-pale": "#ced4b8",
        error:      "#e33a22",
      },
      fontFamily: {
        serif: ["var(--font-inter)", "'Fraunces'", "Georgia", "serif"],
        sans:  ["var(--font-inter)", "Inter", "system-ui", "sans-serif"],
      },
      borderRadius: {
        xs:   "4px",
        sm:   "8px",
        md:   "12px",
        lg:   "24px",
        xl:   "40px",
        full: "9999px",
      },
      boxShadow: {
        card:     "0 1px 4px 0 rgba(28,27,26,0.06), 0 0 0 1px rgba(225,220,211,0.8)",
        elevated: "0 4px 16px 0 rgba(28,27,26,0.10), 0 1px 4px 0 rgba(28,27,26,0.06)",
      },
    },
  },
  plugins: [],
};

export default config;
