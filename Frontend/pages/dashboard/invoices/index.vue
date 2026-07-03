<script setup>
definePageMeta({ middleware: "auth", layout: "dashboard" });
useSeoMeta({ title: "My Invoices | Booksall" });

const api = useApi();
const { data, pending } = await useAsyncData(
  "my-invoices",
  () => api("/api/invoices/", { query: { ordering: "-created_at" } }),
  { server: false, lazy: true }
);

const invoices = computed(() => data.value?.results || []);
const outstanding = computed(() =>
  invoices.value
    .filter((i) => ["UNPAID", "PARTIAL", "OVERDUE"].includes(i.status))
    .reduce((s, i) => s + Number(i.balance), 0)
);

const STATUS = {
  DRAFT: { c: "bg-[#1e1e1e] text-[#bdbdbd]" },
  UNPAID: { c: "bg-[#f5c842]/15 text-[#f5c842]" },
  PARTIAL: { c: "bg-[#4aa3ff]/15 text-[#4aa3ff]" },
  PAID: { c: "bg-[#22c55e]/15 text-[#22c55e]" },
  OVERDUE: { c: "bg-red-500/15 text-red-400" },
  CANCELLED: { c: "bg-[#1e1e1e] text-[#888]" },
  REFUNDED: { c: "bg-[#a855f7]/15 text-[#c99bff]" },
};
const fmtDate = (d) => (d ? new Date(d).toLocaleDateString([], { day: "numeric", month: "short", year: "numeric" }) : "—");
</script>

<template>
  <div>
    <h1 class="font-display text-3xl md:text-4xl font-black uppercase tracking-tight text-[#f0f0f0] mb-1">Invoices</h1>
    <p class="text-[#888888] mb-6">Your booking invoices and payment history.</p>

    <div v-if="outstanding > 0" class="mb-6 inline-flex items-center gap-3 rounded-2xl border border-[#f5c842]/30 bg-[#f5c842]/[0.06] px-5 py-3">
      <UIcon name="i-heroicons-exclamation-circle" class="text-[#f5c842] text-xl" />
      <span class="text-sm text-[#e5e5e5]">Outstanding balance: <b class="text-[#f5c842]">NPR {{ outstanding.toLocaleString() }}</b></span>
    </div>

    <div v-if="pending" class="space-y-3">
      <USkeleton v-for="i in 3" :key="i" class="h-20 rounded-2xl" />
    </div>

    <div v-else-if="invoices.length" class="space-y-3">
      <NuxtLink
        v-for="inv in invoices"
        :key="inv.id"
        :to="`/dashboard/invoices/${inv.id}`"
        class="group flex items-center justify-between gap-4 rounded-2xl border border-white/[0.08] bg-[#141414] p-4 hover:border-[#c9ff47]/40 transition-colors"
      >
        <div class="min-w-0">
          <div class="flex items-center gap-2.5">
            <span class="font-display font-bold text-[#f0f0f0]">{{ inv.number }}</span>
            <span class="text-xs font-bold px-2.5 py-0.5 rounded-full" :class="STATUS[inv.status]?.c">{{ inv.status_display }}</span>
          </div>
          <p class="text-sm text-[#888888] mt-1">
            Issued {{ fmtDate(inv.issue_date) }}<template v-if="inv.due_date"> · Due {{ fmtDate(inv.due_date) }}</template>
          </p>
        </div>
        <div class="text-right shrink-0">
          <p class="font-display font-bold text-[#f0f0f0]">{{ inv.currency }} {{ Number(inv.total).toLocaleString() }}</p>
          <p class="text-xs" :class="Number(inv.balance) > 0 ? 'text-[#f5a623]' : 'text-[#22c55e]'">
            {{ Number(inv.balance) > 0 ? `Balance ${inv.currency} ${Number(inv.balance).toLocaleString()}` : "Paid in full" }}
          </p>
        </div>
        <UIcon name="i-heroicons-chevron-right" class="text-[#666] group-hover:text-[#c9ff47] transition-colors shrink-0" />
      </NuxtLink>
    </div>

    <div v-else class="rounded-2xl border border-white/[0.08] bg-[#141414] text-center py-16">
      <UIcon name="i-heroicons-document-text" class="text-4xl text-[#444]" />
      <p class="mt-3 text-[#888888]">No invoices yet.</p>
      <p class="text-sm text-[#666] mt-1">Invoices appear here after you book a court.</p>
    </div>
  </div>
</template>
