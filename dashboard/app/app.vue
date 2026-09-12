<script setup lang="ts">
import { zh_cn } from "@nuxt/ui/locale"

// 为整站 UI 注入简体中文 locale, 这样:
//   - useLocale() 会拿到中文翻译 (例如 colorMode.system / light / dark -> 系统 / 浅色 / 深色),
//     使顶栏 <UColorModeSelect /> 内置三态文案显示为中文
//   - 其它 Nuxt UI 组件 (alert / banner / calendar / carousel / chat / command palette 等) 的内置文案也会一并本地化
// zh_cn 是从 @nuxt/ui/locale 导出的 Locale 对象, 不是字符串, 因此绑定到 <UApp :locale> 上即可生效.
</script>

<template>
  <UApp :locale="zh_cn">
    <NuxtLayout>
      <NuxtPage />
    </NuxtLayout>
  </UApp>
</template>
