/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: '#4CAF50',
          light: '#A3E4A6',
          dark: '#388E3C',
        },
        surface: {
          DEFAULT: '#F5F0E8',
          dark: '#2D2A26',
        },
        accent: {
          orange: '#FFB74D',
          yellow: '#FFD54F',
        },
      },
      fontFamily: {
        sans: ['Poppins', 'Inter', 'Nunito', 'system-ui', 'sans-serif'],
      },
      boxShadow: {
        card: '0 2px 8px rgba(0,0,0,0.06)',
        cardHover: '0 8px 24px rgba(0,0,0,0.08)',
      },
    },
  },
  plugins: [],
}
