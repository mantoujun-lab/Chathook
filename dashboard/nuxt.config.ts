// https://nuxt.com/docs/api/configuration/nuxt-config
//
// 后端 API_BASE 约定（同时驱动代理与 runtimeConfig）：
//   - 未设置时: 默认 http://127.0.0.1:8000（本地 uv run uvicorn 默认端口）
//   - 生产部署: 如 API_BASE=https://chathook.example.com, 所有 /api 与 /health
//     请求将被代理到该地址, 前端 $fetch 也使用同源策略 (apiBase 留空走相对路径)
//
// Nuxt 的 routeRules 在构建时展开, 因此这里读取字符串级 process.env.API_BASE,
// runtimeConfig.public.apiBase 也复用同一个 env 变量, 保证一致.
const DEFAULT_API_BASE = "http://127.0.0.1:8000";
const API_BASE = process.env.API_BASE || DEFAULT_API_BASE;

export default defineNuxtConfig({
  modules: ["@nuxt/ui"],
  // 将图标本地端点从默认的 /api/_nuxt_icon 改为 /_nuxt_icon,
  // 避免被下方 /api/** 代理规则转发到 FastAPI 导致图标 404
  icon: {
    localApiEndpoint: "/_nuxt_icon",
  },
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
    // 开发/生产均将后端 API 代理到由 API_BASE 环境变量指定的 FastAPI,
    // ** 保留 /api 之后的子路径
    "/api/**": { proxy: { to: `${API_BASE}/api/**` } },
    "/health": { proxy: { to: `${API_BASE}/health` } },
  },
  runtimeConfig: {
    public: {
      // 前端 $fetch 使用的后端基础地址:
      //   - 未设置 NUXT_PUBLIC_API_BASE 且未设置 API_BASE 时 -> "" (同源相对路径, 通过
      //     Nuxt routeRules 代理转发到上方 API_BASE)
      //   - 设置 NUXT_PUBLIC_API_BASE 时 -> 使用该值 (独立部署直连后端的场景)
      //   - 设置 API_BASE 但未设置 NUXT_PUBLIC_API_BASE 时 -> 沿用 API_BASE,
      //     避免单独声明两个相近变量产生漂移
      //
      // 注意: 区分两个环境变量
      //   - API_BASE              : 构建期 routeRules proxy 目标 (本文件顶部使用, 必须在
      //     nuxi dev/build 之前设置)
      //   - NUXT_PUBLIC_API_BASE  : 运行期 runtimeConfig.public.apiBase 的显式覆盖
      //     (Nuxt 约定前缀). 若未显式覆盖, 回退到 API_BASE (同源代理场景仍可留空
      //     "NUXT_PUBLIC_API_BASE=" 显式设为空)
      apiBase: process.env.NUXT_PUBLIC_API_BASE ?? process.env.API_BASE ?? "",
    },
  },
  srcDir: "app/",
});
