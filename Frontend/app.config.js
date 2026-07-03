export default defineAppConfig({
  ui: {
    primary: "volt",
    gray: "neutral",
    button: {
      rounded: "rounded-xl",
      font: "font-semibold",
      default: { size: "md" },
    },
    card: {
      rounded: "rounded-2xl",
      shadow: "shadow-none",
      background: "bg-[#141414]",
      ring: "ring-1 ring-white/[0.08]",
      divide: "divide-y divide-white/[0.08]",
    },
    badge: {
      rounded: "rounded-full",
      font: "font-semibold",
    },
    input: {
      rounded: "rounded-xl",
      color: {
        white: {
          outline: "bg-[#1a1a1a] text-white ring-1 ring-white/[0.08] focus:ring-2 focus:ring-volt-400",
        },
      },
    },
    select: {
      rounded: "rounded-xl",
    },
    accordion: {
      item: {
        padding: "py-4",
      },
    },
  },
});
