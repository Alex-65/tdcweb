import { defineStore } from 'pinia'

export const useLocaleStore = defineStore('locale', () => {
  const current = ref<string>('en')
  const setLocale = (code: string) => { current.value = code }
  return { current, setLocale }
})
