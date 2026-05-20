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
        <span class="model-tag">自研智能体驱动</span>
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
          <!-- 普通消息:逐字打字机 + 闪烁光标 -->
          <p
            v-else
            class="msg-text"
            :class="{ cursor: msg.isTyping }"
            v-html="msg.text"
          ></p>
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
          :placeholder="inputLocked ? '反诈守护者正在打字…请稍候' : '输入你的问题,例如:什么是杀猪盘?'"
          @keyup.enter="sendMessage"
          :disabled="inputLocked"
          class="chat-input"
        />
        <button class="send-btn" @click="sendMessage" :disabled="!inputText.trim() || inputLocked">
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
import { ref, computed, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import http from '../services/http'

const router = useRouter()
const messages = ref([])
const inputText = ref('')
const isLoading = ref(false)
const inputLocked = ref(false)
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

const PUNCT_PAUSE = ['，', '。', '！', '？', '\n']

/**
 * 真·逐字打字机
 * 关键点:必须通过 messages.value[idx] 访问 reactive proxy 再 += ,
 *        否则 Vue 的依赖追踪不到 setter,会导致"光标先闪很久才一次性出现全文"。
 */
function typewriteAssistant(fullText) {
  // 1. 推入空壳气泡,inputLocked 立刻置 true
  inputLocked.value = true
  messages.value.push({
    role: 'assistant',
    text: '',
    isTyping: true,
  })
  const idx = messages.value.length - 1
  const targetMessage = messages.value[idx]   // ← reactive proxy

  // 2. HTML 段落直接整段呈现,避免标签被切坏
  if (fullText.includes('<') && fullText.includes('>')) {
    targetMessage.text = fullText
    targetMessage.isTyping = false
    inputLocked.value = false
    scrollToBottom()
    return
  }

  // 3. 逐字响应式追加
  let i = 0
  const type = () => {
    if (i < fullText.length) {
      const ch = fullText.charAt(i)
      targetMessage.text += ch                // ← 触发响应式
      i++
      let d = 30 + Math.random() * 30
      if (PUNCT_PAUSE.includes(ch)) d += 150
      scrollToBottom()
      setTimeout(type, d)
    } else {
      targetMessage.isTyping = false
      inputLocked.value = false
      scrollToBottom()
    }
  }
  type()
}

async function sendMessage() {
  if (inputLocked.value) return
  const text = inputText.value.trim()
  if (!text) return

  messages.value.push({ role: 'user', text })
  inputText.value = ''
  await scrollToBottom()

  // 敏感词 → 紧急阻断(HTML,瞬时)
  const sensitiveWord = checkSensitiveWords(text)
  if (sensitiveWord) {
    isLoading.value = true
    inputLocked.value = true
    await delay(500)
    messages.value.push({
      role: 'assistant',
      isAlert: true,
      text: `检测到高风险关键词"<b>${sensitiveWord}</b>"!<br><br>`
        + `<b>请立即停止任何转账操作!</b><br>`
        + `正规机关不会通过电话/短信要求转账。<br><br>`
        + `如已转账,请立即拨打 <b>110</b> 报警,并联系银行冻结账户。<br>`
        + `反诈热线:<b>96110</b>`
    })
    isLoading.value = false
    inputLocked.value = false
    await scrollToBottom()
    return
  }

  // 触发情景模拟(HTML,瞬时 + 跳转)
  if (checkSimulationTrigger(text)) {
    isLoading.value = true
    inputLocked.value = true
    await delay(800)
    messages.value.push({
      role: 'assistant',
      text: '哦?你觉得自己不会被骗?那我们来做一个<b>沉浸式情景模拟</b>吧。<br><br>'
        + '接下来你将进入一个真实的诈骗场景还原——<b>《深渊契约》</b>。<br>'
        + '看看你能否识破所有陷阱……<br><br>'
        + '<i>3 秒后进入模拟……</i>'
    })
    isLoading.value = false
    await scrollToBottom()
    await delay(3000)
    inputLocked.value = false
    router.push('/game')
    return
  }

  // 正常对话 → AI 逐字打字
  isLoading.value = true
  inputLocked.value = true
  try {
    const { data } = await http.post('/chat/ask', { question: text })
    isLoading.value = false
    typewriteAssistant(data.answer || '抱歉,出现异常。')
  } catch (e) {
    isLoading.value = false
    if (e?.response?.status === 401) {
      inputLocked.value = false
      return
    }
    typewriteAssistant(
      e?.response?.data?.detail
        ? `抱歉:${e.response.data.detail}`
        : '网络连接异常,请检查网络后重试。如遇紧急情况请拨打 110。'
    )
  } finally {
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
/* ============================================================
   反诈客服聊天（暖色版）· 液态玻璃 + 弹簧交互
============================================================ */
.chat-page {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: transparent;
  color: #2d2416;
}

/* ======== Header ======== */
.chat-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 26px;
  background: rgba(255, 255, 255, 0.4);
  backdrop-filter: blur(16px) saturate(150%);
  -webkit-backdrop-filter: blur(16px) saturate(150%);
  border-bottom: 1px solid rgba(180, 130, 80, 0.12);
  flex-shrink: 0;
}

.header-left { display: flex; align-items: center; gap: 14px; }

.assistant-avatar {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 12px;
  color: #fff;
  background: linear-gradient(135deg, #ffb578, #ff7a50);
  box-shadow:
    0 10px 22px rgba(255, 122, 80, 0.3),
    inset 0 1px 0 rgba(255, 255, 255, 0.5);
}

.header-info { display: flex; flex-direction: column; }
.header-title {
  font-size: 1rem;
  font-weight: 600;
  color: #2d2416;
  letter-spacing: 0.04em;
  margin: 0;
}
.header-status {
  font-size: 0.72rem;
  color: #5fbf8a;
  font-weight: 500;
  letter-spacing: 0.05em;
}
.header-status::before {
  content: '●';
  margin-right: 4px;
  font-size: 0.6rem;
}

.model-tag {
  font-size: 0.7rem;
  padding: 5px 12px;
  background: rgba(255, 255, 255, 0.55);
  color: #ff7a50;
  border-radius: 10px;
  font-weight: 500;
  letter-spacing: 0.06em;
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.9),
    inset 0 0 0 0.5px rgba(255, 154, 86, 0.32);
}

/* ======== Messages ======== */
.chat-messages {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding: 28px 32px;
  display: flex;
  flex-direction: column;
  gap: 22px;
}
.chat-messages::-webkit-scrollbar { width: 6px; }
.chat-messages::-webkit-scrollbar-thumb {
  background: rgba(180, 130, 80, 0.22);
  border-radius: 3px;
}

.message {
  display: flex;
  gap: 12px;
  max-width: 82%;
  animation: msgIn 0.35s cubic-bezier(0.22, 1, 0.36, 1);
}
@keyframes msgIn {
  from { opacity: 0; transform: translateY(6px); }
  to   { opacity: 1; transform: translateY(0); }
}

.user-msg { align-self: flex-end; flex-direction: row-reverse; }
.assistant-msg { align-self: flex-start; }

.msg-avatar {
  width: 38px;
  height: 38px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.05rem;
  flex-shrink: 0;
}
.msg-avatar.user {
  background: rgba(255, 255, 255, 0.6);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.95),
    inset 0 0 0 0.5px rgba(180, 130, 80, 0.22);
}
.msg-avatar.assistant {
  background: linear-gradient(135deg, rgba(255, 181, 120, 0.4), rgba(255, 122, 80, 0.4));
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.5),
    inset 0 0 0 0.5px rgba(255, 154, 86, 0.4);
}

.msg-bubble {
  padding: 14px 18px;
  border-radius: 18px;
  line-height: 1.75;
  font-size: 0.92rem;
  font-weight: 400;
  backdrop-filter: blur(12px) saturate(150%);
  -webkit-backdrop-filter: blur(12px) saturate(150%);
}

.user-bubble {
  background: linear-gradient(135deg, rgba(255, 181, 120, 0.92), rgba(255, 122, 80, 0.92));
  color: #fff;
  border-bottom-right-radius: 6px;
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.35),
    0 10px 22px rgba(255, 122, 80, 0.25);
}

.assistant-bubble {
  background: rgba(255, 255, 255, 0.62);
  color: #463727;
  border-bottom-left-radius: 6px;
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.95),
    inset 0 0 0 0.5px rgba(180, 130, 80, 0.15),
    0 8px 20px rgba(200, 140, 80, 0.08);
}

.msg-text { margin: 0 0 6px 0; }
.msg-text:last-child { margin-bottom: 0; }
.msg-text b { color: #ff7a50; font-weight: 600; }
.user-bubble .msg-text b { color: #fff8ec; }

/* 打字机光标 */
.msg-text.cursor::after {
  content: '▌';
  display: inline-block;
  color: #ff7a50;
  animation: blink 1s step-end infinite;
  margin-left: 4px;
  vertical-align: baseline;
  font-weight: 400;
}
@keyframes blink {
  0%, 100% { opacity: 1; }
  50%      { opacity: 0; }
}

.welcome-list {
  margin: 8px 0 8px 2px;
  padding-left: 20px;
  color: #7e6a4f;
  font-size: 0.86rem;
}
.welcome-list li { margin: 4px 0; }

/* ======== 紧急阻断 ======== */
.alert-block {
  background: linear-gradient(135deg, rgba(255, 225, 220, 0.7), rgba(255, 200, 195, 0.5));
  border-radius: 14px;
  padding: 16px 18px;
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.85),
    inset 0 0 0 0.5px rgba(217, 74, 103, 0.32),
    0 10px 26px rgba(217, 74, 103, 0.15);
}
.alert-icon-row {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
}
.alert-icon { font-size: 1.2rem; }
.alert-title {
  font-size: 0.95rem;
  font-weight: 600;
  color: #a8334a;
  letter-spacing: 0.08em;
}
.alert-text {
  margin: 0;
  color: #7a2a3a;
  font-size: 0.86rem;
  line-height: 1.85;
  font-weight: 400;
}
.alert-text b { color: #a8334a; font-weight: 600; }

/* ======== 打字指示器 ======== */
.typing-indicator {
  display: flex;
  gap: 5px;
  padding: 4px 0;
}
.typing-indicator span {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #ff9a56;
  box-shadow: 0 0 8px rgba(255, 154, 86, 0.55);
  animation: typingBounce 1.4s ease-in-out infinite;
}
.typing-indicator span:nth-child(2) { animation-delay: 0.2s; }
.typing-indicator span:nth-child(3) { animation-delay: 0.4s; }
@keyframes typingBounce {
  0%, 80%, 100% { transform: translateY(0); opacity: 0.4; }
  40%           { transform: translateY(-6px); opacity: 1; }
}

/* ======== Input Area ======== */
.chat-input-area {
  padding: 16px 26px 20px;
  background: rgba(255, 255, 255, 0.4);
  backdrop-filter: blur(16px) saturate(150%);
  -webkit-backdrop-filter: blur(16px) saturate(150%);
  border-top: 1px solid rgba(180, 130, 80, 0.12);
  flex-shrink: 0;
}

.input-wrapper {
  display: flex;
  gap: 10px;
  align-items: center;
  background: rgba(255, 255, 255, 0.7);
  border-radius: 16px;
  padding: 6px 6px 6px 18px;
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.95),
    inset 0 0 0 0.5px rgba(180, 130, 80, 0.18),
    0 6px 18px rgba(200, 130, 70, 0.08);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}
.input-wrapper:focus-within {
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 1),
    inset 0 0 0 0.5px rgba(255, 154, 86, 0.55),
    0 12px 30px rgba(255, 154, 86, 0.2);
}

.chat-input {
  flex: 1;
  border: none;
  background: transparent;
  font-size: 0.95rem;
  color: #2d2416;
  outline: none;
  padding: 12px 0;
  font-family: inherit;
  font-weight: 400;
}
.chat-input::placeholder { color: #b8a583; font-weight: 300; }

/* 发送按钮 · 液态玻璃 + 弹簧 */
.send-btn {
  width: 40px;
  height: 40px;
  border-radius: 12px;
  border: none;
  cursor: pointer;
  color: #fff;
  background: linear-gradient(135deg, #ffb578, #ff7a50);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.45),
    0 10px 22px rgba(255, 122, 80, 0.4);
  transition: transform 0.4s cubic-bezier(0.25, 1.5, 0.5, 1),
              box-shadow 0.3s ease;
}
.send-btn:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.55),
    0 14px 30px rgba(255, 122, 80, 0.55);
}
.send-btn:active:not(:disabled) {
  transform: scale(0.92);
  transition: all 0.4s cubic-bezier(0.25, 1.5, 0.5, 1);
}
.send-btn:disabled { opacity: 0.4; cursor: not-allowed; }

.input-hint {
  margin: 10px 0 0;
  font-size: 0.7rem;
  color: #b8a583;
  text-align: center;
  font-weight: 400;
  letter-spacing: 0.08em;
}
</style>
