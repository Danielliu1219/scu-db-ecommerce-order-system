export const demoMode = import.meta.env.VITE_DEMO_MODE === 'true'
export const apiBase = (import.meta.env.VITE_API_BASE_URL || '/api/v1').replace(/\/$/, '')
export const appBase = import.meta.env.BASE_URL || '/'
export const guestSession = () => demoMode || !sessionStorage.getItem('access_token')
