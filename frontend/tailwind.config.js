/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        sand: "#040814",
        canvas: "#091225",
        ink: "#050816",
        mist: "#0D1B35",
        ocean: "#45C7FF",
        ember: "#F97316",
        moss: "#22C55E",
        butter: "#7DD3FC",
      },
      fontFamily: {
        display: ["Sora", "sans-serif"],
        body: ["IBM Plex Sans", "sans-serif"],
      },
      boxShadow: {
        panel: "0 28px 80px -42px rgba(69, 199, 255, 0.42)",
        soft: "0 18px 45px -28px rgba(69, 199, 255, 0.28)",
      },
      keyframes: {
        float: {
          "0%, 100%": { transform: "translateY(0px)" },
          "50%": { transform: "translateY(-12px)" },
        },
        drift: {
          "0%, 100%": { transform: "translateX(0px)" },
          "50%": { transform: "translateX(10px)" },
        },
      },
      animation: {
        float: "float 7s ease-in-out infinite",
        drift: "drift 9s ease-in-out infinite",
      },
    },
  },
  plugins: [],
};
