<script setup>
definePageMeta({ middleware: "guest" });
useSeoMeta({ title: "Create account | Booksall" });
const { register } = useAuth();
const toast = useToast();
const form = reactive({
    full_name: "",
    email: "",
    phone: "",
    password: "",
    password_confirm: "",
});
const loading = ref(false);
const error = ref("");
const done = ref(false);
async function onSubmit() {
    if (form.password !== form.password_confirm) {
        error.value = "Passwords do not match.";
        return;
    }
    loading.value = true;
    error.value = "";
    try {
        await register(form);
        done.value = true;
        toast.add({ title: "Account created — check your email to verify.", color: "green" });
    }
    catch (e) {
        error.value = apiErrorMessage(e, "Could not create account.");
    }
    finally {
        loading.value = false;
    }
}
</script>

<template>
  <UContainer class="py-16 max-w-md">
    <NuxtLink to="/" class="flex items-center justify-center gap-2 font-display font-bold text-xl text-[#f0f0f0] mb-6">
      <span class="grid place-items-center w-9 h-9 rounded-xl bg-[#c9ff47] text-black">⚽</span>
      Booksall
    </NuxtLink>
    <UCard v-if="!done">
      <template #header>
        <h1 class="font-display text-xl font-bold text-[#f0f0f0]">Create your account</h1>
      </template>

      <form class="space-y-4" @submit.prevent="onSubmit">
        <UAlert v-if="error" color="red" variant="soft" :title="error" />

        <UFormGroup label="Full name">
          <UInput v-model="form.full_name" autocomplete="name" />
        </UFormGroup>

        <UFormGroup label="Email" required>
          <UInput v-model="form.email" type="email" autocomplete="email" />
        </UFormGroup>

        <UFormGroup label="Mobile number" required hint="Nepali format, e.g. 98XXXXXXXX">
          <UInput v-model="form.phone" inputmode="numeric" placeholder="98XXXXXXXX" />
        </UFormGroup>

        <UFormGroup label="Password" required>
          <UInput v-model="form.password" type="password" autocomplete="new-password" />
        </UFormGroup>

        <UFormGroup label="Confirm password" required>
          <UInput v-model="form.password_confirm" type="password" autocomplete="new-password" />
        </UFormGroup>

        <UButton type="submit" color="primary" block :loading="loading">Create account</UButton>
      </form>

      <template #footer>
        <p class="text-sm text-[#888888] text-center">
          Already have an account?
          <NuxtLink to="/login" class="text-primary-600 hover:underline">Sign in</NuxtLink>
        </p>
      </template>
    </UCard>

    <UCard v-else class="text-center">
      <UIcon name="i-heroicons-envelope" class="text-4xl text-primary-600" />
      <h1 class="text-xl font-bold mt-3">Verify your email</h1>
      <p class="text-[#888888] mt-2">
        We've sent a verification link to <strong>{{ form.email }}</strong>. It expires in 30 minutes.
      </p>
      <UButton to="/login" color="primary" variant="soft" class="mt-5">Go to sign in</UButton>
    </UCard>
  </UContainer>
</template>
