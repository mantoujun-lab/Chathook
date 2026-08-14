// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
  modules: ["@nuxt/ui"],
  compatibilityDate: "2025-08-14",
  devtools: { enabled: true },
  typescript: { strict: true },
  css: ["~/assets/css/main.css"],
  // 禁用需要访问海外 CDN 的字体源 (fonts.google.com 等), 避免国内环境启动/构建时卡住超时
  fonts: {
    providers: {
      google: false,
      googleicons: false,
      adobe: false,
      bunny: false,
      fontshare: false,
      fontsource: false,
    },
  },
  routeRules: {
    // 开发/生产均将后端 API 代理到 FastAPI, ** 保留 /api 之后的子路径
    "/api/**": { proxy: { to: "http://127.0.0.1:8000/api/**" } },
    "/health": { proxy: { to: "http://127.0.0.1:8000/health" } },
  },
  runtimeConfig: {
    public: {
      apiBase: process.env.API_BASE ?? "",
    },
  },
  srcDir: "app/",
})
