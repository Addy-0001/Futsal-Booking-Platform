<script setup>
definePageMeta({ middleware: "guest" });
useSeoMeta({ title: "Sign in | Booksall" });
const { login } = useAuth();
const route = useRoute();
const toast = useToast();
const form = reactive({ email: "", password: "" });
const loading = ref(false);
const error = ref("");
async function onSubmit() {
    loading.value = true;
    error.value = "";
    try {
        await login(form.email, form.password);
        toast.add({ title: "Welcome back!", color: "green" });
        await navigateTo(route.query.next || "/dashboard/bookings");
    }
    catch (e) {
        error.value = apiErrorMessage(e, "Invalid email or password.");
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
    <UCard>
      <template #header>
        <h1 class="font-display text-xl font-bold text-[#f0f0f0]">Sign in to Booksall</h1>
      </template>

      <form class="space-y-4" @submit.prevent="onSubmit">
        <UAlert v-if="error" color="red" variant="soft" :title="error" />

        <UFormGroup label="Email" required>
          <UInput v-model="form.email" type="email" autocomplete="email" placeholder="you@example.com" />
        </UFormGroup>

        <UFormGroup label="Password" required>
          <UInput v-model="form.password" type="password" autocomplete="current-password" />
        </UFormGroup>

        <div class="flex justify-end">
          <NuxtLink to="/forgot-password" class="text-sm text-primary-600 hover:underline">
            Forgot password?
          </NuxtLink>
        </div>

        <UButton type="submit" color="primary" block :loading="loading">Sign in</UButton>
      </form>

      <template #footer>
        <p class="text-sm text-[#888888] text-center">
          New to Booksall?
          <NuxtLink to="/register" class="text-primary-600 hover:underline">Create an account</NuxtLink>
        </p>
      </template>
    </UCard>
  </UContainer>
</template>
