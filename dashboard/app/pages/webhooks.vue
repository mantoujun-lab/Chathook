<script setup lang="ts">
import { ref } from "vue"

type PlatformType = "feishu" | "dingtalk" | "custom"

interface WebhookConfig {
  id: string
  name: string
  platform: PlatformType
  url: string
  secret?: string | null
  extra: Record<string, any>
  enabled: boolean
}

const { data, refresh } = await useFetch<WebhookConfig[]>("/api/webhooks")

const form = ref<WebhookConfig>({
  id: "",
  name: "",
  platform: "feishu",
  url: "",
  secret: null,
  extra: {},
  enabled: true,
})

const secretInput = ref("")
const saving = ref(false)
const toast = useToast()

const platformOptions = [
  { label: "飞书", value: "feishu" },
  { label: "钉钉", value: "dingtalk" },
  { label: "自定义", value: "custom" },
]

function resetForm() {
  form.value = {
    id: "",
    name: "",
    platform: "feishu",
    url: "",
    secret: null,
    extra: {},
    enabled: true,
  }
  secretInput.value = ""
}

async function onSubmit() {
  saving.value = true
  try {
    const payload: WebhookConfig = {
      ...form.value,
      secret: secretInput.value.trim() ? secretInput.value.trim() : null,
    }
    await $fetch("/api/webhooks", { method: "POST", body: payload })
    toast.add({ title: "已新增", description: payload.name, color: "success" })
    resetForm()
    await refresh()
  } catch (e: any) {
    toast.add({
      title: "新增失败",
      description: e?.data?.detail ?? e?.message ?? String(e),
      color: "error",
    })
  } finally {
    saving.value = false
  }
}

async function onDelete(id: string) {
  if (!confirm(`删除 Webhook "${id}" ？`)) return
  try {
    await $fetch(`/api/webhooks/${id}`, { method: "DELETE" })
    toast.add({ title: "已删除", description: id, color: "neutral" })
    await refresh()
  } catch (e: any) {
    toast.add({
      title: "删除失败",
      description: e?.data?.detail ?? e?.message ?? String(e),
      color: "error",
    })
  }
}

async function toggleEnabled(w: WebhookConfig) {
  try {
    await $fetch(`/api/webhooks/${w.id}`, {
      method: "PUT",
      body: { enabled: !w.enabled },
    })
    await refresh()
  } catch (e: any) {
    toast.add({
      title: "更新失败",
      description: e?.data?.detail ?? e?.message ?? String(e),
      color: "error",
    })
  }
}
</script>

<template>
  <div class="space-y-4">
    <h1 class="text-xl font-bold">Webhook 配置管理</h1>

    <UCard>
      <template #header>
        <h3 class="text-base font-semibold">新增 Webhook</h3>
      </template>
      <UForm :state="form" @submit.prevent="onSubmit" class="grid grid-cols-2 gap-4">
        <UFormField label="ID" name="id">
          <UInput v-model="form.id" required placeholder="例如：feishu-dev" class="w-full" />
        </UFormField>
        <UFormField label="名称" name="name">
          <UInput v-model="form.name" required placeholder="显示名" class="w-full" />
        </UFormField>
        <UFormField label="平台" name="platform">
          <USelect v-model="form.platform" :items="platformOptions" class="w-full" />
        </UFormField>
        <UFormField label="Webhook URL" name="url" class="col-span-2">
          <UInput v-model="form.url" required type="url" placeholder="https://..." class="w-full" />
        </UFormField>
        <UFormField label="签名密钥（可选）" name="secret" class="col-span-2">
          <UInput v-model="secretInput" placeholder="留空表示不需要" class="w-full" />
        </UFormField>
        <div class="col-span-2">
          <UButton type="submit" :loading="saving" color="primary">新增</UButton>
        </div>
      </UForm>
    </UCard>

    <UCard>
      <template #header>
        <h3 class="text-base font-semibold">已配置</h3>
      </template>
      <UTable
        v-if="data && data.length"
        :data="data"
        :columns="[
          { id: 'name', header: '名称' },
          { id: 'platform', header: '平台' },
          { id: 'url', header: 'URL' },
          { id: 'enabled', header: '启用' },
          { id: 'actions', header: '操作' },
        ]"
        class="w-full"
      >
        <template #name-cell="{ row }">
          <div>
            <div class="font-medium">{{ row.original.name }}</div>
            <div class="text-xs text-gray-500">{{ row.original.id }}</div>
          </div>
        </template>
        <template #platform-cell="{ row }">
          <UBadge
            :color="
              row.original.platform === 'feishu'
                ? 'primary'
                : row.original.platform === 'dingtalk'
                  ? 'success'
                  : 'neutral'
            "
          >
            {{ row.original.platform }}
          </UBadge>
        </template>
        <template #url-cell="{ row }">
          <span class="text-sm break-all">{{ row.original.url }}</span>
        </template>
        <template #enabled-cell="{ row }">
          <USwitch
            :model-value="row.original.enabled"
            @update:model-value="toggleEnabled(row.original)"
          />
        </template>
        <template #actions-cell="{ row }">
          <UButton
            @click="onDelete(row.original.id)"
            color="error"
            variant="outline"
            size="xs"
          >删除</UButton>
        </template>
      </UTable>
      <p v-else class="text-gray-500">暂无配置</p>
    </UCard>

    <UCard variant="soft" class="text-sm text-gray-600">
      💡 数据已通过后端接口
      <code class="px-1 rounded bg-gray-200">/api/webhooks</code>
      读取与写入, 存储于
      <code class="px-1 rounded bg-gray-200">data/webhooks.json</code>.
    </UCard>
  </div>
</template>
