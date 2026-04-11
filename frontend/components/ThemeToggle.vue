<script setup lang="ts">
// Theme cycle button: dark → light → auto → dark ...
//
// VueUse's useColorMode returns a WritableComputedRef where `.value` is the
// resolved mode (dark/light, even when the user chose "auto") and `.store.value`
// is the stored preference string itself ("dark" | "light" | "auto"). We use
// `.store.value` for display and `.value = next` for writes.
const mode = useTheme();

const cycleOrder = ["dark", "light", "auto"] as const;
type Mode = (typeof cycleOrder)[number];

function currentPref(): Mode {
  const raw = (mode.store?.value ?? "auto") as string;
  return (cycleOrder as readonly string[]).includes(raw)
    ? (raw as Mode)
    : "auto";
}

function cycle() {
  const idx = cycleOrder.indexOf(currentPref());
  const next = cycleOrder[(idx + 1) % cycleOrder.length];
  mode.value = next;
}

const label = computed(() => {
  const pref = currentPref();
  if (pref === "auto") return "Theme: auto (system)";
  if (pref === "light") return "Theme: light";
  return "Theme: dark";
});

const iconClass = computed(() => {
  const pref = currentPref();
  if (pref === "auto") return "i-tabler-device-desktop";
  if (pref === "light") return "i-tabler-sun";
  return "i-tabler-moon";
});
</script>

<template>
  <button
    type="button"
    class="theme-toggle"
    :title="label"
    :aria-label="label"
    @click="cycle"
  >
    <div :class="iconClass" />
  </button>
</template>

<style scoped>
.theme-toggle {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: var(--radius-md);
  background: transparent;
  color: var(--text-muted);
  border: 1px solid var(--border);
  font-size: 18px;
  transition: all 0.15s ease;
}

.theme-toggle:hover {
  background: var(--bg-raised);
  color: var(--text);
  border-color: var(--border-strong);
}

.theme-toggle:active {
  transform: scale(0.95);
}
</style>
