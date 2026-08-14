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

// TODO: 后端跑起来后替换为 useFetch("/api/webhooks")
const MOCK_HOOKS: WebhookConfig[] = [
  {
    id: "feishu-demo",
    name: "飞书-产品通知",
    platform: "feishu",
    url: "https://open.feishu.cn/open-apis/bot/v2/hook/xxx",
    secret: null,
    extra: {},
    enabled: true,
  },
  {
    id: "dingtalk-demo",
    name: "钉钉-运维告警",
    platform: "dingtalk",
    url: "https://oapi.dingtalk.com/robot/send?access_token=xxx",
    secret: "SECxxxx",
    extra: {},
    enabled: true,
  },
  {
    id: "custom-demo",
    name: "自定义-内部服务",
    platform: "custom",
    url: "https://api.example.com/webhook",
    secret: null,
    extra: {},
    enabled: false,
  },
]

const { data, refresh } = await useAsyncData<WebhookConfig[]>("mock-hooks-manage", () =>
  Promise.resolve([...MOCK_HOOKS])
)

const form = ref<WebhookConfig>({
  id: "",
  name: "",
  platform: "feishu",
  url: "",
  secret: null,
  extra: {},
  enabled: true,
})

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
}

async function onSubmit() {
  saving.value = true
  try {
    // TODO: 后端跑起来后替换为真实 $fetch
    await new Promise((r) => setTimeout(r, 300))
    const current = data.value ?? []
    current.push({ ...form.value })
    data.value = current
    toast.add({ title: "已新增（Mock）", description: form.value.name, color: "success" })
    resetForm()
  } finally {
    saving.value = false
  }
}

async function onDelete(id: string) {
  if (!confirm(`删除 Webhook "${id}" ？`)) return
  // TODO: 后端跑起来后替换为真实 $fetch
  data.value = (data.value ?? []).filter((w) => w.id !== id)
  toast.add({ title: "已删除（Mock）", description: id, color: "neutral" })
}

async function toggleEnabled(w: WebhookConfig) {
  w.enabled = !w.enabled
  // TODO: 后端跑起来后替换为真实 $fetch PUT
  toast.add({
    title: w.enabled ? "已启用（Mock）" : "已禁用（Mock）",
    description: w.name,
    color: "neutral",
  })
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
          <UInput v-model="form.secret" placeholder="部分平台需要" class="w-full" />
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
      <UTable v-if="data && data.length" :data="data" class="w-full">
        <template #name-cell="{ row }">
          <div>
            <div class="font-medium">{{ row.name }}</div>
            <div class="text-xs text-gray-500">{{ row.id }}</div>
          </div>
        </template>
        <template #platform-cell="{ row }">
          <UBadge
            :color="
              row.platform === 'feishu'
                ? 'primary'
                : row.platform === 'dingtalk'
                  ? 'success'
                  : 'neutral'
            "
          >
            {{ row.platform }}
          </UBadge>
        </template>
        <template #url-cell="{ row }">
          <span class="text-sm break-all">{{ row.url }}</span>
        </template>
        <template #enabled-cell="{ row }">
          <USwitch :model-value="row.enabled" @update:model-value="toggleEnabled(row)" />
        </template>
        <template #actions-cell="{ row }">
          <UButton @click="onDelete(row.id)" color="error" variant="outline" size="xs">删除</UButton>
        </template>
      </UTable>
      <p v-else class="text-gray-500">暂无配置</p>
    </UCard>

    <UCard variant="soft" class="text-sm text-gray-600">
      💡 当前展示为 Mock 数据，等后端跑通后，将
      <code class="px-1 rounded bg-gray-200">useAsyncData</code>
      替换为 <code class="px-1 rounded bg-gray-200">useFetch</code>，操作（增删改）替换为真实的
      <code class="px-1 rounded bg-gray-200">$fetch("/api/webhooks", ...)</code> 即可。
    </UCard>
  </div>
</template>
