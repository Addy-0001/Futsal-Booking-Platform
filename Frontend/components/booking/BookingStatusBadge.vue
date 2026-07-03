<script setup>
const props = defineProps(['status']);
const map = {
    PENDING_APPROVAL: { label: "Pending approval", color: "amber", dot: "bg-amber-500" },
    APPROVED: { label: "Approved", color: "green", dot: "bg-green-500" },
    REJECTED: { label: "Rejected", color: "red", dot: "bg-red-500" },
    CANCELLED: { label: "Cancelled", color: "gray", dot: "bg-[#404040]" },
    EXPIRED: { label: "Expired", color: "gray", dot: "bg-[#404040]" },
    COMPLETED: { label: "Completed", color: "blue", dot: "bg-[#c9ff47]" },
};
const meta = computed(() => map[props.status] ?? { label: props.status, color: "gray", dot: "bg-[#404040]" });
</script>

<template>
  <UBadge :color="meta.color" variant="subtle" size="sm" class="gap-1.5">
    <span class="w-1.5 h-1.5 rounded-full" :class="meta.dot" />
    {{ meta.label }}
  </UBadge>
</template>
