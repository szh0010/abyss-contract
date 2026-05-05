<template>
  <transition name="frozen-fade">
    <div v-if="visible" class="frozen-overlay">
      <!-- 扫描线特效 -->
      <div class="scanlines"></div>

      <!-- 系统操作系统风格弹窗 -->
      <div class="system-window">
        <!-- 标题栏 -->
        <div class="window-titlebar">
          <div class="titlebar-icon">⚠</div>
          <div class="titlebar-text">SYSTEM ALERT · 系统警报</div>
          <div class="titlebar-controls">
            <span class="ctrl-btn disabled">_</span>
            <span class="ctrl-btn disabled">□</span>
            <span class="ctrl-btn disabled">×</span>
          </div>
        </div>

        <!-- 内容区 -->
        <div class="window-body">
          <!-- 告警图标 + 主标题 -->
          <div class="alert-header">
            <div class="alert-icon">
              <svg viewBox="0 0 48 48" width="48" height="48">
                <circle cx="24" cy="24" r="22" fill="none" stroke="#ff3333" stroke-width="2"/>
                <text x="24" y="33" text-anchor="middle" fill="#ff3333" font-size="28" font-weight="bold">!</text>
              </svg>
            </div>
            <div class="alert-titles">
              <h2 class="alert-title-1">【提现通道已关闭】</h2>
              <h3 class="alert-title-2">【账户涉嫌违规已被冻结】</h3>
            </div>
          </div>

          <!-- 系统信息 -->
          <div class="system-info">
            <div class="info-row">
              <span class="info-label">状态:</span>
              <span class="info-value frozen">FROZEN / 已冻结</span>
            </div>
            <div class="info-row">
              <span class="info-label">原因:</span>
              <span class="info-value">涉嫌参与网络赌博</span>
            </div>
            <div class="info-row">
              <span class="info-label">代码:</span>
              <span class="info-value">0x00ABYSS-FINAL</span>
            </div>
            <div class="info-row">
              <span class="info-label">可提现余额:</span>
              <span class="info-value zero">¥ 0.00</span>
            </div>
          </div>

          <!-- 分隔线 -->
          <div class="divider"></div>

          <!-- 打字机文字区 -->
          <div class="typewriter-area">
            <p class="typed-line" v-if="typedStage >= 1">
              <span class="speaker">[K]</span>
              <span class="typed-content">{{ typedText1 }}<span v-if="typingStage === 1" class="cursor">▊</span></span>
            </p>
            <p class="typed-line" v-if="typedStage >= 2">
              <span class="speaker">[K]</span>
              <span class="typed-content">{{ typedText2 }}<span v-if="typingStage === 2" class="cursor">▊</span></span>
            </p>
            <p class="typed-line warning-line" v-if="typedStage >= 3">
              <span class="speaker alert">[⚠]</span>
              <span class="typed-content">{{ typedText3 }}<span v-if="typingStage === 3" class="cursor">▊</span></span>
            </p>
          </div>

          <!-- 按钮区（打完字后才出现） -->
          <div class="button-row" v-if="showButton">
            <button class="restart-btn" @click="handleRestart">
              <span class="btn-icon">⚐</span>
              【 一 键 举 报 并 重 新 开 始 】
            </button>
            <div class="hotline">
              报警: 110 &nbsp;|&nbsp; 反诈热线: 96110 &nbsp;|&nbsp; 法律援助: 12348
            </div>
          </div>
        </div>
      </div>
    </div>
  </transition>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue'

const props = defineProps({
  visible: { type: Boolean, default: false }
})

const emit = defineEmits(['restart'])

const typedText1 = ref('')
const typedText2 = ref('')
const typedText3 = ref('')
const typingStage = ref(0)
const typedStage = ref(0)
const showButton = ref(false)

const line1 = '在这场名为贪婪的游戏里，底牌并不重要。'
const line2 = '因为庄家，永远不会输。'
const line3 = '请警惕网络涉诈赌博与套路贷陷阱！'

function typeLine(text, targetRef, speed = 60) {
  return new Promise((resolve) => {
    let i = 0
    const timer = setInterval(() => {
      if (i < text.length) {
        targetRef.value += text[i]
        i++
      } else {
        clearInterval(timer)
        resolve()
      }
    }, speed)
  })
}

async function startTyping() {
  typedText1.value = ''
  typedText2.value = ''
  typedText3.value = ''
  typedStage.value = 0
  typingStage.value = 0
  showButton.value = false

  await new Promise(r => setTimeout(r, 800))

  typedStage.value = 1
  typingStage.value = 1
  await typeLine(line1, typedText1, 70)

  await new Promise(r => setTimeout(r, 600))

  typedStage.value = 2
  typingStage.value = 2
  await typeLine(line2, typedText2, 70)

  await new Promise(r => setTimeout(r, 800))

  typedStage.value = 3
  typingStage.value = 3
  await typeLine(line3, typedText3, 55)

  typingStage.value = 0
  await new Promise(r => setTimeout(r, 600))
  showButton.value = true
}

function handleRestart() {
  emit('restart')
}

watch(() => props.visible, (val) => {
  if (val) {
    startTyping()
  }
})

onMounted(() => {
  if (props.visible) {
    startTyping()
  }
})
</script>

<style scoped>
/* ======== 遮罩 ======== */
.frozen-overlay {
  position: fixed;
  inset: 0;
  z-index: 9999;
  background: #000;
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: 'Courier New', 'Consolas', monospace;
  pointer-events: all;
}

/* 扫描线特效 */
.scanlines {
  position: absolute;
  inset: 0;
  background: repeating-linear-gradient(
    0deg,
    rgba(0, 0, 0, 0) 0px,
    rgba(0, 0, 0, 0) 2px,
    rgba(255, 255, 255, 0.03) 3px,
    rgba(255, 255, 255, 0.03) 4px
  );
  pointer-events: none;
  animation: scanlinesMove 8s linear infinite;
}

@keyframes scanlinesMove {
  0% { background-position: 0 0; }
  100% { background-position: 0 100px; }
}

/* ======== 系统窗口 ======== */
.system-window {
  width: 92%;
  max-width: 640px;
  background: #0a0a0a;
  border: 2px solid #ff3333;
  box-shadow:
    0 0 40px rgba(255, 51, 51, 0.5),
    0 0 120px rgba(255, 51, 51, 0.2),
    inset 0 0 30px rgba(255, 0, 0, 0.1);
  animation: windowIn 0.6s cubic-bezier(0.19, 1, 0.22, 1);
  position: relative;
  z-index: 2;
}

@keyframes windowIn {
  0% {
    opacity: 0;
    transform: scale(0.9);
    filter: blur(8px);
  }
  100% {
    opacity: 1;
    transform: scale(1);
    filter: blur(0);
  }
}

/* ======== 标题栏 ======== */
.window-titlebar {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 12px;
  background: linear-gradient(90deg, #3a0000, #6a0000, #3a0000);
  border-bottom: 1px solid #ff3333;
}

.titlebar-icon {
  color: #ffeb3b;
  font-size: 1rem;
  animation: iconBlink 1s ease-in-out infinite;
}

@keyframes iconBlink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}

.titlebar-text {
  flex: 1;
  color: #ff9999;
  font-size: 0.85rem;
  letter-spacing: 0.1rem;
  text-transform: uppercase;
}

.titlebar-controls {
  display: flex;
  gap: 6px;
}

.ctrl-btn {
  width: 20px;
  height: 20px;
  line-height: 18px;
  text-align: center;
  background: #1a0a0a;
  border: 1px solid #5a0000;
  color: #666;
  font-size: 0.75rem;
}

.ctrl-btn.disabled {
  cursor: not-allowed;
  opacity: 0.5;
}

/* ======== 窗口内容 ======== */
.window-body {
  padding: 30px;
}

.alert-header {
  display: flex;
  align-items: center;
  gap: 20px;
  margin-bottom: 25px;
}

.alert-icon {
  flex-shrink: 0;
  animation: iconPulse 1.5s ease-in-out infinite;
}

@keyframes iconPulse {
  0%, 100% { transform: scale(1); filter: drop-shadow(0 0 8px rgba(255, 51, 51, 0.6)); }
  50% { transform: scale(1.15); filter: drop-shadow(0 0 20px rgba(255, 51, 51, 1)); }
}

.alert-titles {
  flex: 1;
}

.alert-title-1 {
  color: #ff3333;
  font-size: 1.3rem;
  margin: 0 0 6px 0;
  letter-spacing: 0.2rem;
  text-shadow: 0 0 15px rgba(255, 51, 51, 0.6);
  animation: titleFlicker 3s ease-in-out infinite;
}

.alert-title-2 {
  color: #ff6666;
  font-size: 1rem;
  margin: 0;
  letter-spacing: 0.15rem;
  font-weight: 400;
}

@keyframes titleFlicker {
  0%, 95%, 100% { opacity: 1; }
  96% { opacity: 0.4; }
  97% { opacity: 1; }
  98% { opacity: 0.6; }
}

/* ======== 系统信息 ======== */
.system-info {
  background: #1a0505;
  border: 1px solid #3a0000;
  padding: 15px 18px;
  margin-bottom: 20px;
  font-size: 0.85rem;
}

.info-row {
  display: flex;
  justify-content: space-between;
  padding: 4px 0;
  border-bottom: 1px dashed #2a0000;
}

.info-row:last-child {
  border-bottom: none;
}

.info-label {
  color: #888;
  letter-spacing: 0.1rem;
}

.info-value {
  color: #ccc;
  font-family: 'Courier New', monospace;
}

.info-value.frozen {
  color: #ff3333;
  font-weight: 700;
  text-shadow: 0 0 8px rgba(255, 51, 51, 0.5);
}

.info-value.zero {
  color: #ff6666;
  font-weight: 700;
  font-size: 1rem;
}

/* ======== 分隔线 ======== */
.divider {
  height: 1px;
  background: linear-gradient(90deg, transparent, #ff3333, transparent);
  margin: 20px 0;
}

/* ======== 打字机区 ======== */
.typewriter-area {
  min-height: 140px;
  font-size: 0.95rem;
  line-height: 1.9;
}

.typed-line {
  margin: 8px 0;
  color: #e0e0e0;
}

.typed-line.warning-line {
  color: #ffeb3b;
  font-weight: 700;
  margin-top: 14px;
  padding: 8px 12px;
  background: rgba(255, 235, 59, 0.05);
  border-left: 3px solid #ffeb3b;
}

.speaker {
  color: #ff3333;
  font-weight: 700;
  margin-right: 8px;
  letter-spacing: 0.1rem;
}

.speaker.alert {
  color: #ffeb3b;
}

.typed-content {
  color: inherit;
}

.cursor {
  display: inline-block;
  color: #ff3333;
  animation: cursorBlink 0.7s step-end infinite;
  margin-left: 2px;
}

@keyframes cursorBlink {
  0%, 50% { opacity: 1; }
  51%, 100% { opacity: 0; }
}

/* ======== 按钮区 ======== */
.button-row {
  margin-top: 28px;
  animation: btnIn 0.6s ease;
}

@keyframes btnIn {
  from { opacity: 0; transform: translateY(15px); }
  to { opacity: 1; transform: translateY(0); }
}

.restart-btn {
  width: 100%;
  padding: 16px;
  background: linear-gradient(180deg, #1a1a2e, #0a0a15);
  border: 2px solid #ffeb3b;
  color: #ffeb3b;
  font-size: 1rem;
  font-family: inherit;
  letter-spacing: 0.3rem;
  cursor: pointer;
  transition: all 0.3s;
  margin-bottom: 15px;
}

.restart-btn:hover {
  background: linear-gradient(180deg, #2a2a3e, #1a1a25);
  box-shadow: 0 0 25px rgba(255, 235, 59, 0.5);
  color: #fff;
}

.btn-icon {
  display: inline-block;
  margin-right: 8px;
  animation: flagWave 1.5s ease-in-out infinite;
}

@keyframes flagWave {
  0%, 100% { transform: rotate(-5deg); }
  50% { transform: rotate(5deg); }
}

.hotline {
  text-align: center;
  font-size: 0.75rem;
  color: #ff6666;
  letter-spacing: 0.05rem;
  padding: 8px;
  border-top: 1px dashed #3a0000;
}

/* ======== 过渡 ======== */
.frozen-fade-enter-active {
  transition: opacity 0.8s ease;
}
.frozen-fade-leave-active {
  transition: opacity 0.3s ease;
}
.frozen-fade-enter-from,
.frozen-fade-leave-to {
  opacity: 0;
}
</style>
