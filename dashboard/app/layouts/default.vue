<template>
  <div class="min-h-screen flex flex-col bg-white dark:bg-gray-950 text-gray-800 dark:text-gray-100">
    <header class="flex items-center justify-between px-6 py-3 bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-800">
      <div class="flex items-baseline gap-2">
        <strong class="text-lg">Chathook</strong>
        <span class="text-xs text-gray-500 dark:text-gray-400">Webhook 中转站</span>
      </div>
      <nav class="flex items-center gap-3">
        <UButton to="/" variant="ghost" color="neutral" size="sm">发送</UButton>
        <UButton to="/webhooks" variant="ghost" color="neutral" size="sm">Webhook 配置</UButton>
        <!-- 主题切换: 三态(system/light/dark) + 快速两态按钮 -->
        <!-- ClientOnly 包裹避免 hydration mismatch (@nuxtjs/color-mode 在客户端初始化) -->
        <!-- 注: <UColorModeSelect /> 内部硬编码了 items (见 @nuxt/ui ColorModeSelect.vue 第 63-67 行),
             props 中未声明 items, 外部传入的 :items 会被内部覆盖;
             选项文案来自 useLocale(), 由 <UApp :locale="zh_cn"> 注入为 "系统 / 浅色 / 深色". -->
        <ClientOnly>
          <UColorModeSelect
            size="sm"
            color="neutral"
            variant="outline"
            aria-label="主题模式"
          />
          <UColorModeButton color="neutral" variant="ghost" />
          <template #fallback>
            <div class="size-8" />
          </template>
        </ClientOnly>
      </nav>
    </header>
    <main class="flex-1 p-6 max-w-4xl w-full mx-auto">
      <slot />
    </main>
  </div>
</template>
