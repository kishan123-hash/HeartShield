/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          50: '#FDF2F4',
          100: '#FCE7EA',
          200: '#F8D0D6',
          300: '#F2AAB4',
          400: '#E87486',
          500: '#D8455E',
          600: '#B8233E',
          700: '#8B1E2D',
          800: '#800020', // Primary HeartShield Burgundy
          900: '#640F1D',
          950: '#3D050E',
        },
        warm: {
          bg: '#FFF8F6',
          card: '#FFFFFF',
          border: '#F2D7D5',
          text: '#2C1810',
          muted: '#7E6360',
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      }
    },
  },
  plugins: [],
}
