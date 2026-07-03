<script setup>
definePageMeta({ middleware: "auth", layout: "dashboard" });

const api = useApi();
const route = useRoute();
const toast = useToast();
const { data: ticket, error, refresh } = await useAsyncData(
  `ticket-${route.params.id}`,
  () => api(`/api/support-tickets/${route.params.id}/`),
  { server: false, lazy: true }
);
useSeoMeta({ title: () => `${ticket.value?.number || "Ticket"} | Booksall` });

const reply = ref("");
const sending = ref(false);
const closed = computed(() => ["CLOSED", "RESOLVED"].includes(ticket.value?.status));

async function send() {
  if (!reply.value.trim()) return;
  sending.value = true;
  try {
    await api(`/api/support-tickets/${route.params.id}/reply/`, {
      method: "POST",
      body: { body: reply.value },
    });
    reply.value = "";
    await refresh();
  } catch (e) {
    toast.add({ title: "Could not send reply", description: apiErrorMessage(e), color: "red" });
  } finally {
    sending.value = false;
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
    <NuxtLink to="/dashboard/tickets" class="inline-flex items-center gap-1.5 text-sm text-[#888888] hover:text-[#c9ff47] mb-5">
      <UIcon name="i-heroicons-arrow-left" /> All tickets
    </NuxtLink>

    <div v-if="error" class="rounded-2xl border border-red-500/30 bg-red-500/10 p-6 text-red-300">Ticket not found.</div>

    <div v-else-if="ticket">
      <!-- Header -->
      <div class="flex flex-wrap items-start justify-between gap-3 mb-5">
        <div>
          <div class="flex items-center gap-2.5">
            <span class="text-xs font-mono text-[#888]">{{ ticket.number }}</span>
            <span class="text-xs font-bold px-2.5 py-0.5 rounded-full" :class="STATUS[ticket.status]">{{ ticket.status_display }}</span>
            <span class="text-xs text-[#888]">{{ ticket.priority_display }} priority</span>
          </div>
          <h1 class="font-display text-2xl md:text-3xl font-black text-white mt-1.5">{{ ticket.subject }}</h1>
        </div>
      </div>

      <!-- Thread -->
      <div class="space-y-3">
        <!-- Opening message -->
        <div class="rounded-2xl border border-white/[0.08] bg-[#141414] p-4">
          <div class="flex items-center justify-between mb-2">
            <span class="text-sm font-semibold text-[#f0f0f0]">You <span class="text-[#666] font-normal">opened this</span></span>
            <span class="text-xs text-[#888]">{{ fmtDT(ticket.created_at) }}</span>
          </div>
          <div class="bk-prose text-sm text-[#c4c4c4]" v-html="ticket.message" />
        </div>

        <!-- Replies -->
        <div
          v-for="r in ticket.replies"
          :key="r.id"
          class="rounded-2xl border p-4"
          :class="r.is_staff_reply ? 'border-[#c9ff47]/25 bg-[#c9ff47]/[0.04]' : 'border-white/[0.08] bg-[#141414]'"
        >
          <div class="flex items-center justify-between mb-2">
            <span class="text-sm font-semibold" :class="r.is_staff_reply ? 'text-[#c9ff47]' : 'text-[#f0f0f0]'">
              <UIcon v-if="r.is_staff_reply" name="i-heroicons-shield-check" class="align-text-bottom" />
              {{ r.author_name }}
            </span>
            <span class="text-xs text-[#888]">{{ fmtDT(r.created_at) }}</span>
          </div>
          <div class="bk-prose text-sm text-[#c4c4c4]" v-html="r.body" />
        </div>
      </div>

      <!-- Reply box -->
      <div v-if="!closed" class="mt-5 rounded-2xl border border-white/[0.08] bg-[#141414] p-4">
        <RichEditor v-model="reply" placeholder="Write a reply…" />
        <div class="flex justify-end mt-3">
          <button
            class="inline-flex items-center gap-2 rounded-full bg-[#c9ff47] px-6 py-2.5 text-sm font-bold text-black hover:bg-[#d9ff6b] transition-colors disabled:opacity-60"
            :disabled="sending || !reply.trim()"
            @click="send"
          >
            <UIcon v-if="sending" name="i-heroicons-arrow-path" class="animate-spin" />
            {{ sending ? "Sending…" : "Send reply" }}
          </button>
        </div>
      </div>
      <div v-else class="mt-5 rounded-2xl border border-white/[0.08] bg-[#0f0f0f] p-4 text-center text-sm text-[#888]">
        This ticket is {{ ticket.status_display.toLowerCase() }}. Open a new ticket if you need more help.
      </div>
    </div>
  </div>
</template>
