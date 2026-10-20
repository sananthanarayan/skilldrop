import en from './messages/en'
import de from './messages/de'
import './chartLocales'

export const SUPPORTED_LANGUAGES = ['en', 'de'] as const
export type Language = (typeof SUPPORTED_LANGUAGES)[number]

export const messages: Record<Language, Record<string, string>> = { en, de }
