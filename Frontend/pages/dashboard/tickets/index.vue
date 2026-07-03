<script setup>
definePageMeta({ middleware: "auth", layout: "dashboard" });
useSeoMeta({ title: "Support | Booksall" });

const api = useApi();
const toast = useToast();
const { data, pending, refresh } = await useAsyncData(
  "my-tickets",
  () => api("/api/support-tickets/", { query: { ordering: "-last_reply_at" } }),
  { server: false, lazy: true }
);
const tickets = computed(() => data.value?.results || []);

const showNew = ref(false);
const saving = ref(false);
const form = reactive({ subject: "", type: "SUPPORT", priority: "MEDIUM", message: "" });
const types = [
  { label: "Support request", value: "SUPPORT" },
  { label: "Billing", value: "BILLING" },
  { label: "Bug report", value: "BUG" },
  { label: "Feedback", value: "FEEDBACK" },
];
const priorities = [
  { label: "Low", value: "LOW" }, { label: "Medium", value: "MEDIUM" },
  { label: "High", value: "HIGH" }, { label: "Urgent", value: "URGENT" },
];

async function create() {
  if (!form.subject || !form.message) return;
  saving.value = true;
  try {
    const t = await api("/api/support-tickets/", { method: "POST", body: { ...form } });
    toast.add({ title: "Ticket opened", description: t.number, color: "green" });
    showNew.value = false;
    Object.assign(form, { subject: "", type: "SUPPORT", priority: "MEDIUM", message: "" });
    await refresh();
    if (t.id) navigateTo(`/dashboard/tickets/${t.id}`);
  } catch (e) {
    toast.add({ title: "Could not open ticket", description: apiErrorMessage(e), color: "red" });
  } finally {
    saving.value = false;
  }
}

const STATUS = {
  OPEN: "bg-[#c9ff47]/15 text-[#c9ff47]", ANSWERED: "bg-[#22c55e]/15 text-[#22c55e]",
  CUSTOMER_REPLY: "bg-[#f5c842]/15 text-[#f5c842]", IN_PROGRESS: "bg-[#4aa3ff]/15 text-[#4aa3ff]",
  RESOLVED: "bg-[#22c55e]/15 text-[#22c55e]", CLOSED: "bg-[#1e1e1e] text-[#888]",
};
const fmtDT = (d) => new Date(d).toLocaleString([], { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" });
</script>

<template>
  <div>
    <div class="flex items-center justify-between gap-3 mb-6">
      <div>
        <h1 class="font-display text-3xl md:text-4xl font-black uppercase tracking-tight text-[#f0f0f0]">Support</h1>
        <p class="text-[#888888] mt-1">Your tickets and conversations with our team.</p>
      </div>
      <button class="inline-flex items-center gap-1.5 rounded-full bg-[#c9ff47] px-5 py-2.5 text-sm font-bold text-black hover:bg-[#d9ff6b] transition-colors shrink-0" @click="showNew = true">
        <UIcon name="i-heroicons-plus" /> New ticket
      </button>
    </div>

    <!-- New ticket form -->
    <div v-if="showNew" class="mb-6 rounded-2xl border border-white/[0.08] bg-[#141414] p-5">
      <div class="flex items-center justify-between mb-4">
        <h2 class="font-display font-bold text-white">Open a new ticket</h2>
        <button class="text-[#666] hover:text-white" @click="showNew = false"><UIcon name="i-heroicons-x-mark" /></button>
      </div>
      <div class="space-y-4">
        <UFormGroup label="Subject"><UInput v-model="form.subject" placeholder="Brief summary" /></UFormGroup>
        <div class="grid sm:grid-cols-2 gap-4">
          <UFormGroup label="Type"><USelect v-model="form.type" :options="types" /></UFormGroup>
          <UFormGroup label="Priority"><USelect v-model="form.priority" :options="priorities" /></UFormGroup>
        </div>
        <UFormGroup label="Message"><RichEditor v-model="form.message" placeholder="Describe your issue…" /></UFormGroup>
        <div class="flex justify-end gap-2">
          <UButton color="gray" variant="soft" @click="showNew = false">Cancel</UButton>
          <UButton color="primary" :loading="saving" @click="create">Open ticket</UButton>
        </div>
      </div>
    </div>

    <div v-if="pending" class="space-y-3">
      <USkeleton v-for="i in 3" :key="i" class="h-20 rounded-2xl" />
    </div>

    <div v-else-if="tickets.length" class="space-y-3">
      <NuxtLink
        v-for="t in tickets"
        :key="t.id"
        :to="`/dashboard/tickets/${t.id}`"
        class="group flex items-center justify-between gap-4 rounded-2xl border border-white/[0.08] bg-[#141414] p-4 hover:border-[#c9ff47]/40 transition-colors"
      >
        <div class="min-w-0">
          <div class="flex items-center gap-2.5">
            <span class="text-xs font-mono text-[#888]">{{ t.number }}</span>
            <span class="text-xs font-bold px-2.5 py-0.5 rounded-full" :class="STATUS[t.status]">{{ t.status_display }}</span>
          </div>
          <p class="font-semibold text-[#f0f0f0] truncate mt-1 group-hover:text-[#c9ff47] transition-colors">{{ t.subject }}</p>
          <p class="text-xs text-[#888888] mt-0.5">Last activity {{ fmtDT(t.last_reply_at) }}</p>
        </div>
        <UIcon name="i-heroicons-chevron-right" class="text-[#666] group-hover:text-[#c9ff47] transition-colors shrink-0" />
      </NuxtLink>
    </div>

    <div v-else class="rounded-2xl border border-white/[0.08] bg-[#141414] text-center py-16">
      <UIcon name="i-heroicons-lifebuoy" class="text-4xl text-[#444]" />
      <p class="mt-3 text-[#888888]">No tickets yet.</p>
      <p class="text-sm text-[#666] mt-1">Open one and our team will get back to you.</p>
    </div>
  </div>
</template>
