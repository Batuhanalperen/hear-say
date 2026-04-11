// Nuxt 3 configuration
export default defineNuxtConfig({
  compatibilityDate: "2025-01-01",
  devtools: { enabled: true },
  modules: ["@unocss/nuxt", "@vueuse/nuxt"],

  // SPA mode — the Python backend serves the static build, no Node runtime
  ssr: false,

  runtimeConfig: {
    public: {
      // Empty default = relative URLs, same origin as the backend (port 7777).
      // In dev you can override with NUXT_PUBLIC_API_BASE=http://127.0.0.1:7777
      apiBase: process.env.NUXT_PUBLIC_API_BASE ?? "",
    },
  },

  typescript: {
    strict: true,
  },

  nitro: {
    preset: "static",
    output: {
      publicDir: ".output/public",
    },
  },

  app: {
    head: {
      title: "hear-say",
      meta: [
        { charset: "utf-8" },
        { name: "viewport", content: "width=device-width, initial-scale=1" },
        {
          name: "description",
          content: "Audio to piano MIDI transcription, running locally on your GPU.",
        },
      ],
    },
  },

  css: ["~/assets/main.css"],
});
