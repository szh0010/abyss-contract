<template>
  <Teleport to="body">
    <transition name="modal-fade">
      <div v-if="visible" class="assess-overlay" @click.self="tryClose">
        <div class="assess-shell" :class="{ 'result-mode': phase === 'result' }">
          <!-- ===== 关闭按钮 ===== -->
          <button class="close-btn" @click="tryClose" :disabled="loading">✕</button>

          <!-- ===== 角标装饰 ===== -->
          <span class="corner tl"></span>
          <span class="corner tr"></span>
          <span class="corner bl"></span>
          <span class="corner br"></span>

          <!-- ========== 题目阶段 ========== -->
          <template v-if="phase === 'quiz'">
            <header class="assess-header">
              <div class="header-tag">PSYCHO-PROFILE // 反诈人格评估</div>
              <h2 class="header-title">PERSONALITY DIAGNOSTIC</h2>
              <p class="header-desc">
                共 {{ questions.length }} 题 · 凭第一反应作答 · 结果由 DeepSeek 智能判定
              </p>
              <div class="progress-bar">
                <div
                  class="progress-fill"
                  :style="{ width: ((currentIdx + (answerForCurrent ? 1 : 0)) / questions.length * 100) + '%' }"
                ></div>
              </div>
              <div class="progress-meta">
                <span>{{ currentIdx + 1 }} / {{ questions.length }}</span>
                <span>已作答 {{ answeredCount }}</span>
              </div>
            </header>

            <div v-if="loadingQuestions" class="center-loading">
              正在加载题库…
            </div>

            <div v-else-if="currentQuestion" class="question-card">
              <div class="q-dim">[ {{ currentQuestion.dimension }}维度 ]</div>
              <div class="q-text">{{ currentQuestion.text }}</div>

              <div class="options">
                <button
                  v-for="opt in currentQuestion.options"
                  :key="opt.key"
                  class="option"
                  :class="{ active: answerForCurrent === opt.key }"
                  @click="pickOption(opt.key)"
                >
                  <span class="opt-key">{{ opt.key }}</span>
                  <span class="opt-text">{{ opt.text }}</span>
                </button>
              </div>
            </div>

            <footer class="assess-footer">
              <button class="footer-btn ghost" @click="prev" :disabled="currentIdx === 0">
                ← 上一题
              </button>
              <button
                v-if="currentIdx < questions.length - 1"
                class="footer-btn primary"
                :disabled="!answerForCurrent"
                @click="next"
              >
                下一题 →
              </button>
              <button
                v-else
                class="footer-btn danger"
                :disabled="!allAnswered || loading"
                @click="submit"
              >
                <span v-if="!loading">⚡ 启动判定</span>
                <span v-else>判定中…</span>
              </button>
            </footer>
          </template>

          <!-- ========== 判定中（loading） ========== -->
          <template v-else-if="phase === 'analyzing'">
            <div class="analyzing">
              <div class="scan-ring"></div>
              <div class="analyzing-text">
                <div class="line">&gt; 神经网络加载中…</div>
                <div class="line">&gt; 比对反诈人格模型 v4.7…</div>
                <div class="line pulse">&gt; DeepSeek 正在生成身份判定报告…</div>
              </div>
            </div>
          </template>

          <!-- ========== 结果报告 ========== -->
          <template v-else-if="phase === 'result' && result">
            <div class="report-watermark">CLASSIFIED</div>
            <header class="report-header">
              <div class="report-tag">// PERSONALITY REPORT · 身份判定报告</div>
              <div class="report-id">DOSSIER-{{ reportCode }}</div>
            </header>

            <div class="report-body">
              <div class="personality-wrap">
                <div class="personality-label">PERSONALITY TYPE</div>
                <div class="personality-name">{{ result.personality_type }}</div>
                <div class="personality-underline"></div>
              </div>

              <section class="report-section">
                <div class="section-title">
                  <span class="title-dot"></span>
                  TRAIT ANALYSIS · 特征分析
                </div>
                <p class="section-text">{{ result.trait_analysis }}</p>
              </section>

              <section class="report-section">
                <div class="section-title warn">
                  <span class="title-dot red"></span>
                  PRECAUTIONS · 警戒提示
                </div>
                <p class="section-text warn">{{ result.precautions }}</p>
              </section>

              <section class="medal-award">
                <div class="award-label">🎖 勋章已授予</div>
                <div class="medal-card" :class="result.medal.tier">
                  <svg viewBox="0 0 24 24" width="36" height="36">
                    <path v-if="result.medal.icon === 'shield'" d="M12 2 L20 5 V12 C20 17 16 21 12 22 C8 21 4 17 4 12 V5 Z" fill="currentColor"/>
                    <path v-else-if="result.medal.icon === 'star'" d="M12 2 L14.5 9 L22 9.3 L16 14 L18 21.5 L12 17.3 L6 21.5 L8 14 L2 9.3 L9.5 9 Z" fill="currentColor"/>
                    <path v-else-if="result.medal.icon === 'eye'" d="M12 5 C5 5 2 12 2 12 C2 12 5 19 12 19 C19 19 22 12 22 12 C22 12 19 5 12 5 Z M12 15 A3 3 0 1 1 12 9 A3 3 0 0 1 12 15 Z" fill="currentColor"/>
                    <path v-else-if="result.medal.icon === 'bolt'" d="M13 2 L4 14 H11 L10 22 L20 10 H13 Z" fill="currentColor"/>
                  </svg>
                  <div class="medal-info">
                    <div class="medal-name">{{ result.medal.name }}</div>
                    <div class="medal-tier">{{ tierLabel(result.medal.tier) }} · #{{ result.medal.id }}</div>
                  </div>
                </div>
              </section>
            </div>

            <footer class="report-footer">
              <button class="footer-btn ghost" @click="retry">再测一次</button>
              <button class="footer-btn primary" @click="close">关闭报告</button>
            </footer>
          </template>

          <!-- ========== 错误 ========== -->
          <template v-else-if="phase === 'error'">
            <div class="error-box">
              <div class="error-title">⚠ 判定失败</div>
              <div class="error-msg">{{ errorMsg }}</div>
              <button class="footer-btn ghost" @click="retry">重新开始</button>
            </div>
          </template>
        </div>
      </div>
    </transition>
  </Teleport>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import http from '../services/http'

const props = defineProps({
  visible: Boolean,
})
const emit = defineEmits(['close', 'completed'])

const questions = ref([])
const answers = ref({})
const currentIdx = ref(0)
const phase = ref('quiz')            // quiz | analyzing | result | error
const loading = ref(false)
const loadingQuestions = ref(false)
const result = ref(null)
const errorMsg = ref('')

const currentQuestion = computed(() => questions.value[currentIdx.value] || null)
const answerForCurrent = computed(() =>
  currentQuestion.value ? answers.value[currentQuestion.value.id] : null
)
const answeredCount = computed(() => Object.keys(answers.value).length)
const allAnswered = computed(() =>
  questions.value.length > 0 && answeredCount.value === questions.value.length
)
const reportCode = computed(() =>
  Math.random().toString(36).slice(2, 8).toUpperCase()
)

watch(() => props.visible, (v) => {
  if (v) loadQuestions()
})

async function loadQuestions() {
  if (questions.value.length > 0) return
  loadingQuestions.value = true
  try {
    const { data } = await http.get('/assess/questions')
    questions.value = data.questions || []
  } catch (e) {
    if (e?.response?.status === 401) return
    errorMsg.value = e?.response?.data?.detail || '题库加载失败，请稍后重试'
    phase.value = 'error'
  } finally {
    loadingQuestions.value = false
  }
}

function pickOption(key) {
  if (!currentQuestion.value) return
  answers.value[currentQuestion.value.id] = key
}

function next() {
  if (currentIdx.value < questions.value.length - 1) currentIdx.value++
}
function prev() {
  if (currentIdx.value > 0) currentIdx.value--
}

async function submit() {
  if (!allAnswered.value) return
  phase.value = 'analyzing'
  loading.value = true

  const payload = {
    answers: questions.value.map(q => ({ id: q.id, selected: answers.value[q.id] })),
  }

  try {
    const { data } = await http.post('/assess', payload)
    result.value = data
    // 至少展示一下扫描动画
    setTimeout(() => { phase.value = 'result' }, 1200)
    emit('completed', data)
  } catch (e) {
    if (e?.response?.status === 401) return
    errorMsg.value = e?.response?.data?.detail || e.message || '网络异常'
    phase.value = 'error'
  } finally {
    loading.value = false
  }
}

function tryClose() {
  if (loading.value) return
  close()
}

function close() {
  emit('close')
  // 保留答题状态，下次打开可继续；结果关闭后重置
  if (phase.value === 'result' || phase.value === 'error') {
    setTimeout(() => {
      phase.value = 'quiz'
      result.value = null
      answers.value = {}
      currentIdx.value = 0
    }, 300)
  }
}

function retry() {
  answers.value = {}
  currentIdx.value = 0
  result.value = null
  errorMsg.value = ''
  phase.value = 'quiz'
}

function tierLabel(t) {
  return { gold: 'GOLD 金级', silver: 'SILVER 银级', bronze: 'BRONZE 铜级' }[t] || t?.toUpperCase()
}
</script>

<style scoped>
/* ======== Overlay ======== */
.assess-overlay {
  position: fixed;
  inset: 0;
  background: radial-gradient(ellipse at center, rgba(5, 10, 25, 0.85), rgba(0, 0, 0, 0.94));
  backdrop-filter: blur(8px);
  z-index: 9999;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
}

.modal-fade-enter-active, .modal-fade-leave-active {
  transition: opacity 0.25s ease;
}
.modal-fade-enter-from, .modal-fade-leave-to {
  opacity: 0;
}

/* ======== Shell ======== */
.assess-shell {
  position: relative;
  width: min(720px, 100%);
  max-height: 90vh;
  overflow-y: auto;
  background:
    linear-gradient(135deg, rgba(14, 22, 44, 0.92), rgba(8, 12, 28, 0.95)),
    repeating-linear-gradient(0deg, rgba(0, 234, 255, 0.02) 0, rgba(0, 234, 255, 0.02) 1px, transparent 1px, transparent 3px);
  border: 1px solid rgba(0, 234, 255, 0.35);
  border-radius: 14px;
  box-shadow:
    0 0 60px rgba(0, 234, 255, 0.2),
    0 0 120px rgba(124, 92, 255, 0.18),
    inset 0 0 40px rgba(0, 0, 0, 0.5);
  color: #d6e3ff;
  padding: 34px 32px 28px;
  animation: shellIn 0.5s cubic-bezier(0.22, 1, 0.36, 1);
}

.assess-shell.result-mode {
  border-color: rgba(255, 170, 0, 0.45);
  box-shadow:
    0 0 60px rgba(255, 170, 0, 0.25),
    0 0 120px rgba(255, 51, 85, 0.15),
    inset 0 0 40px rgba(0, 0, 0, 0.5);
}

@keyframes shellIn {
  from { opacity: 0; transform: translateY(20px) scale(0.96); }
  to   { opacity: 1; transform: translateY(0) scale(1); }
}

.assess-shell::-webkit-scrollbar { width: 6px; }
.assess-shell::-webkit-scrollbar-thumb { background: rgba(0, 234, 255, 0.25); border-radius: 3px; }

/* ======== 角标 ======== */
.corner {
  position: absolute;
  width: 18px;
  height: 18px;
  border-color: #00eaff;
  border-style: solid;
}
.corner.tl { top: 8px; left: 8px;  border-width: 2px 0 0 2px; }
.corner.tr { top: 8px; right: 8px; border-width: 2px 2px 0 0; }
.corner.bl { bottom: 8px; left: 8px;  border-width: 0 0 2px 2px; }
.corner.br { bottom: 8px; right: 8px; border-width: 0 2px 2px 0; }

.result-mode .corner { border-color: #ffaa00; }

/* ======== 关闭按钮 ======== */
.close-btn {
  position: absolute;
  top: 14px;
  right: 18px;
  width: 28px;
  height: 28px;
  background: transparent;
  border: 1px solid rgba(99, 180, 255, 0.3);
  color: #8ea0c7;
  cursor: pointer;
  border-radius: 4px;
  font-size: 0.85rem;
  transition: all 0.2s;
  z-index: 2;
}
.close-btn:hover:not(:disabled) {
  border-color: #ff5577;
  color: #ff5577;
  box-shadow: 0 0 10px rgba(255, 85, 119, 0.4);
}

/* ======== Header ======== */
.assess-header { margin-bottom: 22px; }
.header-tag {
  font-family: 'Courier New', monospace;
  font-size: 0.7rem;
  color: #00eaff;
  letter-spacing: 0.15rem;
  margin-bottom: 8px;
}
.header-title {
  font-size: 1.6rem;
  font-weight: 700;
  color: #dcecff;
  letter-spacing: 0.1rem;
  margin: 0 0 6px;
  text-shadow: 0 0 14px rgba(0, 234, 255, 0.35);
}
.header-desc {
  font-size: 0.78rem;
  color: #8ea0c7;
  margin: 0 0 14px;
}

.progress-bar {
  width: 100%;
  height: 4px;
  background: rgba(0, 234, 255, 0.08);
  border: 1px solid rgba(0, 234, 255, 0.15);
  border-radius: 2px;
  overflow: hidden;
}
.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #00eaff, #7c5cff);
  box-shadow: 0 0 12px rgba(0, 234, 255, 0.6);
  transition: width 0.3s ease;
}
.progress-meta {
  display: flex;
  justify-content: space-between;
  font-family: 'Courier New', monospace;
  font-size: 0.7rem;
  color: #5a7099;
  margin-top: 6px;
  letter-spacing: 0.08rem;
}

/* ======== 题目 ======== */
.question-card {
  padding: 18px 4px;
  animation: qFade 0.35s ease;
}
@keyframes qFade {
  from { opacity: 0; transform: translateX(12px); }
  to   { opacity: 1; transform: translateX(0); }
}

.q-dim {
  font-family: 'Courier New', monospace;
  font-size: 0.72rem;
  color: #7c5cff;
  letter-spacing: 0.15rem;
  margin-bottom: 10px;
}
.q-text {
  font-size: 1.05rem;
  color: #e8f0ff;
  line-height: 1.6;
  margin-bottom: 20px;
  letter-spacing: 0.02rem;
}

.options { display: flex; flex-direction: column; gap: 10px; }

.option {
  display: flex;
  align-items: flex-start;
  gap: 14px;
  padding: 13px 16px;
  background: rgba(10, 18, 38, 0.5);
  border: 1px solid rgba(99, 180, 255, 0.2);
  color: #c7d4ff;
  border-radius: 8px;
  font-size: 0.88rem;
  text-align: left;
  cursor: pointer;
  transition: all 0.2s;
  font-family: inherit;
}

.option:hover {
  border-color: rgba(0, 234, 255, 0.5);
  background: rgba(0, 234, 255, 0.06);
  transform: translateX(4px);
}

.option.active {
  border-color: #00eaff;
  background: linear-gradient(135deg, rgba(0, 234, 255, 0.15), rgba(124, 92, 255, 0.12));
  color: #fff;
  box-shadow: 0 0 16px rgba(0, 234, 255, 0.3), inset 0 0 20px rgba(0, 234, 255, 0.08);
}

.opt-key {
  flex-shrink: 0;
  width: 26px;
  height: 26px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid currentColor;
  border-radius: 4px;
  font-family: 'Courier New', monospace;
  font-weight: 700;
  font-size: 0.78rem;
}

.opt-text { flex: 1; line-height: 1.5; padding-top: 3px; }

/* ======== Footer ======== */
.assess-footer {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  margin-top: 22px;
  padding-top: 18px;
  border-top: 1px solid rgba(99, 180, 255, 0.15);
}

.footer-btn {
  padding: 10px 22px;
  border-radius: 6px;
  font-family: inherit;
  font-size: 0.85rem;
  letter-spacing: 0.1rem;
  cursor: pointer;
  transition: all 0.25s;
}
.footer-btn:disabled { opacity: 0.35; cursor: not-allowed; }

.footer-btn.ghost {
  background: transparent;
  border: 1px solid rgba(99, 180, 255, 0.3);
  color: #8ea0c7;
}
.footer-btn.ghost:hover:not(:disabled) {
  border-color: #00eaff;
  color: #00eaff;
}

.footer-btn.primary {
  background: linear-gradient(135deg, rgba(0, 234, 255, 0.25), rgba(124, 92, 255, 0.25));
  border: 1px solid rgba(0, 234, 255, 0.55);
  color: #dcecff;
}
.footer-btn.primary:hover:not(:disabled) {
  background: linear-gradient(135deg, rgba(0, 234, 255, 0.5), rgba(124, 92, 255, 0.5));
  box-shadow: 0 0 18px rgba(0, 234, 255, 0.5);
  color: #fff;
}

.footer-btn.danger {
  background: linear-gradient(135deg, rgba(255, 51, 85, 0.35), rgba(139, 0, 20, 0.45));
  border: 1px solid rgba(255, 85, 119, 0.6);
  color: #fff;
  font-weight: 700;
}
.footer-btn.danger:hover:not(:disabled) {
  box-shadow: 0 0 20px rgba(255, 51, 85, 0.55);
}

.center-loading {
  text-align: center;
  padding: 60px 0;
  color: #8ea0c7;
  font-family: 'Courier New', monospace;
}

/* ======== 分析中动画 ======== */
.analyzing {
  padding: 50px 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 32px;
}

.scan-ring {
  width: 90px;
  height: 90px;
  border-radius: 50%;
  border: 2px solid rgba(0, 234, 255, 0.1);
  border-top-color: #00eaff;
  border-right-color: #7c5cff;
  animation: scanSpin 1.2s linear infinite;
  box-shadow: 0 0 30px rgba(0, 234, 255, 0.4);
}
@keyframes scanSpin {
  to { transform: rotate(360deg); }
}

.analyzing-text {
  font-family: 'Courier New', monospace;
  color: #8ea0c7;
  font-size: 0.82rem;
  letter-spacing: 0.05rem;
}
.analyzing-text .line {
  margin: 6px 0;
  opacity: 0;
  animation: lineIn 0.5s ease forwards;
}
.analyzing-text .line:nth-child(1) { animation-delay: 0.1s; }
.analyzing-text .line:nth-child(2) { animation-delay: 0.7s; }
.analyzing-text .line:nth-child(3) { animation-delay: 1.3s; color: #00eaff; }
.analyzing-text .line.pulse { animation: lineIn 0.5s ease forwards, textPulse 1.4s ease-in-out infinite 1.8s; }
@keyframes lineIn {
  from { opacity: 0; transform: translateX(-8px); }
  to   { opacity: 1; transform: translateX(0); }
}
@keyframes textPulse {
  50% { opacity: 0.5; }
}

/* ======== 报告 ======== */
.report-watermark {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%) rotate(-18deg);
  font-size: 5rem;
  font-weight: 900;
  color: rgba(255, 85, 119, 0.04);
  letter-spacing: 1rem;
  pointer-events: none;
  user-select: none;
}

.report-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-bottom: 14px;
  border-bottom: 1px dashed rgba(255, 170, 0, 0.35);
  margin-bottom: 20px;
  font-family: 'Courier New', monospace;
}
.report-tag {
  font-size: 0.75rem;
  color: #ffaa00;
  letter-spacing: 0.15rem;
}
.report-id {
  font-size: 0.7rem;
  color: #8ea0c7;
  letter-spacing: 0.1rem;
}

.personality-wrap {
  text-align: center;
  padding: 20px 0 28px;
  position: relative;
}
.personality-label {
  font-family: 'Courier New', monospace;
  font-size: 0.72rem;
  color: #ffaa00;
  letter-spacing: 0.3rem;
  margin-bottom: 12px;
}
.personality-name {
  font-size: 2.4rem;
  font-weight: 800;
  color: #fff;
  letter-spacing: 0.4rem;
  text-shadow:
    0 0 16px rgba(255, 170, 0, 0.55),
    0 0 32px rgba(255, 51, 85, 0.3);
  animation: nameGlow 2.2s ease-in-out infinite alternate;
}
@keyframes nameGlow {
  to { text-shadow: 0 0 24px rgba(255, 170, 0, 0.8), 0 0 48px rgba(255, 51, 85, 0.5); }
}
.personality-underline {
  width: 140px;
  height: 2px;
  margin: 14px auto 0;
  background: linear-gradient(90deg, transparent, #ffaa00, transparent);
  box-shadow: 0 0 10px rgba(255, 170, 0, 0.6);
}

.report-section {
  margin-bottom: 20px;
  padding: 14px 16px;
  background: rgba(5, 10, 25, 0.5);
  border-left: 2px solid #00eaff;
  border-radius: 0 6px 6px 0;
}
.section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-family: 'Courier New', monospace;
  font-size: 0.78rem;
  color: #00eaff;
  letter-spacing: 0.12rem;
  margin-bottom: 10px;
}
.section-title.warn { color: #ff5577; }
.title-dot {
  width: 6px; height: 6px; border-radius: 50%;
  background: #00eaff;
  box-shadow: 0 0 8px #00eaff;
}
.title-dot.red { background: #ff5577; box-shadow: 0 0 8px #ff5577; }

.section-text {
  color: #c7d4ff;
  font-size: 0.9rem;
  line-height: 1.75;
  margin: 0;
}
.section-text.warn { color: #ffb3c0; }

.report-section:has(.section-title.warn) {
  border-left-color: #ff5577;
  background: rgba(40, 10, 20, 0.4);
}

/* 勋章授予 */
.medal-award {
  margin-top: 24px;
  padding: 18px;
  border: 1px dashed rgba(255, 170, 0, 0.4);
  border-radius: 8px;
  background: rgba(30, 20, 5, 0.3);
}
.award-label {
  font-family: 'Courier New', monospace;
  font-size: 0.78rem;
  color: #ffaa00;
  letter-spacing: 0.1rem;
  margin-bottom: 12px;
}
.medal-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 14px 16px;
  background: rgba(0, 0, 0, 0.4);
  border: 1px solid currentColor;
  border-radius: 6px;
  animation: medalPop 0.6s cubic-bezier(0.34, 1.56, 0.64, 1) 0.2s both;
}
.medal-card.gold   { color: #ffd24a; box-shadow: 0 0 20px rgba(255, 210, 74, 0.35); }
.medal-card.silver { color: #cfdaf0; box-shadow: 0 0 20px rgba(207, 218, 240, 0.3); }
.medal-card.bronze { color: #d48a56; box-shadow: 0 0 20px rgba(212, 138, 86, 0.3); }

@keyframes medalPop {
  from { opacity: 0; transform: scale(0.5) rotate(-10deg); }
  to   { opacity: 1; transform: scale(1) rotate(0); }
}

.medal-info { display: flex; flex-direction: column; }
.medal-name {
  font-size: 1.1rem;
  font-weight: 700;
  color: #fff;
  letter-spacing: 0.15rem;
}
.medal-tier {
  font-family: 'Courier New', monospace;
  font-size: 0.7rem;
  color: #8ea0c7;
  letter-spacing: 0.08rem;
  margin-top: 2px;
}

.report-footer {
  display: flex;
  justify-content: center;
  gap: 14px;
  margin-top: 22px;
  padding-top: 18px;
  border-top: 1px dashed rgba(255, 170, 0, 0.25);
}

/* 错误状态 */
.error-box {
  text-align: center;
  padding: 40px 20px;
}
.error-title {
  font-size: 1.2rem;
  color: #ff5577;
  margin-bottom: 12px;
  letter-spacing: 0.15rem;
}
.error-msg {
  color: #8ea0c7;
  margin-bottom: 20px;
  font-size: 0.88rem;
}
</style>
