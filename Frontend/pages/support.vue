<script setup>
useSeoMeta({
    title: "Support & feedback | Booksall",
    description: "Contact Booksall support, report a bug, or send feedback.",
});
const api = useApi();
const auth = useAuthStore();
const route = useRoute();
const toast = useToast();
const form = reactive({
    type: "SUPPORT",
    email: "",
    subject: "",
    message: "",
});
const typeOptions = [
    { label: "Support request", value: "SUPPORT" },
    { label: "Bug report", value: "BUG" },
    { label: "Feedback", value: "FEEDBACK" },
];
const loading = ref(false);
const error = ref("");
const done = ref(false);
async function submit() {
    loading.value = true;
    error.value = "";
    try {
        await api("/api/support-tickets/", {
            method: "POST",
            body: {
                type: form.type,
                email: auth.user?.email || form.email,
                subject: form.subject,
                message: form.message,
                url: route.query.from || "",
            },
        });
        done.value = true;
        toast.add({ title: "Thanks — we got your message.", color: "green" });
    }
    catch (e) {
        error.value = apiErrorMessage(e, "Could not send your message.");
    }
    finally {
        loading.value = false;
    }
}
</script>

<template>
  <UContainer class="py-12 max-w-lg">
    <h1 class="font-display text-3xl font-bold text-[#f0f0f0] mb-2">Support & feedback</h1>
    <p class="text-[#888888] mb-8">Have a question, found a bug, or want to suggest something? Tell us.</p>

    <UCard v-if="!done">
      <form class="space-y-4" @submit.prevent="submit">
        <UAlert v-if="error" color="red" variant="soft" :title="error" />
        <UFormGroup label="Type"><USelect v-model="form.type" :options="typeOptions" /></UFormGroup>
        <UFormGroup v-if="!auth.isAuthenticated" label="Your email" required>
          <UInput v-model="form.email" type="email" />
        </UFormGroup>
        <UFormGroup label="Subject" required><UInput v-model="form.subject" /></UFormGroup>
        <UFormGroup label="Message" required><UTextarea v-model="form.message" :rows="5" /></UFormGroup>
        <UButton type="submit" color="primary" block :loading="loading">Send</UButton>
      </form>
    </UCard>

    <UCard v-else class="text-center">
      <UIcon name="i-heroicons-check-circle" class="text-5xl text-green-500" />
      <p class="mt-3 text-[#8f8f8f] dark:text-[#565656]">Thanks for reaching out. We'll get back to you.</p>
      <UButton to="/" color="primary" variant="soft" class="mt-5">Back to home</UButton>
    </UCard>
  </UContainer>
</template>
