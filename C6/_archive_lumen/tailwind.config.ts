import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          50: "#fff8ed",
          100: "#ffefd4",
          200: "#ffdba8",
          300: "#ffc072",
          400: "#ff9d38",
          500: "#fb8106",
          600: "# ea6303",
          700: "#c44a07",
          800: "#9c390d",
          900: "#7e300f",
        },
        ink: {
          50: "#f6f7f9",
          100: "#eceef2",
          200: "#d5d9e0",
          300: "#b0b8c4",
          400: "#8590a3",
          500: "#667085",
          600: "#525862",
          700: "#44474e",
          800: "#2b2d33",
          900: "#1a1b1f",
        },
      },
      fontFamily: {
        sans: [
          "ui-sans-serif",
          "system-ui",
          "-apple-system",
          "Segoe UI",
          "Roboto",
          "Helvetica Neue",
          "Arial",
          "PingFang SC",
          "Hiragino Sans GB",
          "Microsoft YaHei",
          "sans-serif",
        ],
      },
      boxShadow: {
        soft: "0 1px 2px rgba(16,24,40,0.06), 0 1px 3px rgba(16,24,40,0.10)",
        card: "0 4px 24px rgba(16,24,40,0.08)",
      },
      keyframes: {
        "fade-in": {
          from: { opacity: "0", transform: "translateY(4px)" },
          to: { opacity: "1", transform: "translateY(0)" },
        },
      },
      animation: {
        "fade-in": "fade-in 0.25s ease-out",
      },
    },
  },
  plugins: [],
};

export default config;
