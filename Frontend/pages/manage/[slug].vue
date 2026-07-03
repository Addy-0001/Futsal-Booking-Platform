<script setup>
definePageMeta({ middleware: "auth", layout: "dashboard" });
const api = useApi();
const toast = useToast();
const route = useRoute();
const slug = route.params.slug;
const WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
const weekdayOptions = WEEKDAYS.map((label, value) => ({ label, value }));
const surfaceOptions = [
    { label: "Artificial turf", value: "ARTIFICIAL" },
    { label: "Natural grass", value: "NATURAL" },
    { label: "Indoor", value: "INDOOR" },
];
const { data: venue, refresh: refreshVenue } = await useAsyncData(() => `manage-venue-${slug}`, () => api(`/api/futsals/${slug}/`), { server: false });
useSeoMeta({ title: () => `Manage ${venue.value?.name ?? "venue"} | Booksall` });
const courtIds = computed(() => new Set((venue.value?.courts || []).map((c) => c.id)));
const { data: rulesData, refresh: refreshRules } = await useAsyncData(() => `manage-rules-${slug}`, () => api("/api/price-rules/", { query: { page_size: 100 } }), { server: false });
const rulesByCourt = computed(() => {
    const map = {};
    for (const r of rulesData.value?.results || []) {
        if (courtIds.value.has(r.court))
            (map[r.court] ||= []).push(r);
    }
    return map;
});
// ---- Court modal ----
const courtModal = ref(false);
const courtForm = reactive({ name: "", surface_type: "ARTIFICIAL", default_price: "1000" });
async function addCourt() {
    try {
        await api("/api/courts/", { method: "POST", body: { futsal: venue.value.id, ...courtForm } });
        toast.add({ title: "Court added", color: "green" });
        courtModal.value = false;
        Object.assign(courtForm, { name: "", surface_type: "ARTIFICIAL", default_price: "1000" });
        await refreshVenue();
    }
    catch (e) {
        toast.add({ title: "Could not add court", description: apiErrorMessage(e), color: "red" });
    }
}
// ---- Operating hours modal ----
const hoursModal = ref(false);
const hoursForm = reactive({ court: "", weekday: 0, open_time: "06:00", close_time: "22:00" });
function openHours(courtId) {
    hoursForm.court = courtId;
    hoursModal.value = true;
}
async function addHours() {
    try {
        await api("/api/operating-hours/", { method: "POST", body: { ...hoursForm } });
        toast.add({ title: "Hours added", color: "green" });
        hoursModal.value = false;
        await refreshVenue();
    }
    catch (e) {
        toast.add({ title: "Could not add hours", description: apiErrorMessage(e), color: "red" });
    }
}
// ---- Price rule modal ----
const ruleModal = ref(false);
const ruleForm = reactive({
    court: "", name: "", start_time: "18:00", end_time: "22:00",
    price: "1500", priority: 0, days: [0, 1, 2, 3, 4, 5, 6],
});
function openRule(courtId) {
    ruleForm.court = courtId;
    ruleModal.value = true;
}
function maskFromDays(days) {
    return days.reduce((m, d) => m | (1 << d), 0);
}
async function addRule() {
    try {
        await api("/api/price-rules/", {
            method: "POST",
            body: {
                court: ruleForm.court, name: ruleForm.name,
                start_time: ruleForm.start_time, end_time: ruleForm.end_time,
                price: ruleForm.price, priority: ruleForm.priority,
                days_mask: maskFromDays(ruleForm.days),
            },
        });
        toast.add({ title: "Price rule added", color: "green" });
        ruleModal.value = false;
        Object.assign(ruleForm, { name: "", start_time: "18:00", end_time: "22:00", price: "1500", priority: 0 });
        await refreshRules();
    }
    catch (e) {
        toast.add({ title: "Could not add rule", description: apiErrorMessage(e), color: "red" });
    }
}
// ---- Image uploads (multipart) ----
async function uploadFutsalImage(e) {
    const input = e.target;
    const file = input.files?.[0];
    if (!file)
        return;
    const fd = new FormData();
    fd.append("futsal", venue.value.id);
    fd.append("image", file);
    try {
        await api("/api/futsal-images/", { method: "POST", body: fd });
        toast.add({ title: "Photo uploaded", color: "green" });
        await refreshVenue();
    }
    catch (err) {
        toast.add({ title: "Upload failed", description: apiErrorMessage(err), color: "red" });
    }
    finally {
        input.value = "";
    }
}
async function uploadCourtImage(e, courtId) {
    const input = e.target;
    const file = input.files?.[0];
    if (!file)
        return;
    const fd = new FormData();
    fd.append("court", courtId);
    fd.append("image", file);
    try {
        await api("/api/court-images/", { method: "POST", body: fd });
        toast.add({ title: "Photo uploaded", color: "green" });
        await refreshVenue();
    }
    catch (err) {
        toast.add({ title: "Upload failed", description: apiErrorMessage(err), color: "red" });
    }
    finally {
        input.value = "";
    }
}
</script>

<template>
  <div v-if="venue">
    <nav class="text-sm text-[#888888] mb-2">
      <NuxtLink to="/manage" class="hover:text-primary-600">Manage</NuxtLink>
      <span class="mx-1">/</span><span>{{ venue.name }}</span>
    </nav>
    <div class="flex items-center justify-between mb-6">
      <h1 class="font-display text-3xl font-bold text-[#f0f0f0]">{{ venue.name }}</h1>
      <div class="flex gap-2">
        <label class="inline-flex items-center gap-1 px-3 py-1.5 text-sm rounded-md border border-white/[0.08] dark:border-white/[0.10] cursor-pointer hover:bg-[#111111] dark:hover:bg-[#1a1a1a]">
          <UIcon name="i-heroicons-photo" />
          Add venue photo
          <input type="file" accept="image/*" class="hidden" @change="uploadFutsalImage" />
        </label>
        <UButton color="primary" icon="i-heroicons-plus" @click="courtModal = true">Add court</UButton>
      </div>
    </div>

    <div v-if="venue.images?.length" class="flex gap-2 overflow-x-auto mb-6">
      <img v-for="img in venue.images" :key="img.id" :src="img.image" :alt="img.caption || venue.name"
        class="h-24 w-32 object-cover rounded-md flex-shrink-0" loading="lazy" />
    </div>

    <div v-if="venue.courts?.length" class="space-y-5">
      <UCard v-for="court in venue.courts" :key="court.id">
        <div class="flex items-start justify-between">
          <div>
            <h3 class="font-semibold text-[#f0f0f0] dark:text-white">{{ court.name }}</h3>
            <p class="text-sm text-[#888888]">{{ court.surface_type }} · default NPR {{ court.default_price }}</p>
          </div>
          <label class="inline-flex items-center gap-1 px-2 py-1 text-xs rounded-md border border-white/[0.08] dark:border-white/[0.10] cursor-pointer hover:bg-[#111111] dark:hover:bg-[#1a1a1a]">
            <UIcon name="i-heroicons-photo" /> Add photo
            <input type="file" accept="image/*" class="hidden" @change="(e) => uploadCourtImage(e, court.id)" />
          </label>
        </div>

        <div v-if="court.images?.length" class="mt-3 flex gap-2 overflow-x-auto">
          <img v-for="img in court.images" :key="img.id" :src="img.image" :alt="img.caption || court.name"
            class="h-16 w-24 object-cover rounded flex-shrink-0" loading="lazy" />
        </div>

        <!-- Operating hours -->
        <div class="mt-4">
          <div class="flex items-center justify-between mb-2">
            <p class="text-xs font-medium uppercase text-[#6b6b6b]">Operating hours</p>
            <UButton size="2xs" color="gray" variant="soft" @click="openHours(court.id)">Add hours</UButton>
          </div>
          <ul v-if="court.operating_hours?.length" class="text-sm text-[#8f8f8f] dark:text-[#565656] grid grid-cols-2 sm:grid-cols-4 gap-1">
            <li v-for="h in court.operating_hours" :key="h.id">
              {{ WEEKDAYS[h.weekday] }} {{ h.open_time.slice(0, 5) }}–{{ h.close_time.slice(0, 5) }}
            </li>
          </ul>
          <p v-else class="text-sm text-[#6b6b6b]">No hours set — court won't be bookable.</p>
        </div>

        <!-- Price rules -->
        <div class="mt-4 border-t border-white/[0.06] dark:border-white/[0.08] pt-3">
          <div class="flex items-center justify-between mb-2">
            <p class="text-xs font-medium uppercase text-[#6b6b6b]">Dynamic pricing</p>
            <UButton size="2xs" color="gray" variant="soft" @click="openRule(court.id)">Add rule</UButton>
          </div>
          <ul v-if="rulesByCourt[court.id]?.length" class="text-sm space-y-1">
            <li v-for="r in rulesByCourt[court.id]" :key="r.id" class="flex justify-between">
              <span>{{ r.name }} · {{ r.start_time.slice(0, 5) }}–{{ r.end_time.slice(0, 5) }}
                <span class="text-[#6b6b6b]">({{ r.days.map((d) => WEEKDAYS[d]).join(", ") }})</span>
              </span>
              <span class="font-medium">NPR {{ r.price }}</span>
            </li>
          </ul>
          <p v-else class="text-sm text-[#6b6b6b]">Falls back to default price.</p>
        </div>
      </UCard>
    </div>
    <UCard v-else class="text-center py-12">
      <p class="text-[#888888]">No courts yet. Add one to start taking bookings.</p>
    </UCard>

    <!-- Add court modal -->
    <UModal v-model="courtModal">
      <UCard>
        <template #header><h3 class="font-semibold">Add court</h3></template>
        <div class="space-y-4">
          <UFormGroup label="Name" required><UInput v-model="courtForm.name" placeholder="Court A" /></UFormGroup>
          <UFormGroup label="Surface"><USelect v-model="courtForm.surface_type" :options="surfaceOptions" /></UFormGroup>
          <UFormGroup label="Default price (NPR)"><UInput v-model="courtForm.default_price" type="number" /></UFormGroup>
        </div>
        <template #footer>
          <div class="flex justify-end gap-2">
            <UButton color="gray" variant="soft" @click="courtModal = false">Cancel</UButton>
            <UButton color="primary" @click="addCourt">Add court</UButton>
          </div>
        </template>
      </UCard>
    </UModal>

    <!-- Add hours modal -->
    <UModal v-model="hoursModal">
      <UCard>
        <template #header><h3 class="font-semibold">Add operating hours</h3></template>
        <div class="space-y-4">
          <UFormGroup label="Weekday"><USelect v-model="hoursForm.weekday" :options="weekdayOptions" /></UFormGroup>
          <div class="flex gap-3">
            <UFormGroup label="Opens" class="flex-1"><UInput v-model="hoursForm.open_time" type="time" /></UFormGroup>
            <UFormGroup label="Closes" class="flex-1"><UInput v-model="hoursForm.close_time" type="time" /></UFormGroup>
          </div>
        </div>
        <template #footer>
          <div class="flex justify-end gap-2">
            <UButton color="gray" variant="soft" @click="hoursModal = false">Cancel</UButton>
            <UButton color="primary" @click="addHours">Add</UButton>
          </div>
        </template>
      </UCard>
    </UModal>

    <!-- Add price rule modal -->
    <UModal v-model="ruleModal">
      <UCard>
        <template #header><h3 class="font-semibold">Add price rule</h3></template>
        <div class="space-y-4">
          <UFormGroup label="Name" required><UInput v-model="ruleForm.name" placeholder="Night / Weekend surge" /></UFormGroup>
          <div class="flex gap-3">
            <UFormGroup label="From" class="flex-1"><UInput v-model="ruleForm.start_time" type="time" /></UFormGroup>
            <UFormGroup label="To" class="flex-1"><UInput v-model="ruleForm.end_time" type="time" /></UFormGroup>
          </div>
          <div class="flex gap-3">
            <UFormGroup label="Price (NPR)" class="flex-1"><UInput v-model="ruleForm.price" type="number" /></UFormGroup>
            <UFormGroup label="Priority" class="flex-1" hint="higher wins"><UInput v-model.number="ruleForm.priority" type="number" /></UFormGroup>
          </div>
          <UFormGroup label="Days">
            <div class="flex flex-wrap gap-3">
              <UCheckbox v-for="(label, d) in WEEKDAYS" :key="d" v-model="ruleForm.days" :value="d" :label="label" />
            </div>
          </UFormGroup>
        </div>
        <template #footer>
          <div class="flex justify-end gap-2">
            <UButton color="gray" variant="soft" @click="ruleModal = false">Cancel</UButton>
            <UButton color="primary" @click="addRule">Add rule</UButton>
          </div>
        </template>
      </UCard>
    </UModal>
  </div>
</template>
