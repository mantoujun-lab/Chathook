<script setup lang="ts">
import { computed, ref } from "vue"

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

interface SendResult {
  success: boolean
  platform: string
  webhook_name: string
  error_message?: string
}

const { data: webhooks } = await useFetch<WebhookConfig[]>("/api/webhooks")

const selected = ref<string>("")
const title = ref("")
const text = ref("")
const atAll = ref(false)
const atMobiles = ref("")
const sending = ref(false)
const lastResult = ref<SendResult | null>(null)

const webhookOptions = computed(() =>
  (webhooks.value ?? []).map((w) => ({
    label: `${w.name}（${w.platform}）`,
    value: w.id,
  }))
)

async function send() {
  if (!selected.value || !text.value) return
  sending.value = true
  lastResult.value = null
  try {
    // TODO: 适配器实现后替换为真实 $fetch("/api/send")
    const hook = webhooks.value?.find((w) => w.id === selected.value)
    const mockOk = hook?.enabled ?? false
    await new Promise((r) => setTimeout(r, 500))
    lastResult.value = mockOk
      ? {
          success: true,
          platform: hook?.platform ?? "",
          webhook_name: hook?.name ?? "",
        }
      : {
          success: false,
          platform: hook?.platform ?? "",
          webhook_name: hook?.name ?? "",
          error_message: "Webhook disabled",
        }
  } catch (e: any) {
    lastResult.value = {
      success: false,
      platform: "error",
      webhook_name: "",
      error_message: e?.message || String(e),
    }
  } finally {
    sending.value = false
  }
}
</script>

<template>
  <div class="space-y-4">
    <h1 class="text-xl font-bold">发送消息</h1>

    <UCard>
      <UForm :state="{ selected }" @submit.prevent="send" class="grid grid-cols-2 gap-4">
        <UFormField label="目标 Webhook" name="selected">
          <USelect v-model="selected" :items="webhookOptions" required class="w-full" />
        </UFormField>
        <UFormField label="标题（可选）" name="title">
          <UInput v-model="title" placeholder="富文本/Markdown 标题" class="w-full" />
        </UFormField>
        <UFormField label="消息内容" name="text" class="col-span-2">
          <UTextarea
            v-model="text"
            :rows="6"
            required
            placeholder="支持纯文本 / Markdown"
            class="w-full"
          />
        </UFormField>
        <UFormField label="@所有人" name="atAll">
          <USwitch v-model="atAll" />
        </UFormField>
        <UFormField label="@手机号（用空格/逗号分隔）" name="atMobiles">
          <UInput v-model="atMobiles" placeholder="138xxxx1234 139xxxx5678" class="w-full" />
        </UFormField>
        <div class="col-span-2">
          <UButton
            type="submit"
            :loading="sending"
            :disabled="!selected"
            color="success"
            size="lg"
          >
            发送
          </UButton>
        </div>
      </UForm>
    </UCard>

    <UAlert
      v-if="lastResult"
      :color="lastResult.success ? 'success' : 'error'"
      :title="lastResult.success ? '发送成功' : '发送失败'"
      :description="`${lastResult.platform} / ${lastResult.webhook_name}${
        lastResult.error_message ? ' — ' + lastResult.error_message : ''
      }`"
    />

    <UCard variant="soft" class="text-sm text-gray-600">
      💡 Webhook 列表已从后端加载
      <code class="px-1 rounded bg-gray-200">/api/webhooks</code>.
      发送功能待后端适配器实现后接通
      <code class="px-1 rounded bg-gray-200">POST /api/send</code>.
    </UCard>
  </div>
</template>
