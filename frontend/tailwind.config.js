/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class', // support class-based dark mode (we will make it default)
  theme: {
    extend: {
      colors: {
        brand: {
          dark: "#080b16",
          secondary: "#0f1322",
          tertiary: "#191e32",
          card: "rgba(25, 30, 50, 0.65)",
          border: "rgba(255, 255, 255, 0.08)",
        },
        accent: {
          blue: "#0ea5e9", // electric sky blue
          purple: "#6366f1", // indigo tech
          cyan: "#06b6d4", // cyber cyan
        }
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "-apple-system", "sans-serif"],
        heading: ["Outfit", "sans-serif"],
        mono: ["JetBrains Mono", "monospace"],
      },
    },
  },
  plugins: [],
}

