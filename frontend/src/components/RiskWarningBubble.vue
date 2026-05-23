<!--
  RiskWarningBubble · 流式琥珀色玻璃气泡警告
  - 用 v-model:visible 双向绑定开关,父组件直接 visible.value = true/false
  - 文本通过 :message 注入
  - 平滑推开:进入时从下方上浮 + 撑开高度;离开时高度收回
  - 不使用遮罩层 / 不打断对话气流,只在聊天流末尾"流式插入"
-->
<template>
  <transition name="risk-bubble">
    <div
      v-if="visible"
      class="risk-bubble"
      role="status"
      aria-live="polite"
    >
      <div class="risk-icon" aria-hidden="true">⚠️</div>
      <div class="risk-body">
        <span class="risk-tag">REAL-TIME RISK ANALYSIS</span>
        <h4 class="risk-title">实时反诈预警</h4>
        <p class="risk-text">{{ message }}</p>
      </div>
      <button
        type="button"
        class="risk-close"
        @click="close"
        aria-label="关闭预警"
      >×</button>
    </div>
  </transition>
</template>

<script setup>
import { defineProps, defineEmits } from 'vue'

const props = defineProps({
  visible: { type: Boolean, default: false },
  message: { type: String, default: '' },
})

const emit = defineEmits(['update:visible'])

function close() {
  emit('update:visible', false)
}
</script>

<style scoped>
/* 琥珀色液态玻璃气泡 · 警示但不暴力 */
.risk-bubble {
  display: grid;
  grid-template-columns: auto 1fr auto;
  align-items: flex-start;
  gap: 14px;
  padding: 16px 18px;
  border-radius: 22px;
  background: linear-gradient(
    135deg,
    rgba(255, 222, 168, 0.78) 0%,
    rgba(255, 196, 130, 0.72) 60%,
    rgba(255, 168, 100, 0.7) 100%
  );
  backdrop-filter: blur(22px);
  -webkit-backdrop-filter: blur(22px);
  border: 1px solid rgba(255, 255, 255, 0.65);
  box-shadow:
    inset 0 2px 4px rgba(255, 255, 255, 0.95),
    inset 0 -2px 6px rgba(217, 119, 6, 0.18),
    0 14px 36px rgba(217, 119, 6, 0.22);
  position: relative;
  overflow: hidden;
}

/* 顶部一道高光 */
.risk-bubble::before {
  content: '';
  position: absolute;
  inset: 0 0 auto 0;
  height: 1px;
  background: linear-gradient(
    90deg,
    transparent,
    rgba(255, 255, 255, 0.95),
    transparent
  );
}

.risk-icon {
  width: 36px;
  height: 36px;
  border-radius: 12px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 1.35rem;
  background: rgba(255, 255, 255, 0.55);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.9);
  flex-shrink: 0;
  animation: riskIconPulse 1.6s ease-in-out infinite;
}
@keyframes riskIconPulse {
  0%, 100% { transform: scale(1);    box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.9), 0 0 0 0 rgba(217, 119, 6, 0.4); }
  50%      { transform: scale(1.08); box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.9), 0 0 0 8px rgba(217, 119, 6, 0); }
}

.risk-body {
  min-width: 0;
}
.risk-tag {
  display: block;
  font-family: 'SF Mono', ui-monospace, monospace;
  font-size: 0.66rem;
  letter-spacing: 0.28em;
  color: #8a4d0a;
}
.risk-title {
  margin: 4px 0 6px;
  font-size: 0.96rem;
  font-weight: 700;
  letter-spacing: 0.06em;
  color: #5b2f04;
}
.risk-text {
  margin: 0;
  font-size: 0.9rem;
  line-height: 1.65;
  color: #4a2700;
  word-break: break-word;
}
.risk-close {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  border: 1px solid rgba(255, 255, 255, 0.7);
  background: rgba(255, 255, 255, 0.65);
  font-size: 1rem;
  color: #8a4d0a;
  cursor: pointer;
  line-height: 1;
  flex-shrink: 0;
}
.risk-close:hover { background: rgba(255, 255, 255, 0.85); }

/* —— 流式入场:防抖动 + 平滑撑开 —— */
.risk-bubble-enter-active {
  transition:
    max-height 0.45s cubic-bezier(0.25, 1.5, 0.5, 1),
    opacity 0.35s ease,
    transform 0.45s cubic-bezier(0.25, 1.5, 0.5, 1),
    margin 0.35s ease,
    padding 0.35s ease;
  overflow: hidden;
}
.risk-bubble-leave-active {
  transition:
    max-height 0.35s cubic-bezier(0.4, 0, 0.6, 1),
    opacity 0.25s ease,
    transform 0.35s cubic-bezier(0.4, 0, 0.6, 1),
    margin 0.3s ease,
    padding 0.3s ease;
  overflow: hidden;
}
.risk-bubble-enter-from,
.risk-bubble-leave-to {
  opacity: 0;
  transform: translateY(8px) scale(0.985);
  max-height: 0;
  margin-top: 0;
  margin-bottom: 0;
  padding-top: 0;
  padding-bottom: 0;
}
.risk-bubble-enter-to,
.risk-bubble-leave-from {
  opacity: 1;
  transform: translateY(0) scale(1);
  max-height: 320px;
}
</style>
