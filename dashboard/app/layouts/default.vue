<template>
  <div class="min-h-screen flex flex-col bg-gray-50 text-gray-800">
    <header class="flex items-center justify-between px-6 py-3 bg-white border-b border-gray-200">
      <div class="flex items-baseline gap-2">
        <strong class="text-lg">Chathook</strong>
        <span class="text-xs text-gray-500">Webhook 中转站</span>
      </div>
      <nav class="flex gap-3">
        <UButton to="/" variant="ghost" color="neutral" size="sm">发送</UButton>
        <UButton to="/webhooks" variant="ghost" color="neutral" size="sm">Webhook 配置</UButton>
      </nav>
    </header>
    <main class="flex-1 p-6 max-w-4xl w-full mx-auto">
      <slot />
    </main>
  </div>
</template>
