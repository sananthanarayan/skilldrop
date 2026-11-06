<script setup lang="ts">
const route = useRoute()
const recipe = ref<any>(null)
const saved = ref(false)

onMounted(async () => {
  recipe.value = await $fetch(`/recipes/${route.params.slug}`, {
    baseURL: useRuntimeConfig().public.larderApiBase,
  })
  useHead({
    title: recipe.value.title,
    meta: [
      { property: 'og:title', content: recipe.value.title },
      { property: 'og:image', content: recipe.value.heroImage },
      { name: 'description', content: recipe.value.summary },
    ],
  })
  const token = localStorage.getItem('ck_token')
  if (token) {
    const res: any = await $fetch(`/api/saved/${route.params.slug}`, {
      headers: { Authorization: `Bearer ${token}` },
    })
    saved.value = res.saved
  }
})
</script>

<template>
  <div v-if="recipe">
    <h1>{{ recipe.title }}</h1>
    <SaveHeart :saved="saved" />
    <RatingStars :avg="recipe.ratingAvg" :count="recipe.reviewCount" />
    <IngredientList :items="recipe.ingredients" />
    <MethodSteps :steps="recipe.steps" />
  </div>
  <Spinner v-else />
</template>
