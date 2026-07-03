<script setup>
useSeoMeta({ title: "Reset password | Booksall" });
const { requestPasswordReset } = useAuth();
const email = ref("");
const loading = ref(false);
const done = ref(false);
async function onSubmit() {
    loading.value = true;
    try {
        await requestPasswordReset(email.value);
    }
    finally {
        // Always show the same message — never reveal whether the email exists.
        done.value = true;
        loading.value = false;
    }
}
</script>

<template>
  <UContainer class="py-16 max-w-md">
    <UCard v-if="!done">
      <template #header>
        <h1 class="text-xl font-bold">Reset your password</h1>
      </template>
      <form class="space-y-4" @submit.prevent="onSubmit">
        <p class="text-sm text-[#888888]">
          Enter your email and we'll send a reset link (valid for 30 minutes).
        </p>
        <UFormGroup label="Email" required>
          <UInput v-model="email" type="email" autocomplete="email" />
        </UFormGroup>
        <UButton type="submit" color="primary" block :loading="loading">Send reset link</UButton>
      </form>
    </UCard>

    <UCard v-else class="text-center">
      <UIcon name="i-heroicons-envelope" class="text-4xl text-primary-600" />
      <p class="mt-3 text-[#8f8f8f] dark:text-[#565656]">
        If an account exists for that email, a reset link is on its way.
      </p>
      <UButton to="/login" color="primary" variant="soft" class="mt-5">Back to sign in</UButton>
    </UCard>
  </UContainer>
</template>
