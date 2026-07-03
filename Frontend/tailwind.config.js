// Merged into Nuxt UI's generated Tailwind config.
export default {
  theme: {
    extend: {
      fontFamily: {
        sans: ["Inter", "ui-sans-serif", "system-ui", "sans-serif"],
        display: ['"Barlow Condensed"', "Inter", "ui-sans-serif", "system-ui", "sans-serif"],
      },
      colors: {
        // Near-black "ink" ramp for dark surfaces (matches template).
        ink: {
          50: "#f0f0f0",
          100: "#d8d8d8",
          200: "#b0b0b0",
          300: "#888888",
          400: "#555555",
          500: "#333333",
          600: "#262626",
          700: "#1e1e1e",
          800: "#1a1a1a",
          900: "#141414",
          950: "#0a0a0a",
        },
        // Neon lime — the brand accent. 400 = template #c9ff47.
        volt: {
          50: "#f9ffe8",
          100: "#f0ffc4",
          200: "#e4ff93",
          300: "#d6ff6b",
          400: "#c9ff47",
          500: "#aef01f",
          600: "#8ac70c",
          700: "#679410",
          800: "#517214",
          900: "#445f16",
          950: "#243600",
        },
        brand: {
          50: "#f9ffe8",
          100: "#f0ffc4",
          200: "#e4ff93",
          300: "#d6ff6b",
          400: "#c9ff47",
          500: "#aef01f",
          600: "#8ac70c",
          700: "#679410",
          800: "#517214",
          900: "#445f16",
          950: "#243600",
        },
      },
      boxShadow: {
        volt: "0 18px 50px -12px rgba(201, 255, 71, 0.35)",
        "volt-lg": "0 26px 70px -16px rgba(201, 255, 71, 0.45)",
        lime: "0 18px 50px -12px rgba(201, 255, 71, 0.35)",
        glow: "0 18px 50px -16px rgba(201, 255, 71, 0.35)",
        "card-hover": "0 28px 60px -20px rgba(0, 0, 0, 0.7)",
      },
      keyframes: {
        floaty: {
          "0%, 100%": { transform: "translateY(0)" },
          "50%": { transform: "translateY(-12px)" },
        },
        shimmer: {
          "100%": { transform: "translateX(100%)" },
        },
      },
      animation: {
        floaty: "floaty 6s ease-in-out infinite",
        shimmer: "shimmer 2s infinite",
      },
    },
  },
};
