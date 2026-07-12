<script setup lang="ts">
import { nextTick, ref } from 'vue'
import type { Fragment } from '../types'

const props = defineProps<{ modelValue: Fragment[] }>()
const emit = defineEmits<{ 'update:modelValue': [Fragment[]] }>()

const draft = ref('')
const listening = ref(false)
const speechSupported = !!(window.SpeechRecognition || window.webkitSpeechRecognition)
let recog: any = null

const editingIndex = ref<number | null>(null)
const editText = ref('')
const editInputEl = ref<HTMLTextAreaElement | null>(null)
function bindEdit(el: any) { editInputEl.value = el }

const quickTags = ['坠落', '追逐', '飞起来', '水', '一扇门', '迷路', '亲人', '一束光']

function commit(next: Fragment[]) { emit('update:modelValue', next) }

function add(type = 'text', content?: string): number {
  const text = (content ?? draft.value).trim()
  if (!text) return -1
  const next = [...props.modelValue, { type, content: text }]
  commit(next)
  if (content === undefined) draft.value = ''
  return next.length - 1
}
function remove(i: number) {
  const next = props.modelValue.slice()
  next.splice(i, 1)
  commit(next)
  if (editingIndex.value === i) editingIndex.value = null
}
function onKeydown(e: KeyboardEvent) {
  if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') { e.preventDefault(); add() }
}
async function startEdit(i: number, preset?: string) {
  editingIndex.value = i
  // preset：语音转写文本直接传入，避免读取尚未同步回来的 prop（否则会是空）
  editText.value = preset !== undefined ? preset : (props.modelValue[i]?.content ?? '')
  await nextTick()
  editInputEl.value?.focus()
  editInputEl.value?.select()
}
function saveEdit() {
  if (editingIndex.value === null) return
  const i = editingIndex.value
  const text = editText.value.trim()
  editingIndex.value = null
  if (!text) { remove(i); return }
  const next = props.modelValue.slice()
  next[i] = { ...next[i], content: text }
  commit(next)
}

function toggleVoice() {
  if (!speechSupported) return
  if (listening.value) { recog?.stop(); return }
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition
  recog = new SR()
  recog.lang = 'zh-CN'
  recog.interimResults = false
  recog.continuous = false
  recog.onresult = (ev: any) => {
    const t = ev.results?.[0]?.[0]?.transcript
    if (t) {
      const i = add('voice', t)
      if (i >= 0) startEdit(i, t) // 直接用转写文本进入可编辑态（便于纠错），不依赖尚未同步的 prop
    }
  }
  recog.onend = () => { listening.value = false }
  recog.onerror = () => { listening.value = false }
  listening.value = true
  recog.start()
}
function iconFor(type: string) {
  return type === 'voice' ? '🎙' : type === 'tag' ? '✦' : '✎'
}
</script>

<template>
  <div class="frag">
    <textarea
      v-model="draft"
      class="field"
      rows="3"
      placeholder="把记得的片段写下来，一句也好…（⌘/Ctrl + Enter 添加）"
      @keydown="onKeydown"
    ></textarea>

    <div class="row">
      <button class="btn btn-primary" :disabled="!draft.trim()" @click="add()">＋ 添加这片碎片</button>
      <button v-if="speechSupported" class="btn" :class="{ live: listening }" @click="toggleVoice">
        <span class="dot" :class="{ live: listening }"></span>
        {{ listening ? '正在聆听…' : '语音录入' }}
      </button>
      <span v-else class="faint tip">（此浏览器不支持语音录入，可用文字）</span>
    </div>

    <div class="tags">
      <span class="faint tip">常见意象：</span>
      <button v-for="t in quickTags" :key="t" class="chip tag-chip" @click="add('tag', t)">{{ t }}</button>
    </div>

    <ul class="list">
      <li v-for="(f, i) in props.modelValue" :key="i" class="frag-item" :class="{ editing: editingIndex === i }">
        <span class="ficon">{{ iconFor(f.type) }}</span>
        <textarea
          v-if="editingIndex === i"
          :ref="bindEdit"
          v-model="editText"
          class="edit-input"
          rows="1"
          @keydown.enter.prevent="saveEdit"
          @keydown.esc="saveEdit"
          @blur="saveEdit"
        ></textarea>
        <template v-else>
          <span class="ftext" title="点击编辑纠错" @click="startEdit(i)">{{ f.content }}</span>
          <button class="act" title="编辑" @click="startEdit(i)">✎</button>
        </template>
        <button class="del" title="移除" @click="remove(i)">×</button>
      </li>
    </ul>
    <p v-if="props.modelValue.length" class="faint count">
      已收下 {{ props.modelValue.length }} 片梦境碎片 · 点任意一片可编辑纠错
    </p>
  </div>
</template>

<style scoped>
.frag { display: flex; flex-direction: column; gap: 14px; }
.row { display: flex; gap: 10px; flex-wrap: wrap; align-items: center; }
.tip { font-size: 13px; }
.btn .dot { width: 8px; height: 8px; border-radius: 50%; background: var(--ink-faint); }
.btn .dot.live { background: #ff6b8b; animation: breathe 1.1s infinite; }
.btn.live { border-color: rgba(255,107,139,0.5); }
.tags { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.tag-chip { cursor: pointer; transition: all 0.2s var(--ease); }
.tag-chip:hover { color: var(--ink); background: rgba(174,182,224,0.16); }
.list { list-style: none; padding: 0; margin: 4px 0 0; display: flex; flex-direction: column; gap: 8px; }
.frag-item {
  display: flex; align-items: center; gap: 11px;
  background: var(--card); border: 1px solid var(--line); border-radius: 13px; padding: 11px 14px;
  transition: border 0.2s;
}
.frag-item.editing { border-color: rgba(174,182,224,0.55); background: rgba(174,182,224,0.08); }
.ficon { color: var(--accent); opacity: 0.8; flex: none; }
.ftext { flex: 1; color: var(--ink); line-height: 1.5; cursor: text; }
.ftext:hover { color: #fff; }
.edit-input {
  flex: 1; background: transparent; border: none; color: #fff; font-family: inherit;
  font-size: 15px; line-height: 1.5; resize: none; outline: none; padding: 0;
}
.act, .del {
  background: transparent; border: none; color: var(--ink-faint); line-height: 1;
  padding: 0 3px; transition: color 0.2s; flex: none;
}
.act { font-size: 14px; }
.del { font-size: 20px; }
.act:hover { color: var(--accent); }
.del:hover { color: #ff6b8b; }
.count { font-size: 13px; margin: 2px 0 0; }
</style>
