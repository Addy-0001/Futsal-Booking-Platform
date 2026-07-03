<script setup>
const api = useApi();
const auth = useAuthStore();
const toast = useToast();
const { data, pending, refresh } = await useAsyncData("teams", () => api("/api/teams/"));
useSeoMeta({
    title: "Teams | Booksall",
    description: "Browse futsal teams, build your squad, and challenge rivals.",
});
const createOpen = ref(false);
const saving = ref(false);
const error = ref("");
const form = reactive({ name: "", description: "" });
async function createTeam() {
    if (!auth.isAuthenticated) {
        navigateTo("/login?next=/teams");
        return;
    }
    saving.value = true;
    error.value = "";
    try {
        const team = await api("/api/teams/", { method: "POST", body: { ...form } });
        toast.add({ title: "Team created", color: "green" });
        createOpen.value = false;
        await navigateTo(`/teams/${team.slug}`);
    }
    catch (e) {
        error.value = apiErrorMessage(e, "Could not create team.");
    }
    finally {
        saving.value = false;
    }
}
</script>

<template>
  <UContainer class="py-10">
    <div class="flex items-center justify-between mb-8">
      <div>
        <h1 class="font-display text-3xl md:text-4xl font-bold text-[#f0f0f0]">Teams</h1>
        <p class="text-[#888888] mt-1">Build a squad and challenge other teams.</p>
      </div>
      <UButton color="primary" icon="i-heroicons-plus"
        @click="auth.isAuthenticated ? (createOpen = true) : navigateTo('/login?next=/teams')">
        Create team
      </UButton>
    </div>

    <div v-if="pending" class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      <USkeleton v-for="i in 6" :key="i" class="h-28" />
    </div>

    <div v-else-if="data?.results?.length" class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      <TeamCard v-for="t in data.results" :key="t.id" :team="t" />
    </div>

    <UCard v-else class="text-center py-16">
      <UIcon name="i-heroicons-shield-check" class="text-4xl text-[#6b6b6b]" />
      <p class="mt-3 text-[#888888]">No teams yet. Create the first one.</p>
    </UCard>

    <UModal v-model="createOpen">
      <UCard>
        <template #header><h3 class="font-semibold">Create a team</h3></template>
        <div class="space-y-4">
          <UAlert v-if="error" color="red" variant="soft" :title="error" />
          <UFormGroup label="Team name" required><UInput v-model="form.name" /></UFormGroup>
          <UFormGroup label="Description"><UTextarea v-model="form.description" :rows="3" /></UFormGroup>
        </div>
        <template #footer>
          <div class="flex justify-end gap-2">
            <UButton color="gray" variant="soft" @click="createOpen = false">Cancel</UButton>
            <UButton color="primary" :loading="saving" @click="createTeam">Create</UButton>
          </div>
        </template>
      </UCard>
    </UModal>
  </UContainer>
</template>
