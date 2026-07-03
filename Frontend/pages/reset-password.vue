<script setup>
useSeoMeta({ title: "Set new password | Booksall" });
const route = useRoute();
const toast = useToast();
const { confirmPasswordReset } = useAuth();
const uid = route.query.uid;
const token = route.query.token;
const password = ref("");
const confirm = ref("");
const loading = ref(false);
const error = ref("");
const done = ref(false);
const invalidLink = computed(() => !uid || !token);
async function onSubmit() {
    if (password.value !== confirm.value) {
        error.value = "Passwords do not match.";
        return;
    }
    loading.value = true;
    error.value = "";
    try {
        await confirmPasswordReset(uid, token, password.value);
        done.value = true;
        toast.add({ title: "Password updated. You can sign in now.", color: "green" });
    }
    catch (e) {
        error.value = apiErrorMessage(e, "This link is invalid or has expired.");
    }
    finally {
        loading.value = false;
    }
}
</script>

<template>
  <UContainer class="py-16 max-w-md">
    <UCard v-if="invalidLink" class="text-center">
      <UIcon name="i-heroicons-x-circle" class="text-5xl text-red-500" />
      <p class="mt-3 text-[#888888]">This reset link is invalid. Request a new one.</p>
      <UButton to="/forgot-password" color="primary" variant="soft" class="mt-5">Request reset</UButton>
    </UCard>

    <UCard v-else-if="!done">
      <template #header>
        <h1 class="text-xl font-bold">Set a new password</h1>
      </template>
      <form class="space-y-4" @submit.prevent="onSubmit">
        <UAlert v-if="error" color="red" variant="soft" :title="error" />
        <UFormGroup label="New password" required>
          <UInput v-model="password" type="password" autocomplete="new-password" />
        </UFormGroup>
        <UFormGroup label="Confirm new password" required>
          <UInput v-model="confirm" type="password" autocomplete="new-password" />
        </UFormGroup>
        <UButton type="submit" color="primary" block :loading="loading">Update password</UButton>
      </form>
    </UCard>

    <UCard v-else class="text-center">
      <UIcon name="i-heroicons-check-circle" class="text-5xl text-green-500" />
      <p class="mt-3 text-[#8f8f8f] dark:text-[#565656]">Your password has been updated.</p>
      <UButton to="/login" color="primary" class="mt-5">Sign in</UButton>
    </UCard>
  </UContainer>
</template>
