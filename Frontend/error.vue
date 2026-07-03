<script setup>
const props = defineProps(['error']);
const is404 = computed(() => props.error?.statusCode === 404);
</script>

<template>
  <div class="min-h-screen flex items-center justify-center bg-[#141414] dark:bg-[#0a0a0a] px-4">
    <div class="text-center max-w-md">
      <p class="text-6xl font-extrabold text-primary-600">{{ error.statusCode }}</p>
      <h1 class="mt-4 text-2xl font-bold text-[#f0f0f0] dark:text-white">
        {{ is404 ? "Page not found" : "Something went wrong" }}
      </h1>
      <p class="mt-2 text-[#888888]">
        {{ is404 ? "The page you're looking for doesn't exist or has moved." : error.message }}
      </p>
      <UButton class="mt-6" color="primary" @click="clearError({ redirect: '/' })">
        Back to home
      </UButton>
    </div>
  </div>
</template>
