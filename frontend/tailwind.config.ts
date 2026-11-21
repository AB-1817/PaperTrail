import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./lib/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        // Oura design system palette
        canvas:    "#f7f1e8", // warm paper — default page background
        surface:   "#ffffff", // elevated cards, inputs
        "surface-grey": "#ececec",
        ink:       "#1c1b1a", // primary heading & body text
        stone:     "#4a4741", // brand neutral — wordmark, secondary buttons, nav
        ash:       "#838280", // muted meta text
        mute:      "#a8a5a0", // quietest captions
        hairline:  "#e1dcd3", // 1px dividers on canvas
        silver:    "#cccac7",
        "ink-band":      "#000000",
        "ink-band-soft": "#19191c", // footer surface
        // Action
        primary:   "#2a72de", // single conversion blue — CTA only
        "on-primary": "#ffffff",
        // Earth accents (bands/data-viz only — never buttons)
        gold:      "#af751b",
        ochre:     "#bc924c",
        "gold-soft":"#ddaa61",
        clay:      "#6b443d",
        espresso:  "#39221e",
        forest:    "#224228",
        olive:     "#5c6f5d",
        sage:      "#849671",
        "sage-pale":"#ced4b8",
        // Semantic
        error:     "#e33a22",
      },
      fontFamily: {
        serif: ["var(--font-fraunces)", "Fraunces", "Georgia", "serif"],
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
