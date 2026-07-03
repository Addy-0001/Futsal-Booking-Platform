<script setup>
const api = useApi();
const auth = useAuthStore();
const toast = useToast();
const route = useRoute();
const slug = route.params.slug;
const { data: team, error, refresh: refreshTeam } = await useAsyncData(() => `team-${slug}`, () => api(`/api/teams/${slug}/`));
if (error.value || !team.value) {
    throw createError({ statusCode: 404, statusMessage: "Team not found", fatal: true });
}
useSeoMeta({
    title: () => `${team.value?.name} | Booksall Teams`,
    description: () => team.value?.description || `${team.value?.name} on Booksall.`,
});
const isCaptain = computed(() => auth.user && team.value?.captain === auth.user.id);
const isMember = computed(() => team.value?.members?.some((m) => m.user === auth.user?.id && m.status === "ACTIVE"));
// Challenges involving this team (visible to members/captains; empty otherwise).
const { data: challengeData, refresh: refreshChallenges } = await useAsyncData(() => `team-challenges-${slug}`, () => api("/api/challenges/", { query: { page_size: 100 } }), { server: false });
const challenges = computed(() => (challengeData.value?.results || []).filter((c) => c.challenger_team === team.value?.id || c.opponent_team === team.value?.id));
// Teams to challenge (everyone but this one).
const { data: allTeams } = await useAsyncData(() => `all-teams-${slug}`, () => api("/api/teams/", { query: { page_size: 100 } }), { server: false });
const opponentOptions = computed(() => (allTeams.value?.results || [])
    .filter((t) => t.id !== team.value?.id)
    .map((t) => ({ label: t.name, value: t.id })));
function fmt(iso) {
    return new Date(iso).toLocaleString([], {
        weekday: "short", day: "numeric", month: "short", hour: "2-digit", minute: "2-digit",
    });
}
// ---- Membership actions ----
const inviteOpen = ref(false);
const inviteEmail = ref("");
async function invite() {
    try {
        await api(`/api/teams/${slug}/invite/`, { method: "POST", body: { email: inviteEmail.value } });
        toast.add({ title: "Invite sent", color: "green" });
        inviteOpen.value = false;
        inviteEmail.value = "";
        await refreshTeam();
    }
    catch (e) {
        toast.add({ title: "Could not invite", description: apiErrorMessage(e), color: "red" });
    }
}
async function acceptInvite() {
    try {
        await api(`/api/teams/${slug}/accept-invite/`, { method: "POST", body: {} });
        toast.add({ title: "You joined the team", color: "green" });
        await refreshTeam();
    }
    catch (e) {
        toast.add({ title: "No pending invite", description: apiErrorMessage(e), color: "red" });
    }
}
async function leave() {
    try {
        await api(`/api/teams/${slug}/leave/`, { method: "POST", body: {} });
        toast.add({ title: "You left the team", color: "green" });
        await refreshTeam();
    }
    catch (e) {
        toast.add({ title: "Could not leave", description: apiErrorMessage(e), color: "red" });
    }
}
// ---- Challenge actions ----
const challengeOpen = ref(false);
const challengeForm = reactive({ opponent_team: "", proposed_start: "" });
async function propose() {
    try {
        await api("/api/challenges/", {
            method: "POST",
            body: {
                challenger_team: team.value.id,
                opponent_team: challengeForm.opponent_team,
                proposed_start: challengeForm.proposed_start,
            },
        });
        toast.add({ title: "Challenge sent", color: "green" });
        challengeOpen.value = false;
        await refreshChallenges();
    }
    catch (e) {
        toast.add({ title: "Could not send challenge", description: apiErrorMessage(e), color: "red" });
    }
}
async function respond(c, action) {
    try {
        await api(`/api/challenges/${c.id}/${action}/`, { method: "POST", body: {} });
        await refreshChallenges();
    }
    catch (e) {
        toast.add({ title: "Action failed", description: apiErrorMessage(e), color: "red" });
    }
}
const resultOpen = ref(false);
const resultForm = reactive({ id: "", challenger_score: 0, opponent_score: 0 });
function openResult(c) {
    resultForm.id = c.id;
    resultForm.challenger_score = 0;
    resultForm.opponent_score = 0;
    resultOpen.value = true;
}
async function saveResult() {
    try {
        await api(`/api/challenges/${resultForm.id}/result/`, {
            method: "POST",
            body: { challenger_score: resultForm.challenger_score, opponent_score: resultForm.opponent_score },
        });
        toast.add({ title: "Result recorded", color: "green" });
        resultOpen.value = false;
        await refreshChallenges();
    }
    catch (e) {
        toast.add({ title: "Could not save result", description: apiErrorMessage(e), color: "red" });
    }
}
const challengeColor = {
    PROPOSED: "amber", ACCEPTED: "green", DECLINED: "red",
    SCHEDULED: "blue", PLAYED: "gray", CANCELLED: "gray",
};
</script>

<template>
  <UContainer v-if="team" class="py-10">
    <nav class="text-sm text-[#888888] mb-2">
      <NuxtLink to="/teams" class="hover:text-primary-600">Teams</NuxtLink>
      <span class="mx-1">/</span><span>{{ team.name }}</span>
    </nav>

    <div class="flex items-center justify-between mb-6">
      <div class="flex items-center gap-3">
        <UAvatar :src="team.logo || undefined" :alt="team.name" size="lg" />
        <div>
          <h1 class="font-display text-2xl font-bold text-[#f0f0f0]">{{ team.name }}</h1>
          <p class="text-sm text-[#888888]">Captain: {{ team.captain_name }}</p>
        </div>
      </div>
      <ClientOnly>
        <div class="flex gap-2">
          <UButton v-if="isCaptain" color="primary" size="sm" @click="inviteOpen = true">Invite</UButton>
          <UButton v-if="isCaptain" color="gray" variant="soft" size="sm" @click="challengeOpen = true">Challenge</UButton>
          <UButton v-if="auth.isAuthenticated && !isMember && !isCaptain" color="primary" variant="soft" size="sm" @click="acceptInvite">Accept invite</UButton>
          <UButton v-if="isMember && !isCaptain" color="red" variant="soft" size="sm" @click="leave">Leave</UButton>
        </div>
      </ClientOnly>
    </div>

    <p v-if="team.description" class="text-[#c4c4c4] dark:text-[#565656] mb-8 max-w-3xl">{{ team.description }}</p>

    <section class="mb-10">
      <h2 class="font-display text-lg font-semibold text-[#f0f0f0] mb-3">Squad</h2>
      <div class="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
        <div v-for="m in team.members" :key="m.id" class="flex items-center gap-2 p-2 rounded-lg border border-white/[0.06] dark:border-white/[0.08]">
          <UAvatar :alt="m.user_name" size="xs" />
          <span class="text-sm">{{ m.user_name || m.user_email }}</span>
          <UBadge v-if="m.role === 'CAPTAIN'" color="primary" variant="subtle" size="xs">Captain</UBadge>
        </div>
      </div>
    </section>

    <ClientOnly>
      <section v-if="challenges.length">
        <h2 class="font-display text-lg font-semibold text-[#f0f0f0] mb-3">Challenges</h2>
        <div class="space-y-3">
          <UCard v-for="c in challenges" :key="c.id">
            <div class="flex items-center justify-between gap-3">
              <div>
                <p class="font-medium">
                  {{ c.challenger_name }} <span class="text-[#6b6b6b]">vs</span> {{ c.opponent_name }}
                  <UBadge :color="challengeColor[c.status]" variant="subtle" size="xs" class="ml-1">{{ c.status }}</UBadge>
                </p>
                <p class="text-sm text-[#888888]">{{ fmt(c.proposed_start) }}</p>
                <p v-if="c.status === 'PLAYED'" class="text-sm font-medium mt-1">
                  Final: {{ c.challenger_score }} – {{ c.opponent_score }}
                </p>
              </div>
              <div class="flex gap-2">
                <template v-if="isCaptain && c.status === 'PROPOSED' && c.opponent_team === team.id">
                  <UButton color="green" size="xs" @click="respond(c, 'accept')">Accept</UButton>
                  <UButton color="red" variant="soft" size="xs" @click="respond(c, 'decline')">Decline</UButton>
                </template>
                <UButton v-if="isCaptain && ['ACCEPTED', 'SCHEDULED'].includes(c.status)" color="primary" size="xs" @click="openResult(c)">
                  Record result
                </UButton>
                <UButton v-if="isCaptain && c.status === 'PROPOSED' && c.challenger_team === team.id" color="gray" variant="soft" size="xs" @click="respond(c, 'cancel')">
                  Cancel
                </UButton>
              </div>
            </div>
          </UCard>
        </div>
      </section>
    </ClientOnly>

    <!-- Invite modal -->
    <UModal v-model="inviteOpen">
      <UCard>
        <template #header><h3 class="font-semibold">Invite a player</h3></template>
        <UFormGroup label="Player email" required>
          <UInput v-model="inviteEmail" type="email" placeholder="player@example.com" />
        </UFormGroup>
        <template #footer>
          <div class="flex justify-end gap-2">
            <UButton color="gray" variant="soft" @click="inviteOpen = false">Cancel</UButton>
            <UButton color="primary" @click="invite">Send invite</UButton>
          </div>
        </template>
      </UCard>
    </UModal>

    <!-- Challenge modal -->
    <UModal v-model="challengeOpen">
      <UCard>
        <template #header><h3 class="font-semibold">Challenge a team</h3></template>
        <div class="space-y-4">
          <UFormGroup label="Opponent" required>
            <USelect v-model="challengeForm.opponent_team" :options="opponentOptions" placeholder="Select a team" />
          </UFormGroup>
          <UFormGroup label="Proposed time" required>
            <UInput v-model="challengeForm.proposed_start" type="datetime-local" />
          </UFormGroup>
        </div>
        <template #footer>
          <div class="flex justify-end gap-2">
            <UButton color="gray" variant="soft" @click="challengeOpen = false">Cancel</UButton>
            <UButton color="primary" @click="propose">Send challenge</UButton>
          </div>
        </template>
      </UCard>
    </UModal>

    <!-- Result modal -->
    <UModal v-model="resultOpen">
      <UCard>
        <template #header><h3 class="font-semibold">Record result</h3></template>
        <div class="flex gap-3">
          <UFormGroup label="Challenger score" class="flex-1"><UInput v-model.number="resultForm.challenger_score" type="number" /></UFormGroup>
          <UFormGroup label="Opponent score" class="flex-1"><UInput v-model.number="resultForm.opponent_score" type="number" /></UFormGroup>
        </div>
        <template #footer>
          <div class="flex justify-end gap-2">
            <UButton color="gray" variant="soft" @click="resultOpen = false">Cancel</UButton>
            <UButton color="primary" @click="saveResult">Save</UButton>
          </div>
        </template>
      </UCard>
    </UModal>
  </UContainer>
</template>
