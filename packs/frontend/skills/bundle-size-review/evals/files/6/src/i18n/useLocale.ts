import { useSyncExternalStore } from 'react'
import { SUPPORTED_LANGUAGES, type Language } from './index'

function read(): Language {
  const stored = localStorage.getItem('tpo.lang')
  return (SUPPORTED_LANGUAGES as readonly string[]).includes(stored ?? '') ? (stored as Language) : 'en'
}

export function useLocale(): Language {
  return useSyncExternalStore((cb) => {
    window.addEventListener('storage', cb)
    return () => window.removeEventListener('storage', cb)
  }, read)
}
