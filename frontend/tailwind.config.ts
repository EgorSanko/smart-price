import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        // Графитовая тема
        graphite: {
          950: '#0D0E13',  // Основной фон
          900: '#13141B',  // Шапка
          800: '#1B1D29',  // Карточки
          700: '#242736',  // Hover карточек
          600: '#2D3143',  // Бордеры
          500: '#3D4155',  // Неактивные элементы
        },
        // Фиолетовый акцент
        accent: {
          DEFAULT: '#5F4BFF',
          light: '#8C7BFF',
          dark: '#4A38CC',
        },
        // Текст
        txt: {
          primary: '#ECEBFA',
          secondary: '#A1A1B8',
          muted: '#6B6B80',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
      boxShadow: {
        'card': '0 4px 24px rgba(0, 0, 0, 0.3)',
        'glow': '0 0 20px rgba(95, 75, 255, 0.3)',
      },
    },
  },
  plugins: [],
}
export default config
