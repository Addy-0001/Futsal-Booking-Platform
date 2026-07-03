<script setup>
const props = defineProps(['slug']);
const api = useApi();
const { data: policy, error } = await useAsyncData(`policy-${props.slug}`, () => api(`/api/policies/${props.slug}/`));
useSeoMeta({
    title: () => `${policy.value?.title ?? "Policy"} | Booksall`,
    description: () => policy.value?.body?.slice(0, 150),
});
</script>

<template>
  <UContainer class="py-12 max-w-3xl">
    <div v-if="policy">
      <h1 class="font-display text-3xl font-bold text-[#f0f0f0] mb-1">{{ policy.title }}</h1>
      <p class="text-sm text-[#6b6b6b] mb-6">
        Version {{ policy.version }} · Updated {{ new Date(policy.published_at).toLocaleDateString() }}
      </p>
      <div class="prose dark:prose-invert max-w-none whitespace-pre-line">{{ policy.body }}</div>
    </div>
    <p v-else-if="error" class="text-[#888888]">This policy isn't available yet.</p>
  </UContainer>
</template>
