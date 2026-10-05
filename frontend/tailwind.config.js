/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      fontFamily: {
        wandor: ['"Special Elite"', 'Georgia', 'serif'],
        sans: ['Geist', 'Inter', 'system-ui', '-apple-system', 'BlinkMacSystemFont', 'sans-serif'],
        mono: ['"Geist Mono"', 'ui-monospace', 'monospace'],
      },
      colors: {
        terracotta: {
          50: '#fdf6f3',
          100: '#faece6',
          200: '#f6d9ce',
          300: '#efbeab',
          400: '#e59a7f',
          500: '#d97757',
          600: '#c55c3c',
          700: '#a4472d',
          800: '#863c27',
          900: '#6f3525',
          950: '#3c1810',
        },
        sand: {
          50: '#faf8f5',
          100: '#f4f0e9',
          200: '#eae0d2',
          300: '#dcceb8',
          400: '#c9b498',
          500: '#b79c7c',
          600: '#aa8b6c',
          700: '#8e7157',
          800: '#735c49',
          900: '#5f4d3d',
        },
        glass: {
          light: 'rgba(255, 255, 255, 0.75)',
          medium: 'rgba(255, 255, 255, 0.55)',
          dark: 'rgba(18, 18, 20, 0.75)',
          card: 'rgba(255, 255, 255, 0.85)',
          border: 'rgba(255, 255, 255, 0.35)',
        }
      },
      boxShadow: {
        'glass': '0 8px 32px 0 rgba(0, 0, 0, 0.08)',
        'glass-hover': '0 12px 40px 0 rgba(0, 0, 0, 0.14)',
        'glow': '0 0 25px rgba(217, 119, 87, 0.35)',
        'card': '0 4px 20px -2px rgba(0, 0, 0, 0.06), 0 2px 6px -1px rgba(0, 0, 0, 0.04)',
      },
      borderRadius: {
        '4xl': '2rem',
        '5xl': '2.5rem',
      },
      backdropBlur: {
        'xs': '2px',
        'md': '12px',
        'xl': '24px',
        '2xl': '40px',
      }
    },
  },
  plugins: [],
}
