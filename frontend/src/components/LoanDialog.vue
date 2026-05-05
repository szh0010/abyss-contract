<template>
  <transition name="loan-fade">
    <div v-if="visible" class="loan-overlay" @click.self="null">
      <!-- 血色光晕背景 -->
      <div class="blood-aura"></div>

      <!-- 契约主体 -->
      <div class="contract-box">
        <!-- 顶部装饰 -->
        <div class="contract-top">
          <div class="seal-icon">契</div>
          <h2 class="contract-title">信用借款协议</h2>
          <div class="contract-subtitle">Credit Loan Agreement</div>
        </div>

        <!-- 分隔线 -->
        <div class="divider-ornament">
          <span class="divider-line"></span>
          <span class="divider-dot">◆</span>
          <span class="divider-line"></span>
        </div>

        <!-- 协议正文 -->
        <div class="contract-body">
          <p class="contract-lead">
            （K 推过来一张烫金边的纸，微笑着递上一支钢笔）
          </p>

          <p class="contract-para">
            看你骨骼惊奇，是块赌石的料。
          </p>

          <p class="contract-para">
            免抵押借你 <span class="highlight-chips">¥100,000</span> 筹码，
          </p>

          <p class="contract-para">
            翻本就在这一把——<span class="highlight-win">赢了全拿走</span>。
          </p>

          <p class="contract-para small-print">
            * 月利率仅 <span class="fake-low">0.3%</span>（年化 <span class="real-high">365%</span>）
          </p>

          <p class="contract-para small-print fine">
            * 本协议一经签订，不可撤销
          </p>
        </div>

        <!-- 签名行 -->
        <div class="signature-row">
          <div class="signature-label">甲方签名：</div>
          <div class="signature-line">
            <span class="signature-placeholder">________________</span>
          </div>
        </div>

        <!-- 同意按钮 -->
        <button class="accept-btn" @click="handleAccept" :disabled="loading">
          <span v-if="!loading" class="btn-text">
            <span class="btn-stamp">✓</span>
            【 同 意 并 借 款 】
          </span>
          <span v-else class="btn-loading">正在生成合同...</span>
        </button>

        <p class="warning-text">
          ⚠ 现实中此类"免抵押高利贷"均为套路贷诈骗
        </p>
      </div>
    </div>
  </transition>
</template>

<script setup>
import { ref } from 'vue'

const props = defineProps({
  visible: { type: Boolean, default: false }
})

const emit = defineEmits(['accept'])
const loading = ref(false)

function handleAccept() {
  loading.value = true
  setTimeout(() => {
    emit('accept')
    loading.value = false
  }, 800)
}
</script>

<style scoped>
/* ======== 遮罩 ======== */
.loan-overlay {
  position: fixed;
  inset: 0;
  z-index: 500;
  background: radial-gradient(circle at center, rgba(30, 0, 0, 0.92), rgba(0, 0, 0, 0.98));
  display: flex;
  align-items: center;
  justify-content: center;
  backdrop-filter: blur(4px);
  font-family: 'Noto Serif SC', 'SimSun', serif;
}

.blood-aura {
  position: absolute;
  width: 600px;
  height: 600px;
  background: radial-gradient(circle, rgba(139, 0, 0, 0.35), transparent 70%);
  animation: auraPulse 3s ease-in-out infinite;
  filter: blur(40px);
}

@keyframes auraPulse {
  0%, 100% { transform: scale(1); opacity: 0.6; }
  50% { transform: scale(1.15); opacity: 1; }
}

/* ======== 契约盒子 ======== */
.contract-box {
  position: relative;
  width: 90%;
  max-width: 520px;
  padding: 40px 45px;
  background: linear-gradient(135deg, #1a0a0a 0%, #2a0808 50%, #1a0a0a 100%);
  border: 2px solid #8b6914;
  box-shadow:
    0 0 60px rgba(139, 0, 0, 0.6),
    inset 0 0 40px rgba(139, 105, 20, 0.15),
    0 20px 80px rgba(0, 0, 0, 0.8);
  animation: contractIn 0.8s cubic-bezier(0.19, 1, 0.22, 1);
}

@keyframes contractIn {
  0% {
    opacity: 0;
    transform: scale(0.85) translateY(30px);
    filter: blur(10px);
  }
  100% {
    opacity: 1;
    transform: scale(1) translateY(0);
    filter: blur(0);
  }
}

/* 四角金色装饰 */
.contract-box::before,
.contract-box::after {
  content: '';
  position: absolute;
  width: 30px;
  height: 30px;
  border: 2px solid #d4af37;
}
.contract-box::before {
  top: 8px;
  left: 8px;
  border-right: none;
  border-bottom: none;
}
.contract-box::after {
  bottom: 8px;
  right: 8px;
  border-left: none;
  border-top: none;
}

/* ======== 顶部 ======== */
.contract-top {
  text-align: center;
  margin-bottom: 25px;
}

.seal-icon {
  display: inline-block;
  width: 60px;
  height: 60px;
  line-height: 56px;
  text-align: center;
  background: radial-gradient(circle, #8b0000, #4a0000);
  border: 3px double #d4af37;
  border-radius: 50%;
  color: #ffd700;
  font-size: 1.8rem;
  font-weight: 700;
  margin-bottom: 15px;
  box-shadow: 0 0 25px rgba(255, 215, 0, 0.4), inset 0 0 15px rgba(255, 215, 0, 0.3);
  animation: sealRotate 8s linear infinite;
}

@keyframes sealRotate {
  to { transform: rotate(360deg); }
}

.contract-title {
  font-size: 1.6rem;
  color: #ffd700;
  letter-spacing: 0.4rem;
  margin: 0 0 4px 0;
  text-shadow: 0 0 15px rgba(255, 215, 0, 0.5);
  font-weight: 700;
}

.contract-subtitle {
  font-size: 0.7rem;
  color: #8b6914;
  letter-spacing: 0.3rem;
  font-family: 'Courier New', monospace;
}

/* ======== 分隔线 ======== */
.divider-ornament {
  display: flex;
  align-items: center;
  gap: 10px;
  margin: 20px 0;
}

.divider-line {
  flex: 1;
  height: 1px;
  background: linear-gradient(90deg, transparent, #8b6914, transparent);
}

.divider-dot {
  color: #d4af37;
  font-size: 0.8rem;
}

/* ======== 正文 ======== */
.contract-body {
  color: #d4c4a0;
  line-height: 2;
  font-size: 1rem;
  text-align: center;
}

.contract-lead {
  font-size: 0.85rem;
  color: #888;
  font-style: italic;
  margin-bottom: 12px;
}

.contract-para {
  margin: 8px 0;
}

.highlight-chips {
  color: #ffd700;
  font-weight: 700;
  font-size: 1.4rem;
  font-family: 'Courier New', monospace;
  text-shadow: 0 0 20px rgba(255, 215, 0, 0.7);
  animation: chipsGlow 1.8s ease-in-out infinite;
}

@keyframes chipsGlow {
  0%, 100% { text-shadow: 0 0 20px rgba(255, 215, 0, 0.7); }
  50% { text-shadow: 0 0 35px rgba(255, 215, 0, 1), 0 0 60px rgba(255, 215, 0, 0.5); }
}

.highlight-win {
  color: #ff4c4c;
  font-weight: 700;
  text-shadow: 0 0 15px rgba(255, 76, 76, 0.6);
}

.small-print {
  font-size: 0.75rem !important;
  color: #666 !important;
  margin-top: 15px !important;
}

.fake-low {
  color: #4caf50;
  font-weight: 700;
}

.real-high {
  color: #ff4c4c;
  font-weight: 700;
  text-decoration: line-through;
  opacity: 0.8;
}

.fine {
  font-size: 0.65rem !important;
  color: #444 !important;
}

/* ======== 签名行 ======== */
.signature-row {
  display: flex;
  align-items: center;
  gap: 12px;
  margin: 25px 0 30px;
  padding: 10px 0;
  border-top: 1px dashed #3a2a0a;
  border-bottom: 1px dashed #3a2a0a;
}

.signature-label {
  font-size: 0.85rem;
  color: #8b6914;
  letter-spacing: 0.2rem;
}

.signature-line {
  flex: 1;
}

.signature-placeholder {
  color: #444;
  font-family: 'Courier New', monospace;
  letter-spacing: 0.2rem;
}

/* ======== 同意按钮 ======== */
.accept-btn {
  width: 100%;
  padding: 18px;
  background: linear-gradient(180deg, #8b0000 0%, #4a0000 100%);
  border: 2px solid #d4af37;
  color: #ffd700;
  font-size: 1.1rem;
  font-family: inherit;
  letter-spacing: 0.5rem;
  cursor: pointer;
  position: relative;
  overflow: hidden;
  transition: all 0.3s;
  box-shadow: 0 0 30px rgba(139, 0, 0, 0.5), inset 0 0 20px rgba(255, 215, 0, 0.2);
}

.accept-btn::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 215, 0, 0.3), transparent);
  animation: btnShine 2.5s ease-in-out infinite;
}

@keyframes btnShine {
  0% { left: -100%; }
  50%, 100% { left: 100%; }
}

.accept-btn:hover:not(:disabled) {
  background: linear-gradient(180deg, #a00000 0%, #6a0000 100%);
  box-shadow: 0 0 50px rgba(255, 76, 76, 0.6), inset 0 0 30px rgba(255, 215, 0, 0.3);
  transform: translateY(-2px);
}

.accept-btn:active:not(:disabled) {
  transform: translateY(1px);
}

.accept-btn:disabled {
  opacity: 0.7;
  cursor: wait;
}

.btn-text {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  position: relative;
  z-index: 1;
}

.btn-stamp {
  display: inline-block;
  width: 22px;
  height: 22px;
  line-height: 20px;
  border: 2px solid #ffd700;
  border-radius: 50%;
  font-size: 0.85rem;
}

.warning-text {
  text-align: center;
  margin-top: 20px;
  font-size: 0.7rem;
  color: #ff6666;
  letter-spacing: 0.1rem;
  opacity: 0.7;
}

/* ======== 过渡动画 ======== */
.loan-fade-enter-active {
  transition: opacity 0.5s ease;
}
.loan-fade-leave-active {
  transition: opacity 0.3s ease;
}
.loan-fade-enter-from,
.loan-fade-leave-to {
  opacity: 0;
}
</style>
