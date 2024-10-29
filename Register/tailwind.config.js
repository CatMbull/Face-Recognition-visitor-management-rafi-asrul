/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./templates/**/*.html", 
    "./src/**/*.css",   
  ],
  theme: {
    extend: {
      colors: {
        customGreen: "rgb(6, 78, 59)",
        biruicon:"rgb(0 ,174 ,239)",
        "birubg":"#4353F0",
        "superwhite":"#ffffff",
      },
    },
  },
  plugins: [],
}

