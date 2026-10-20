// Crumbly Kitchen - Nuxt 3
export default defineNuxtConfig({
  ssr: false,
  nitro: {
    preset: 'static',
  },
  app: {
    head: {
      title: 'Crumbly Kitchen',
      meta: [{ name: 'description', content: 'Recipes for every day' }],
    },
  },
  runtimeConfig: {
    public: {
      larderApiBase: 'https://cms.example.invalid/api',
      findItKey: 'PLACEHOLDER_SEARCH_KEY',
    },
  },
})
