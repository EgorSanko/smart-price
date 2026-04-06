import type { Config } from 'tailwindcss'

const config: Config = {
  content: ['./src/**/*.{js,ts,jsx,tsx,mdx}'],
  theme: {
    extend: {
      colors: {
        // Маппинг старых классов на твои CSS переменные
        'graphite': {
          950: 'var(--bg)',      // #08080b
          900: 'var(--c1)',      // #111116
          800: 'var(--c2)',      // #1a1a22
          700: 'var(--ci)',      // #13131a
          600: 'var(--bd)',      // #222230
          500: 'var(--bl)',      // #2a2a3a
        },
        'txt': {
          primary: 'var(--t)',    // #e8e8ed
          secondary: 'var(--td)', // #7a7a8e
          muted: 'var(--tm)',     // #55556a
        },
        'accent': {
          DEFAULT: 'var(--ac)',   // #6c5ce7
          light: '#a78bfa',
          dark: '#5849c4',
        },
        'success': 'var(--g)',    // #00d68f
        'warning': 'var(--o)',    // #f5a623
        'danger': 'var(--r)',     // #ff6b6b
      },
      fontFamily: {
        sans: ['Manrope', 'system-ui', 'sans-serif'],
      },
      borderRadius: {
        'xl': '14px',
        '2xl': '18px',
      },
      boxShadow: {
        'card': '0 4px 24px rgba(0,0,0,.3)',
        'glow': '0 0 20px rgba(108,92,231,.4)',
      },
    },
  },
  plugins: [],
}

export default config
