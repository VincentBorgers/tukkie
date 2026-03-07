/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        sand: "#F3EBDD",
        clay: "#C8683A",
        moss: "#5B7254",
        ink: "#14222E",
        mist: "#D7E1E8"
      },
      boxShadow: {
        panel: "0 22px 44px rgba(20, 34, 46, 0.12)"
      },
      borderRadius: {
        panel: "28px"
      }
    }
  },
  plugins: []
};

