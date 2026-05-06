<template>
  <div class="chat-page">
    <!-- 顶部标题栏 -->
    <header class="chat-header">
      <div class="header-left">
        <div class="assistant-avatar">
          <svg viewBox="0 0 32 32" width="24" height="24">
            <circle cx="16" cy="16" r="14" fill="none" stroke="currentColor" stroke-width="2"/>
            <path d="M10 20 L16 10 L22 20 Z" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round"/>
          </svg>
        </div>
        <div class="header-info">
          <h1 class="header-title">反诈先锋守护者</h1>
          <span class="header-status">在线 · 随时为您服务</span>
        </div>
      </div>
      <div class="header-right">
        <span class="model-tag">DeepSeek 驱动</span>
      </div>
    </header>

    <!-- 消息区域 -->
    <div class="chat-messages" ref="messagesContainer">
      <!-- 欢迎消息 -->
      <div class="message assistant-msg" v-if="messages.length === 0">
        <div class="msg-avatar assistant">🛡️</div>
        <div class="msg-bubble assistant-bubble">
          <p class="msg-text">你好！我是<b>反诈先锋守护者</b>，你的 AI 反诈助手。</p>
          <p class="msg-text">我可以帮你：</p>
          <ul class="welcome-list">
            <li>解答各类诈骗手法和防范知识</li>
            <li>分析可疑链接和信息的风险</li>
            <li>提供紧急情况下的应对建议</li>
          </ul>
          <p class="msg-text">你也可以尝试说"我绝对不会被骗"来挑战<b>情景模拟</b>。</p>
        </div>
      </div>

      <!-- 消息列表 -->
      <div v-for="(msg, i) in messages" :key="i"
           class="message" :class="msg.role === 'user' ? 'user-msg' : 'assistant-msg'">
        <div class="msg-avatar" :class="msg.role">
          {{ msg.role === 'user' ? '👤' : '🛡️' }}
        </div>
        <div class="msg-bubble" :class="msg.role + '-bubble'">
          <!-- 紧急阻断消息 -->
          <div v-if="msg.isAlert" class="alert-block">
            <div class="alert-icon-row">
              <span class="alert-icon">⚠️</span>
              <span class="alert-title">紧急风险提醒</span>
            </div>
            <p class="alert-text" v-html="msg.text"></p>
          </div>
          <p v-else class="msg-text" v-html="msg.text"></p>
        </div>
      </div>

      <!-- 加载指示器 -->
      <div v-if="isLoading" class="message assistant-msg">
        <div class="msg-avatar assistant">🛡️</div>
        <div class="msg-bubble assistant-bubble">
          <div class="typing-indicator">
            <span></span><span></span><span></span>
          </div>
        </div>
      </div>
    </div>

    <!-- 输入区域 -->
    <div class="chat-input-area">
      <div class="input-wrapper">
        <input
          v-model="inputText"
          type="text"
          placeholder="输入你的问题，例如：什么是杀猪盘？"
          @keyup.enter="sendMessage"
          :disabled="isLoading"
          class="chat-input"
        />
        <button class="send-btn" @click="sendMessage" :disabled="!inputText.trim() || isLoading">
          <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M22 2L11 13M22 2L15 22L11 13M22 2L2 9L11 13"/>
          </svg>
        </button>
      </div>
      <p class="input-hint">按 Enter 发送 · 如遇紧急情况请拨打 110</p>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const messages = ref([])
const inputText = ref('')
const isLoading = ref(false)
const messagesContainer = ref(null)

const SENSITIVE_WORDS = ['转账', '安全账户', '验证码', '刷单', '中奖', '贷款', '裸聊']

function checkSensitiveWords(text) {
  for (const word of SENSITIVE_WORDS) {
    if (text.includes(word)) return word
  }
  return null
}

function checkSimulationTrigger(text) {
  const triggers = ['不会被骗', '骗不了我', '我很聪明', '试试看', '情景模拟']
  return triggers.some(t => text.includes(t))
}

async function sendMessage() {
  const text = inputText.value.trim()
  if (!text) return

  messages.value.push({ role: 'user', text })
  inputText.value = ''
  await scrollToBottom()

  // 检查敏感词 → 紧急阻断
  const sensitiveWord = checkSensitiveWords(text)
  if (sensitiveWord) {
    isLoading.value = true
    await delay(500)
    messages.value.push({
      role: 'assistant',
      isAlert: true,
      text: `检测到高风险关键词"<b>${sensitiveWord}</b>"！<br><br>`
        + `<b>请立即停止任何转账操作！</b><br>`
        + `正规机关不会通过电话/短信要求转账。<br><br>`
        + `如已转账，请立即拨打 <b>110</b> 报警，并联系银行冻结账户。<br>`
        + `反诈热线：<b>96110</b>`
    })
    isLoading.value = false
    await scrollToBottom()
    return
  }

  // 检查是否触发情景模拟
  if (checkSimulationTrigger(text)) {
    isLoading.value = true
    await delay(800)
    messages.value.push({
      role: 'assistant',
      text: '哦？你觉得自己不会被骗？那我们来做一个<b>沉浸式情景模拟</b>吧。<br><br>'
        + '接下来你将进入一个真实的诈骗场景还原——<b>《深渊契约》</b>。<br>'
        + '看看你能否识破所有陷阱……<br><br>'
        + '<i>3 秒后进入模拟……</i>'
    })
    isLoading.value = false
    await scrollToBottom()
    await delay(3000)
    router.push('/')
    return
  }

  // 正常对话 → 调用后端 AI
  isLoading.value = true
  try {
    const res = await fetch('/api/chat/ask', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question: text })
    })

    if (res.ok) {
      const data = await res.json()
      messages.value.push({ role: 'assistant', text: data.answer })
    } else {
      messages.value.push({
        role: 'assistant',
        text: '抱歉，我暂时无法回答这个问题。请稍后再试，或拨打反诈热线 96110 获取帮助。'
      })
    }
  } catch (e) {
    messages.value.push({
      role: 'assistant',
      text: '网络连接异常，请检查网络后重试。如遇紧急情况请拨打 110。'
    })
  } finally {
    isLoading.value = false
    await scrollToBottom()
  }
}

function delay(ms) {
  return new Promise(r => setTimeout(r, ms))
}

async function scrollToBottom() {
  await nextTick()
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}
</script>

<style scoped>
.chat-page {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: #f8f9fc;
}

/* ======== Header ======== */
.chat-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 28px;
  background: #fff;
  border-bottom: 1px solid #e5e7eb;
  flex-shrink: 0;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 14px;
}

.assistant-avatar {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #6366f1, #4f46e5);
  border-radius: 10px;
  color: #fff;
}

.header-info {
  display: flex;
  flex-direction: column;
}

.header-title {
  font-size: 1rem;
  font-weight: 700;
  color: #1f2937;
  margin: 0;
}

.header-status {
  font-size: 0.75rem;
  color: #10b981;
}

.model-tag {
  font-size: 0.7rem;
  padding: 4px 10px;
  background: #f3f4f6;
  color: #6b7280;
  border-radius: 12px;
  border: 1px solid #e5e7eb;
}

/* ======== Messages ======== */
.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 24px 28px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.message {
  display: flex;
  gap: 12px;
  max-width: 85%;
  animation: msgIn 0.3s ease;
}

@keyframes msgIn {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}

.user-msg {
  align-self: flex-end;
  flex-direction: row-reverse;
}

.assistant-msg {
  align-self: flex-start;
}

.msg-avatar {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.1rem;
  flex-shrink: 0;
}

.msg-avatar.user {
  background: #e0e7ff;
}

.msg-avatar.assistant {
  background: linear-gradient(135deg, #dbeafe, #ede9fe);
}

.msg-bubble {
  padding: 14px 18px;
  border-radius: 16px;
  line-height: 1.7;
  font-size: 0.9rem;
}

.user-bubble {
  background: #6366f1;
  color: #fff;
  border-bottom-right-radius: 4px;
}

.assistant-bubble {
  background: #fff;
  color: #374151;
  border: 1px solid #e5e7eb;
  border-bottom-left-radius: 4px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}

.msg-text {
  margin: 0 0 6px 0;
}
.msg-text:last-child {
  margin-bottom: 0;
}

.welcome-list {
  margin: 8px 0;
  padding-left: 20px;
  color: #6b7280;
  font-size: 0.85rem;
}

.welcome-list li {
  margin: 4px 0;
}

/* 紧急阻断 */
.alert-block {
  background: #fef2f2;
  border: 2px solid #ef4444;
  border-radius: 10px;
  padding: 14px 16px;
}

.alert-icon-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
}

.alert-icon {
  font-size: 1.2rem;
}

.alert-title {
  font-size: 0.95rem;
  font-weight: 700;
  color: #dc2626;
}

.alert-text {
  margin: 0;
  color: #7f1d1d;
  font-size: 0.85rem;
  line-height: 1.8;
}

/* 打字指示器 */
.typing-indicator {
  display: flex;
  gap: 5px;
  padding: 4px 0;
}

.typing-indicator span {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #6366f1;
  animation: typingBounce 1.4s ease-in-out infinite;
}

.typing-indicator span:nth-child(2) { animation-delay: 0.2s; }
.typing-indicator span:nth-child(3) { animation-delay: 0.4s; }

@keyframes typingBounce {
  0%, 80%, 100% { transform: translateY(0); opacity: 0.4; }
  40% { transform: translateY(-6px); opacity: 1; }
}

/* ======== Input Area ======== */
.chat-input-area {
  padding: 16px 28px 20px;
  background: #fff;
  border-top: 1px solid #e5e7eb;
  flex-shrink: 0;
}

.input-wrapper {
  display: flex;
  gap: 10px;
  align-items: center;
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 14px;
  padding: 6px 6px 6px 18px;
  transition: border-color 0.2s, box-shadow 0.2s;
}

.input-wrapper:focus-within {
  border-color: #6366f1;
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
}

.chat-input {
  flex: 1;
  border: none;
  background: transparent;
  font-size: 0.9rem;
  color: #1f2937;
  outline: none;
  padding: 10px 0;
  font-family: inherit;
}

.chat-input::placeholder {
  color: #9ca3af;
}

.send-btn {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  border: none;
  background: linear-gradient(135deg, #6366f1, #4f46e5);
  color: #fff;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
  flex-shrink: 0;
}

.send-btn:hover:not(:disabled) {
  transform: scale(1.05);
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.4);
}

.send-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.input-hint {
  margin: 8px 0 0;
  font-size: 0.7rem;
  color: #9ca3af;
  text-align: center;
}
</style>
