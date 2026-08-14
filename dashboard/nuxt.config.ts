// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
  modules: ["@nuxt/ui"],
  compatibilityDate: "2025-08-14",
  devtools: { enabled: true },
  typescript: { strict: true },
  css: ["~/assets/css/main.css"],
  nitro: {
    devProxy: {
      "/api": { target: "http://127.0.0.1:8000", changeOrigin: true },
      "/health": { target: "http://127.0.0.1:8000", changeOrigin: true },
    },
  },
  runtimeConfig: {
    public: {
      apiBase: process.env.API_BASE ?? "",
    },
  },
  srcDir: "app/",
})
