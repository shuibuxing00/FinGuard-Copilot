/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        surface: { DEFAULT: '#161b22', light: '#21262d' },
        border: '#30363d',
      },
    },
  },
  plugins: [],
};
