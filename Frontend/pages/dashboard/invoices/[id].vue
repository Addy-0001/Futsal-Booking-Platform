<script setup>
definePageMeta({ middleware: "auth", layout: "dashboard" });

const api = useApi();
const route = useRoute();
const { data: inv, error } = await useAsyncData(
  `invoice-${route.params.id}`,
  () => api(`/api/invoices/${route.params.id}/`),
  { server: false, lazy: true }
);
useSeoMeta({ title: () => `Invoice ${inv.value?.number || ""} | Booksall` });

const STATUS = {
  DRAFT: "bg-[#1e1e1e] text-[#bdbdbd]", UNPAID: "bg-[#f5c842]/15 text-[#f5c842]",
  PARTIAL: "bg-[#4aa3ff]/15 text-[#4aa3ff]", PAID: "bg-[#22c55e]/15 text-[#22c55e]",
  OVERDUE: "bg-red-500/15 text-red-400", CANCELLED: "bg-[#1e1e1e] text-[#888]",
  REFUNDED: "bg-[#a855f7]/15 text-[#c99bff]",
};
const fmtDate = (d) => (d ? new Date(d).toLocaleDateString([], { day: "numeric", month: "short", year: "numeric" }) : "—");
const fmtDT = (d) => (d ? new Date(d).toLocaleString([], { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" }) : "—");
const money = (n, c = "NPR") => `${c} ${Number(n).toLocaleString(undefined, { minimumFractionDigits: 2 })}`;
</script>

<template>
  <div>
    <NuxtLink to="/dashboard/invoices" class="inline-flex items-center gap-1.5 text-sm text-[#888888] hover:text-[#c9ff47] mb-5">
      <UIcon name="i-heroicons-arrow-left" /> All invoices
    </NuxtLink>

    <div v-if="error" class="rounded-2xl border border-red-500/30 bg-red-500/10 p-6 text-red-300">Invoice not found.</div>

    <div v-else-if="inv" class="rounded-3xl border border-white/[0.08] bg-[#141414] overflow-hidden">
      <!-- Header -->
      <div class="flex flex-wrap items-start justify-between gap-4 p-6 border-b border-white/[0.06]">
        <div>
          <p class="eyebrow text-[#c9ff47]">Invoice</p>
          <h1 class="font-display text-3xl font-black text-white mt-1">{{ inv.number }}</h1>
          <p class="text-sm text-[#888888] mt-1">Issued {{ fmtDate(inv.issue_date) }}<template v-if="inv.due_date"> · Due {{ fmtDate(inv.due_date) }}</template></p>
        </div>
        <span class="text-sm font-bold px-3 py-1 rounded-full" :class="STATUS[inv.status]">{{ inv.status_display }}</span>
      </div>

      <!-- Bill to -->
      <div class="grid sm:grid-cols-2 gap-4 p-6 border-b border-white/[0.06]">
        <div>
          <p class="text-xs uppercase tracking-wide text-[#666] mb-1">Billed to</p>
          <p class="text-[#f0f0f0] font-semibold">{{ inv.customer_name }}</p>
        </div>
        <div class="sm:text-right">
          <p class="text-xs uppercase tracking-wide text-[#666] mb-1">Amount due</p>
          <p class="font-display text-2xl font-bold" :class="Number(inv.balance) > 0 ? 'text-[#f5a623]' : 'text-[#22c55e]'">{{ money(inv.balance, inv.currency) }}</p>
        </div>
      </div>

      <!-- Items -->
      <div class="p-6">
        <table class="w-full text-sm">
          <thead>
            <tr class="text-left text-[#888888] border-b border-white/[0.08]">
              <th class="py-2 font-medium">Description</th>
              <th class="py-2 font-medium text-right">Qty</th>
              <th class="py-2 font-medium text-right">Unit</th>
              <th class="py-2 font-medium text-right">Amount</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="it in inv.items" :key="it.id" class="border-b border-white/[0.05]">
              <td class="py-3 text-[#e5e5e5]">{{ it.description }}</td>
              <td class="py-3 text-right text-[#bdbdbd]">{{ Number(it.quantity) }}</td>
              <td class="py-3 text-right text-[#bdbdbd]">{{ money(it.unit_price, inv.currency) }}</td>
              <td class="py-3 text-right text-[#f0f0f0] font-medium">{{ money(it.amount, inv.currency) }}</td>
            </tr>
          </tbody>
        </table>

        <!-- Totals -->
        <div class="mt-5 ml-auto max-w-xs space-y-1.5 text-sm">
          <div class="flex justify-between text-[#bdbdbd]"><span>Subtotal</span><span>{{ money(inv.subtotal, inv.currency) }}</span></div>
          <div v-if="Number(inv.tax_amount) > 0" class="flex justify-between text-[#bdbdbd]"><span>Tax ({{ Number(inv.tax_rate) }}%)</span><span>{{ money(inv.tax_amount, inv.currency) }}</span></div>
          <div class="flex justify-between text-[#f0f0f0] font-bold text-base border-t border-white/[0.08] pt-2"><span>Total</span><span>{{ money(inv.total, inv.currency) }}</span></div>
          <div class="flex justify-between text-[#22c55e]"><span>Paid</span><span>{{ money(inv.amount_paid, inv.currency) }}</span></div>
          <div class="flex justify-between font-bold" :class="Number(inv.balance) > 0 ? 'text-[#f5a623]' : 'text-[#22c55e]'"><span>Balance</span><span>{{ money(inv.balance, inv.currency) }}</span></div>
        </div>
      </div>

      <!-- Payments -->
      <div v-if="inv.payments?.length" class="px-6 pb-6">
        <p class="text-xs uppercase tracking-wide text-[#666] mb-2">Payments</p>
        <div class="space-y-2">
          <div v-for="p in inv.payments" :key="p.id" class="flex items-center justify-between rounded-xl bg-[#0f0f0f] border border-white/[0.06] px-4 py-2.5 text-sm">
            <span class="text-[#bdbdbd]"><UIcon name="i-heroicons-check-circle" class="text-[#22c55e]" /> {{ p.method_display }}<template v-if="p.reference"> · {{ p.reference }}</template></span>
            <span class="text-[#888888]">{{ fmtDT(p.paid_at) }}</span>
            <span class="text-[#f0f0f0] font-medium">{{ money(p.amount, inv.currency) }}</span>
          </div>
        </div>
      </div>

      <div class="px-6 pb-6">
        <p class="text-xs text-[#666]">Payments are collected at the venue. Questions about this invoice? <NuxtLink to="/dashboard/tickets" class="text-[#c9ff47] hover:underline">Open a support ticket</NuxtLink>.</p>
      </div>
    </div>
  </div>
</template>
