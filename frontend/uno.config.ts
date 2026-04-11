import { defineConfig, presetIcons, presetUno } from "unocss";

// Icons referenced only through dynamic class bindings (e.g.
// `:class="\`i-tabler-${step.icon}\`"`) are invisible to UnoCSS's static
// scanner. Safelist them so the CSS rules are always emitted.
const DYNAMIC_ICONS = [
  // Feature cards (index.vue)
  "i-tabler-stack-2",
  "i-tabler-device-speaker",
  // Pipeline diagram steps (PipelineDiagram.vue)
  "i-tabler-microphone",
  "i-tabler-file-music",
  // Stem icons in the debug audio section ([id].vue stemIconMap)
  "i-tabler-microphone-2",
  "i-tabler-activity",
  "i-tabler-guitar-pick",
  // EmptyState default icon
  "i-tabler-music-off",
];

// NOTE: No theme colors, no shortcuts. All design tokens (colors, spacing,
// typography, component classes like .card / .btn-*) live in assets/main.css
// as CSS custom properties so they can react to the light/dark theme switch.
// Adding UnoCSS shortcuts with hardcoded colors here would bake one theme
// into the compiled CSS and defeat theme switching.
export default defineConfig({
  presets: [
    presetUno(),
    presetIcons({
      scale: 1.2,
      // Local package — no build-time CDN fetch, works offline
      collections: {
        tabler: () =>
          import("@iconify-json/tabler/icons.json").then((m: any) => m.default),
      },
    }),
  ],
  safelist: DYNAMIC_ICONS,
});
