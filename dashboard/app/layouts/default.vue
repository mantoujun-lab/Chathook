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
        <ClientOnly>
          <UColorModeSelect
            :items="[
              { label: '系统', value: 'system' },
              { label: '浅色', value: 'light' },
              { label: '深色', value: 'dark' },
            ]"
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
