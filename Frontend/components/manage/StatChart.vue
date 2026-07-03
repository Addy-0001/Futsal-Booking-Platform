<script setup>
// Dependency-free SVG bar chart with an optional line overlay (second series).
// Data arrives pre-aggregated from the backend — this only draws.
const props = defineProps({
    data: { type: Array, default: () => [] }, // [{ label, value, line?, title? }]
    height: { type: Number, default: 160 },
    lineLabel: { type: String, default: "" },
    barLabel: { type: String, default: "" },
    // Show roughly this many x-axis labels (avoids 30 cramped labels).
    maxTicks: { type: Number, default: 8 },
});

const W = 600;
const PAD = { top: 10, bottom: 22, left: 0, right: 0 };

const maxBar = computed(() => Math.max(1, ...props.data.map((d) => d.value)));
const maxLine = computed(() => Math.max(1, ...props.data.map((d) => d.line ?? 0)));
const hasLine = computed(() => props.data.some((d) => (d.line ?? 0) > 0));

const innerH = computed(() => props.height - PAD.top - PAD.bottom);
const slot = computed(() => W / Math.max(1, props.data.length));
const barW = computed(() => Math.max(3, Math.min(26, slot.value * 0.62)));

function barX(i) {
    return i * slot.value + (slot.value - barW.value) / 2;
}
function barY(v) {
    return PAD.top + innerH.value * (1 - v / maxBar.value);
}
function barH(v) {
    return (innerH.value * v) / maxBar.value;
}
const linePath = computed(() => {
    if (!hasLine.value) return "";
    return props.data
        .map((d, i) => {
            const x = i * slot.value + slot.value / 2;
            const y = PAD.top + innerH.value * (1 - (d.line ?? 0) / maxLine.value);
            return `${i === 0 ? "M" : "L"}${x.toFixed(1)},${y.toFixed(1)}`;
        })
        .join(" ");
});

const tickEvery = computed(() => Math.max(1, Math.ceil(props.data.length / props.maxTicks)));
const hovered = ref(-1);
</script>

<template>
  <div>
    <div v-if="barLabel || (hasLine && lineLabel)" class="flex items-center gap-4 text-xs text-[#888888] mb-2">
      <span v-if="barLabel" class="inline-flex items-center gap-1.5">
        <span class="w-3 h-3 rounded-sm bg-[#c9ff47]" /> {{ barLabel }}
      </span>
      <span v-if="hasLine && lineLabel" class="inline-flex items-center gap-1.5">
        <span class="w-3 h-0.5 rounded bg-[#4aa3ff]" /> {{ lineLabel }}
      </span>
    </div>

    <svg :viewBox="`0 0 ${W} ${height}`" class="w-full" preserveAspectRatio="none" @mouseleave="hovered = -1">
      <!-- Baseline -->
      <line :x1="0" :x2="W" :y1="height - PAD.bottom" :y2="height - PAD.bottom" stroke="rgba(255,255,255,0.08)" />

      <!-- Bars -->
      <g v-for="(d, i) in data" :key="i">
        <rect
          :x="barX(i)" :y="barY(d.value)"
          :width="barW" :height="Math.max(d.value > 0 ? 2 : 0, barH(d.value))"
          rx="3"
          :fill="hovered === i ? '#d9ff6b' : '#c9ff47'"
          :fill-opacity="d.value > 0 ? (hovered === i ? 1 : 0.85) : 0"
        />
        <!-- Invisible hover target across the full column -->
        <rect
          :x="i * slot" y="0" :width="slot" :height="height - PAD.bottom"
          fill="transparent"
          @mouseenter="hovered = i"
        >
          <title>{{ d.title || `${d.label}: ${d.value}` }}</title>
        </rect>
        <!-- X labels (thinned) -->
        <text
          v-if="i % tickEvery === 0"
          :x="i * slot + slot / 2" :y="height - 7"
          text-anchor="middle" font-size="10" fill="#777777"
        >
          {{ d.label }}
        </text>
      </g>

      <!-- Line overlay -->
      <path v-if="hasLine" :d="linePath" fill="none" stroke="#4aa3ff" stroke-width="2" stroke-linejoin="round" vector-effect="non-scaling-stroke" />

      <!-- Hover readout -->
      <g v-if="hovered >= 0 && data[hovered]">
        <text :x="W - 4" y="14" text-anchor="end" font-size="12" font-weight="700" fill="#f0f0f0">
          {{ data[hovered].title || `${data[hovered].label}: ${data[hovered].value}` }}
        </text>
      </g>
    </svg>
  </div>
</template>
