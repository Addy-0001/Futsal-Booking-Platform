<script setup>
useSeoMeta({ title: "Verify email | Booksall" });
const route = useRoute();
const { verifyEmail } = useAuth();
const state = ref("working");
const message = ref("");
onMounted(async () => {
    const uid = route.query.uid;
    const token = route.query.token;
    if (!uid || !token) {
        state.value = "error";
        message.value = "This verification link is invalid.";
        return;
    }
    try {
        await verifyEmail(uid, token);
        state.value = "ok";
    }
    catch (e) {
        state.value = "error";
        message.value = apiErrorMessage(e, "This link is invalid or has expired.");
    }
});
</script>

<template>
  <UContainer class="py-20 max-w-md text-center">
    <UCard>
      <template v-if="state === 'working'">
        <UIcon name="i-heroicons-arrow-path" class="text-4xl text-[#6b6b6b] animate-spin" />
        <p class="mt-3 text-[#888888]">Verifying your email…</p>
      </template>

      <template v-else-if="state === 'ok'">
        <UIcon name="i-heroicons-check-circle" class="text-5xl text-green-500" />
        <h1 class="text-xl font-bold mt-3">Email verified</h1>
        <p class="text-[#888888] mt-2">Your account is ready. You can sign in now.</p>
        <UButton to="/login" color="primary" class="mt-5">Sign in</UButton>
      </template>

      <template v-else>
        <UIcon name="i-heroicons-x-circle" class="text-5xl text-red-500" />
        <h1 class="text-xl font-bold mt-3">Verification failed</h1>
        <p class="text-[#888888] mt-2">{{ message }}</p>
        <UButton to="/login" color="gray" variant="soft" class="mt-5">Back to sign in</UButton>
      </template>
    </UCard>
  </UContainer>
</template>
