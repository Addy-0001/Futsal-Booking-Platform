<script setup>
const api = useApi();
const auth = useAuthStore();
const toast = useToast();
const { data, pending, refresh } = await useAsyncData("open-matches", () => api("/api/matches/", { query: { ordering: "proposed_start" } }));
useSeoMeta({
    title: "Open matches — find a game | Booksall",
    description: "Find and join open futsal matches near you. No more scrolling Facebook groups.",
});
const createOpen = ref(false);
const saving = ref(false);
const error = ref("");
const form = reactive({
    proposed_start: "", format: "5s", max_players: 10, city: "", skill_level: "", notes: "",
});
const formatOptions = [
    { label: "5-a-side", value: "5s" },
    { label: "7-a-side", value: "7s" },
    { label: "Other", value: "OTHER" },
];
function requireAuth(next = "/matches") {
    if (!auth.isAuthenticated) {
        navigateTo(`/login?next=${encodeURIComponent(next)}`);
        return false;
    }
    return true;
}
async function createMatch() {
    saving.value = true;
    error.value = "";
    try {
        await api("/api/matches/", { method: "POST", body: { ...form } });
        toast.add({ title: "Match posted", color: "green" });
        createOpen.value = false;
        await refresh();
    }
    catch (e) {
        error.value = apiErrorMessage(e, "Could not post match.");
    }
    finally {
        saving.value = false;
    }
}
const acting = ref(null);
async function doAction(m, action) {
    if (!requireAuth())
        return;
    acting.value = m.id;
    try {
        await api(`/api/matches/${m.id}/${action}/`, { method: "POST", body: {} });
        await refresh();
    }
    catch (e) {
        toast.add({ title: "Action failed", description: apiErrorMessage(e), color: "red" });
    }
    finally {
        acting.value = null;
    }
}
function fmt(iso) {
    return new Date(iso).toLocaleString([], {
        weekday: "short", day: "numeric", month: "short", hour: "2-digit", minute: "2-digit",
    });
}
function isMine(m) {
    return m.players?.some((p) => p.user === auth.user?.id && p.status === "JOINED");
}
</script>

<template>
  <UContainer class="py-10">
    <div class="flex items-center justify-between mb-8">
      <div>
        <h1 class="font-display text-3xl md:text-4xl font-bold text-[#f0f0f0]">Open matches</h1>
        <p class="text-[#888888] mt-1">Join a game or host your own.</p>
      </div>
      <UButton color="primary" icon="i-heroicons-plus" @click="requireAuth() && (createOpen = true)">
        Host a match
      </UButton>
    </div>

    <div v-if="pending" class="space-y-3">
      <USkeleton v-for="i in 3" :key="i" class="h-24" />
    </div>

    <div v-else-if="data?.results?.length" class="grid gap-4 sm:grid-cols-2">
      <UCard v-for="m in data.results" :key="m.id">
        <div class="flex items-start justify-between">
          <div>
            <div class="flex items-center gap-2">
              <h3 class="font-semibold text-[#f0f0f0] dark:text-white">{{ m.format }} match</h3>
              <UBadge :color="m.status === 'OPEN' ? 'green' : 'amber'" variant="subtle" size="xs">
                {{ m.status }}
              </UBadge>
            </div>
            <p class="text-sm text-[#888888] mt-1">{{ fmt(m.proposed_start) }}</p>
            <p v-if="m.city" class="text-sm text-[#888888]">{{ m.city }}</p>
            <p v-if="m.notes" class="text-sm text-[#8f8f8f] dark:text-[#565656] mt-2">{{ m.notes }}</p>
          </div>
          <div class="text-right text-sm text-[#888888]">
            <UIcon name="i-heroicons-user-group" /> {{ m.joined_count }}/{{ m.max_players }}
          </div>
        </div>
        <template #footer>
          <div class="flex justify-end gap-2">
            <UButton v-if="m.host === auth.user?.id" color="red" variant="soft" size="sm"
              :loading="acting === m.id" @click="doAction(m, 'cancel')">Cancel</UButton>
            <UButton v-else-if="isMine(m)" color="gray" variant="soft" size="sm"
              :loading="acting === m.id" @click="doAction(m, 'leave')">Leave</UButton>
            <UButton v-else color="primary" size="sm" :disabled="m.status !== 'OPEN'"
              :loading="acting === m.id" @click="doAction(m, 'join')">Join</UButton>
          </div>
        </template>
      </UCard>
    </div>

    <UCard v-else class="text-center py-16">
      <UIcon name="i-heroicons-user-group" class="text-4xl text-[#6b6b6b]" />
      <p class="mt-3 text-[#888888]">No open matches right now. Be the first to host one.</p>
    </UCard>

    <UModal v-model="createOpen">
      <UCard>
        <template #header><h3 class="font-semibold">Host a match</h3></template>
        <div class="space-y-4">
          <UAlert v-if="error" color="red" variant="soft" :title="error" />
          <UFormGroup label="When" required><UInput v-model="form.proposed_start" type="datetime-local" /></UFormGroup>
          <div class="flex gap-3">
            <UFormGroup label="Format" class="flex-1"><USelect v-model="form.format" :options="formatOptions" /></UFormGroup>
            <UFormGroup label="Max players" class="flex-1"><UInput v-model.number="form.max_players" type="number" /></UFormGroup>
          </div>
          <UFormGroup label="City"><UInput v-model="form.city" /></UFormGroup>
          <UFormGroup label="Skill level"><UInput v-model="form.skill_level" placeholder="Casual / Intermediate / Competitive" /></UFormGroup>
          <UFormGroup label="Notes"><UTextarea v-model="form.notes" :rows="2" /></UFormGroup>
        </div>
        <template #footer>
          <div class="flex justify-end gap-2">
            <UButton color="gray" variant="soft" @click="createOpen = false">Cancel</UButton>
            <UButton color="primary" :loading="saving" @click="createMatch">Post match</UButton>
          </div>
        </template>
      </UCard>
    </UModal>
  </UContainer>
</template>
