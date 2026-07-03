<script setup>
// Client-only banner; records consent against the current cookie policy version.
const api = useApi();
const KEY = "booksall_cookie_consent";
const visible = ref(false);
onMounted(() => {
    visible.value = !localStorage.getItem(KEY);
});
async function accept() {
    visible.value = false;
    localStorage.setItem(KEY, new Date().toISOString());
    try {
        await api("/api/consent/", { method: "POST", body: { slug: "cookies" } });
    }
    catch {
        // non-blocking
    }
}
</script>

<template>
  <ClientOnly>
    <div
      v-if="visible"
      class="fixed bottom-4 inset-x-4 sm:inset-x-auto sm:right-6 sm:max-w-md z-50"
    >
      <UCard :ui="{ body: { padding: 'p-4' } }" class="shadow-lg">
        <p class="text-sm text-[#8f8f8f] dark:text-[#565656]">
          We use essential cookies to keep you signed in and remember preferences. See our
          <NuxtLink to="/cookies" class="text-primary-600 hover:underline">Cookie Policy</NuxtLink>.
        </p>
        <div class="flex justify-end gap-2 mt-3">
          <UButton color="gray" variant="soft" size="xs" to="/cookies">Learn more</UButton>
          <UButton color="primary" size="xs" @click="accept">Accept</UButton>
        </div>
      </UCard>
    </div>
  </ClientOnly>
</template>
