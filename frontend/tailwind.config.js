/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        bg: '#0F172A',
        card: '#1E293B',
        border: '#334155',
        textPrimary: '#F1F5F9',
        textSecondary: '#94A3B8',
        low: '#22C55E',
        medium: '#FACC15',
        high: '#FB923C',
        critical: '#EF4444',
        attack: '#DC2626',
        accent: '#06B6D4',
      }
    },
  },
  plugins: [],
}
