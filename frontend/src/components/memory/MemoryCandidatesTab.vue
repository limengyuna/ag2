<script setup lang="ts">
import { ref } from 'vue'
import { Sparkles, Check, RefreshCw, X } from 'lucide-vue-next'
import { useMemoryStore } from '@/stores/memory'
import type { MemoryCandidateItem } from '@/api/memory'
import { defaultSlots } from '@/constants/memory'

const memory = useMemoryStore()

const processingCandidateId = ref<number | null>(null)
const reviewingCandidate = ref<MemoryCandidateItem | null>(null)
const candidateEditValue = ref<any>(null)

// 格式化辅助函数
function formatDate(dateStr: string | null): string {
  if (!dateStr) return '未知'
  const d = new Date(dateStr)
  const now = new Date()
  const diffMs = now.getTime() - d.getTime()
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24))

  if (diffDays === 0) {
    return `今天 ${d.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })}`
  } else if (diffDays === 1) {
    return `昨天 ${d.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })}`
  } else if (diffDays < 7) {
    return `${diffDays} 天前`
  } else {
    return d.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })
  }
}

function startReviewCandidate(candidate: MemoryCandidateItem) {
  reviewingCandidate.value = candidate
  candidateEditValue.value = candidate.suggested_value
}

function closeReviewCandidate() {
  reviewingCandidate.value = null
  candidateEditValue.value = null
}

async function acceptPref(candidateId: number) {
  processingCandidateId.value = candidateId
  try {
    await memory.confirmCandidate(candidateId, true, candidateEditValue.value)
    closeReviewCandidate()
  } catch (err) {
    console.error('采纳偏好失败:', err)
  } finally {
    processingCandidateId.value = null
  }
}

async function rejectPref(candidateId: number) {
  if (confirm('确认拒绝该候选偏好提取？拒绝后本条建议将被丢弃。')) {
    processingCandidateId.value = candidateId
    try {
      await memory.confirmCandidate(candidateId, false)
      closeReviewCandidate()
    } catch (err) {
      console.error('拒绝偏好失败:', err)
    } finally {
      processingCandidateId.value = null
    }
  }
}
</script>

<template>
  <div class="h-full flex flex-col relative">
    <div v-if="memory.candidatesLoading" class="flex items-center justify-center h-48">
      <div class="flex items-center gap-3 text-zinc-400">
        <RefreshCw :size="18" class="animate-spin" />
        <span class="text-sm">检索候选偏好列表中...</span>
      </div>
    </div>

    <div v-else-if="memory.candidates.length === 0" class="flex flex-col items-center justify-center py-16 text-center">
      <Sparkles :size="40" :stroke-width="1.5" class="text-zinc-300 dark:text-zinc-600 mb-3 animate-pulse" />
      <p class="text-sm text-zinc-500 dark:text-zinc-400">暂无待确认候选偏好</p>
      <p class="text-xs text-zinc-400 dark:text-zinc-500 mt-1 max-w-sm leading-relaxed">
        系统检测到可能长期有效的习惯、约束或规则后，会生成候选项并等待你的确认。
      </p>
    </div>

    <div v-else class="grid gap-6 max-w-4xl">
      <div 
        v-for="cand in memory.candidates" 
        :key="cand.id"
        class="bg-white dark:bg-zinc-900/40 rounded-xl p-6 flex flex-col justify-between shadow-sm hover:shadow-md hover:-translate-y-0.5 ring-1 ring-black/[0.03] dark:ring-white/[0.05] transition-all duration-300 relative overflow-hidden"
      >
        <div class="absolute top-0 right-0 bg-zinc-900 text-white dark:bg-zinc-200 dark:text-zinc-900 px-3 py-1 text-[9px] rounded-bl font-semibold uppercase tracking-wider flex items-center gap-1">
          <Sparkles :size="10" />
          <span>候选建议 (Suggested)</span>
        </div>

        <div>
          <div class="flex items-center gap-2 mb-3">
            <span class="px-2 py-0.5 rounded bg-zinc-100 dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 text-xs font-mono font-semibold text-zinc-700 dark:text-zinc-300">
              {{ cand.suggested_slot_key }}
            </span>
            <span class="text-xs text-zinc-400">建议写入值:</span>
            <span class="text-xs font-mono font-bold bg-amber-50 dark:bg-amber-950/20 text-amber-600 dark:text-amber-400 px-2 py-0.5 rounded border border-amber-200/50 dark:border-amber-900/30">
              {{ cand.suggested_value }}
            </span>
          </div>

          <p class="text-xs text-zinc-500 dark:text-zinc-400 bg-zinc-50 dark:bg-zinc-950/40 p-2.5 rounded leading-relaxed border border-zinc-100 dark:border-zinc-800/40 mb-4">
            <strong class="text-zinc-700 dark:text-zinc-300">提取理由：</strong>
            {{ cand.reason || '大模型在你的话语中发现并归纳了稳定的偏好设定。' }}
          </p>

          <div class="mb-4">
            <h4 class="text-[11px] font-semibold text-zinc-400 dark:text-zinc-500 mb-1.5 uppercase">上下文会话依据 (Context)</h4>
            <blockquote class="text-xs text-zinc-600 dark:text-zinc-400 italic pl-3 border-l-2 border-zinc-300 dark:border-zinc-700 py-1.5 leading-relaxed bg-zinc-50/50 dark:bg-zinc-950/20 pr-3 rounded-r">
              "{{ cand.candidate_text }}"
            </blockquote>
          </div>
        </div>

        <div class="flex items-center justify-between pt-4 border-t border-zinc-100 dark:border-zinc-800/60">
          <div class="flex items-center gap-4 text-[10px] text-zinc-400 dark:text-zinc-500">
            <span>首次检测置信度: {{ (cand.confidence * 100).toFixed(0) }}%</span>
            <span>检测频次: 重复提及 {{ cand.seen_count }} 次</span>
            <span>发现时间: {{ formatDate(cand.created_at) }}</span>
          </div>

          <div class="flex items-center gap-2">
            <button
              @click="rejectPref(cand.id)"
              class="px-3 py-1.5 text-xs text-zinc-500 hover:text-rose-500 border border-zinc-200 dark:border-zinc-800 rounded hover:bg-rose-50 dark:hover:bg-rose-950/10 transition-colors"
              :disabled="processingCandidateId === cand.id"
            >
              丢弃拒绝
            </button>
            <button
              @click="startReviewCandidate(cand)"
              class="px-4 py-1.5 text-xs bg-zinc-900 text-white dark:bg-zinc-100 dark:text-zinc-900 rounded hover:opacity-90 flex items-center gap-1"
              :disabled="processingCandidateId === cand.id"
            >
              <Check :size="12" />
              <span>采纳确认...</span>
            </button>
          </div>
        </div>
      </div>
    </div>

    <div 
      v-if="reviewingCandidate" 
      class="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4 transition-all duration-200"
    >
      <div class="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded max-w-lg w-full p-6 shadow-xl relative animate-in fade-in zoom-in-95 duration-200">
        <button 
          @click="closeReviewCandidate" 
          class="absolute top-4 right-4 text-zinc-400 hover:text-zinc-600 dark:hover:text-zinc-200"
        >
          <X :size="18" />
        </button>

        <h3 class="text-base font-semibold text-zinc-900 dark:text-zinc-100 flex items-center gap-2">
          <Sparkles :size="18" class="text-amber-500" />
          <span>确认采纳候选偏好</span>
        </h3>
        <p class="text-xs text-zinc-400 dark:text-zinc-500 mt-1">
          将模型学习到的提取规则转换为物理生效的用户画像。在写入前，你可以对提取出的值进行手动校对微调：
        </p>

        <div class="mt-5 space-y-4">
          <div>
            <label class="block text-xs font-semibold text-zinc-400 dark:text-zinc-500 mb-1 uppercase">槽位 (Slot Key)</label>
            <div class="text-xs font-mono font-bold bg-zinc-100 dark:bg-zinc-800 text-zinc-700 dark:text-zinc-300 px-3 py-2 rounded">
              {{ reviewingCandidate.suggested_slot_key }}
            </div>
          </div>

          <div>
            <label class="block text-xs font-semibold text-zinc-400 dark:text-zinc-500 mb-1 uppercase">拟写入的值 (Verified Value)</label>
            <select 
              v-if="defaultSlots.find((s) => s.key === reviewingCandidate!.suggested_slot_key)?.valType === 'enum'" 
              v-model="candidateEditValue"
              class="w-full bg-zinc-50 dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 text-xs rounded px-3 py-2 text-zinc-800 dark:text-zinc-100 focus:outline-none focus:ring-1 focus:ring-zinc-400"
            >
              <option 
                v-for="opt in defaultSlots.find((s) => s.key === reviewingCandidate!.suggested_slot_key)?.options" 
                :key="opt" 
                :value="opt"
              >
                {{ opt }}
              </option>
            </select>
            <select 
              v-else-if="defaultSlots.find((s) => s.key === reviewingCandidate!.suggested_slot_key)?.valType === 'boolean'" 
              v-model="candidateEditValue"
              class="w-full bg-zinc-50 dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 text-xs rounded px-3 py-2 text-zinc-800 dark:text-zinc-100 focus:outline-none focus:ring-1 focus:ring-zinc-400"
            >
              <option :value="true">是 (True)</option>
              <option :value="false">否 (False)</option>
            </select>
            <input 
              v-else 
              type="text" 
              v-model="candidateEditValue"
              class="w-full bg-zinc-50 dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 text-xs rounded px-3 py-2 text-zinc-800 dark:text-zinc-100 focus:outline-none focus:ring-1 focus:ring-zinc-400"
            />
          </div>

          <div>
            <label class="block text-xs font-semibold text-zinc-400 dark:text-zinc-500 mb-1 uppercase">提取依据背景 (Context Reference)</label>
            <div class="text-xs italic bg-zinc-50 dark:bg-zinc-950/40 p-3 rounded border border-zinc-100 dark:border-zinc-800/40 leading-relaxed text-zinc-500 dark:text-zinc-400 max-h-24 overflow-y-auto">
              "{{ reviewingCandidate.candidate_text }}"
            </div>
          </div>
        </div>

        <div class="mt-6 flex items-center justify-end gap-2 pt-4 border-t border-zinc-100 dark:border-zinc-800">
          <button 
            @click="closeReviewCandidate" 
            class="px-4 py-2 text-xs font-medium text-zinc-600 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-100 hover:bg-zinc-100 dark:hover:bg-zinc-800 rounded transition-colors"
          >
            取消
          </button>
          <button 
            @click="acceptPref(reviewingCandidate.id)" 
            class="px-4 py-2 text-xs font-medium bg-zinc-900 text-white dark:bg-zinc-100 dark:text-zinc-900 rounded hover:opacity-90 flex items-center gap-1 shadow-sm"
            :disabled="processingCandidateId === reviewingCandidate.id"
          >
            <Check :size="14" />
            <span>确认采纳</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.fade-in {
  animation: fadeIn 0.2s ease-out;
}
@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}
</style>
