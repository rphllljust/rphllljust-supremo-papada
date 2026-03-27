/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx,ts,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Rawline', 'Segoe UI', 'Tahoma', 'sans-serif'],
      },
      colors: {
        institutional: {
          dark: '#163126',
          base: '#2D6A4F',
          light: '#52B788',
          pale: '#D8F3DC',
        },
      },
      boxShadow: {
        wizard: '0 12px 24px rgba(27, 67, 50, 0.12)',
      },
    },
  },
  corePlugins: {
    preflight: false,
  },
  plugins: [],
}
