<template>
  <Teleport to="body">
    <transition name="modal-fade">
      <div v-if="visible" class="assess-overlay" @click.self="tryClose">
        <div class="assess-shell" :class="{ 'result-mode': phase === 'result' }">
          <!-- ===== 关闭按钮 ===== -->
          <button class="close-btn" @click="tryClose" :disabled="loading" aria-label="关闭">
            <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M18 6L6 18M6 6l12 12"/>
            </svg>
          </button>

          <!-- 暖色光晕 -->
          <span class="aura aura-tl" aria-hidden="true"></span>
          <span class="aura aura-br" aria-hidden="true"></span>

          <!-- ========== 题目阶段 ========== -->
          <template v-if="phase === 'quiz'">
            <header class="assess-header">
              <span class="header-tag">PSYCHO PROFILE · 反诈人格评估</span>
              <h2 class="header-title">认识那个最不易被骗的你</h2>
              <p class="header-desc">
                共 {{ questions.length }} 题 · 凭第一反应作答 · 由 DeepSeek 智能判定
              </p>
              <div class="progress-bar">
                <div
                  class="progress-fill"
                  :style="{ width: ((currentIdx + (answerForCurrent ? 1 : 0)) / questions.length * 100) + '%' }"
                ></div>
              </div>
              <div class="progress-meta">
                <span>第 {{ currentIdx + 1 }} / {{ questions.length }} 题</span>
                <span>已作答 {{ answeredCount }}</span>
              </div>
            </header>

            <div v-if="loadingQuestions" class="center-loading">
              <span class="dot-loader"><i></i><i></i><i></i></span>
              <span>正在加载题库…</span>
            </div>

            <div v-else-if="currentQuestion" class="question-card">
              <div class="q-dim">{{ currentQuestion.dimension }} 维度</div>
              <div class="q-text">{{ currentQuestion.text }}</div>

              <div class="options">
                <button
                  v-for="opt in currentQuestion.options"
                  :key="opt.key"
                  class="option"
                  :class="{ active: answerForCurrent === opt.key }"
                  @click="pickOption(opt.key)"
                  type="button"
                >
                  <span class="opt-key">{{ opt.key }}</span>
                  <span class="opt-text">{{ opt.text }}</span>
                  <span class="opt-check" aria-hidden="true">
                    <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
                      <path d="M5 12l5 5L20 7"/>
                    </svg>
                  </span>
                </button>
              </div>
            </div>

            <footer class="assess-footer">
              <button class="footer-btn ghost" @click="prev" :disabled="currentIdx === 0" type="button">
                ← 上一题
              </button>
              <button
                v-if="currentIdx < questions.length - 1"
                class="footer-btn primary"
                :disabled="!answerForCurrent"
                @click="next"
                type="button"
              >
                下一题 →
              </button>
              <button
                v-else
                class="footer-btn primary"
                :disabled="!allAnswered || loading"
                @click="submit"
                type="button"
              >
                <span v-if="!loading">启动判定</span>
                <span v-else>判定中…</span>
              </button>
            </footer>
          </template>

          <!-- ========== 判定中（loading） ========== -->
          <template v-else-if="phase === 'analyzing'">
            <div class="analyzing">
              <div class="scan-ring"></div>
              <div class="analyzing-text">
                <div class="line">神经网络加载中…</div>
                <div class="line">比对反诈人格模型 v4.7…</div>
                <div class="line pulse">DeepSeek 正在生成你的判定报告…</div>
              </div>
            </div>
          </template>

          <!-- ========== 结果报告 ========== -->
          <template v-else-if="phase === 'result' && result">
            <header class="report-header">
              <span class="report-tag">PERSONALITY REPORT · 身份判定报告</span>
              <span class="report-id">DOSSIER · {{ reportCode }}</span>
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
                  特征分析 · TRAIT ANALYSIS
                </div>
                <p class="section-text">{{ result.trait_analysis }}</p>
              </section>

              <section class="report-section">
                <div class="section-title warn">
                  <span class="title-dot red"></span>
                  警戒提示 · PRECAUTIONS
                </div>
                <p class="section-text warn">{{ result.precautions }}</p>
              </section>

              <section class="medal-award">
                <div class="award-label">勋章已授予</div>
                <div class="medal-card" :class="result.medal.tier">
                  <div class="medal-icon">
                    <svg viewBox="0 0 24 24" width="34" height="34">
                      <path v-if="result.medal.icon === 'shield'" d="M12 2 L20 5 V12 C20 17 16 21 12 22 C8 21 4 17 4 12 V5 Z" fill="currentColor"/>
                      <path v-else-if="result.medal.icon === 'star'" d="M12 2 L14.5 9 L22 9.3 L16 14 L18 21.5 L12 17.3 L6 21.5 L8 14 L2 9.3 L9.5 9 Z" fill="currentColor"/>
                      <path v-else-if="result.medal.icon === 'eye'" d="M12 5 C5 5 2 12 2 12 C2 12 5 19 12 19 C19 19 22 12 22 12 C22 12 19 5 12 5 Z M12 15 A3 3 0 1 1 12 9 A3 3 0 0 1 12 15 Z" fill="currentColor"/>
                      <path v-else-if="result.medal.icon === 'bolt'" d="M13 2 L4 14 H11 L10 22 L20 10 H13 Z" fill="currentColor"/>
                    </svg>
                  </div>
                  <div class="medal-info">
                    <div class="medal-name">{{ result.medal.name }}</div>
                    <div class="medal-tier">{{ tierLabel(result.medal.tier) }} · #{{ result.medal.id }}</div>
                  </div>
                </div>
              </section>
            </div>

            <footer class="report-footer">
              <button class="footer-btn ghost" @click="retry" type="button">再测一次</button>
              <button class="footer-btn primary" @click="close" type="button">关闭报告</button>
            </footer>
          </template>

          <!-- ========== 错误 ========== -->
          <template v-else-if="phase === 'error'">
            <div class="error-box">
              <div class="error-title">判定失败</div>
              <div class="error-msg">{{ errorMsg }}</div>
              <button class="footer-btn primary" @click="retry" type="button">重新开始</button>
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
/* ============================================================
   反诈人格评估 · 暖色液态玻璃 · 香槟金 + 浅桃色渐变
============================================================ */
.assess-overlay {
  position: fixed;
  inset: 0;
  z-index: 80;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  background: rgba(70, 50, 30, 0.18);
  backdrop-filter: blur(6px);
  -webkit-backdrop-filter: blur(6px);
}

.assess-shell {
  position: relative;
  width: min(620px, 100%);
  max-height: 88vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  padding: 32px clamp(20px, 4vw, 36px) 28px;
  border-radius: 32px;
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(28px) saturate(180%);
  -webkit-backdrop-filter: blur(28px) saturate(180%);
  border: 1px solid rgba(255, 255, 255, 0.95);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.95),
    0 30px 80px rgba(200, 130, 70, 0.18),
    0 8px 24px rgba(180, 110, 50, 0.08);
  color: #1f2937;
  font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display',
               'PingFang SC', 'Helvetica Neue', sans-serif;
}

.aura {
  position: absolute;
  z-index: 0;
  border-radius: 50%;
  filter: blur(60px);
  opacity: 0.55;
  pointer-events: none;
  mix-blend-mode: multiply;
}
.aura-tl {
  width: 280px; height: 280px;
  top: -100px; left: -80px;
  background: radial-gradient(circle, #ffe1b3 0%, transparent 70%);
}
.aura-br {
  width: 320px; height: 320px;
  bottom: -120px; right: -100px;
  background: radial-gradient(circle, #ffd1c2 0%, transparent 70%);
}

/* 关闭按钮 */
.close-btn {
  position: absolute;
  top: 16px;
  right: 16px;
  z-index: 10;
  width: 32px; height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.7);
  color: #4b3710;
  cursor: pointer;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.95), 0 4px 12px rgba(0, 0, 0, 0.06);
  transition: all 0.3s cubic-bezier(0.25, 1.5, 0.5, 1);
}
.close-btn:hover:not(:disabled) {
  background: rgba(255, 255, 255, 0.95);
  color: #c2410c;
  transform: rotate(90deg);
}
.close-btn:disabled { opacity: 0.5; cursor: not-allowed; }

/* 进入/离开动画 */
.modal-fade-enter-active,
.modal-fade-leave-active {
  transition: opacity 0.4s cubic-bezier(0.22, 1, 0.36, 1);
}
.modal-fade-enter-active .assess-shell,
.modal-fade-leave-active .assess-shell {
  transition:
    transform 0.5s cubic-bezier(0.25, 1.5, 0.5, 1),
    opacity 0.4s cubic-bezier(0.22, 1, 0.36, 1);
}
.modal-fade-enter-from { opacity: 0; }
.modal-fade-leave-to   { opacity: 0; }
.modal-fade-enter-from .assess-shell { opacity: 0; transform: scale(0.92) translateY(12px); }
.modal-fade-leave-to .assess-shell   { opacity: 0; transform: scale(0.96) translateY(-6px); }
/* ============ Header ============ */
.assess-header {
  position: relative;
  z-index: 1;
  text-align: center;
  margin-bottom: 22px;
}
.header-tag {
  display: inline-block;
  font-family: 'SF Mono', ui-monospace, monospace;
  font-size: 0.66rem;
  letter-spacing: 0.24em;
  color: #b97011;
  padding: 4px 12px;
  border-radius: 999px;
  background: linear-gradient(90deg, rgba(252, 211, 77, 0.22), rgba(251, 146, 60, 0.18));
  margin-bottom: 14px;
}
.header-title {
  font-size: 1.4rem;
  font-weight: 800;
  letter-spacing: 0.04em;
  color: #1f2937;
  margin-bottom: 8px;
}
.header-desc {
  font-size: 0.82rem;
  color: #6b7280;
  letter-spacing: 0.01em;
}
.progress-bar {
  margin: 18px 0 8px;
  height: 6px;
  border-radius: 999px;
  background: rgba(0, 0, 0, 0.06);
  overflow: hidden;
}
.progress-fill {
  height: 100%;
  border-radius: 999px;
  background: linear-gradient(90deg, #fcd34d 0%, #fb923c 100%);
  transition: width 0.5s cubic-bezier(0.22, 1, 0.36, 1);
  box-shadow: 0 0 12px rgba(251, 146, 60, 0.4);
}
.progress-meta {
  display: flex;
  justify-content: space-between;
  font-size: 0.74rem;
  color: #9ca3af;
  font-family: 'SF Mono', ui-monospace, monospace;
  letter-spacing: 0.04em;
}
/* ============ Question ============ */
.question-card {
  position: relative;
  z-index: 1;
  padding: 20px 22px;
  border-radius: 22px;
  background: rgba(255, 255, 255, 0.6);
  border: 1px solid rgba(255, 255, 255, 0.8);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.95);
  margin-bottom: 18px;
  flex: 1 1 auto;
  min-height: 0;
  overflow-y: auto;
  scrollbar-width: none;
}
.question-card::-webkit-scrollbar { display: none; }
.q-dim {
  display: inline-block;
  font-size: 0.7rem;
  letter-spacing: 0.16em;
  color: #b97011;
  padding: 3px 10px;
  border-radius: 8px;
  background: rgba(251, 191, 36, 0.16);
  margin-bottom: 12px;
}
.q-text {
  font-size: 1.05rem;
  font-weight: 700;
  color: #1f2937;
  line-height: 1.7;
  margin-bottom: 18px;
}

/* 选项卡片 */
.options { display: flex; flex-direction: column; gap: 10px; }
.option {
  position: relative;
  display: grid;
  grid-template-columns: 32px 1fr 24px;
  align-items: center;
  gap: 12px;
  width: 100%;
  padding: 14px 16px;
  border: 1px solid rgba(255, 255, 255, 0.8);
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.6);
  font: inherit;
  font-size: 0.92rem;
  text-align: left;
  color: #374151;
  cursor: pointer;
  transition: all 0.35s cubic-bezier(0.25, 1.5, 0.5, 1);
}
.option:hover {
  background: rgba(255, 255, 255, 0.85);
  transform: translateY(-1px);
  box-shadow: 0 8px 20px rgba(200, 140, 70, 0.12);
}
.option.active {
  border-color: #fbbf24;
  background: rgba(254, 243, 199, 0.55);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.95),
    0 6px 18px rgba(251, 146, 60, 0.18);
  color: #1f2937;
}
.opt-key {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px; height: 28px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.85);
  font-family: 'SF Mono', ui-monospace, monospace;
  font-weight: 700;
  font-size: 0.82rem;
  color: #b97011;
  border: 1px solid rgba(251, 146, 60, 0.18);
}
.option.active .opt-key {
  color: #fff;
  background: linear-gradient(135deg, #fcd34d 0%, #fb923c 100%);
  border-color: transparent;
  box-shadow: 0 4px 12px rgba(251, 146, 60, 0.4);
}
.opt-text {
  line-height: 1.55;
  word-break: break-word;
}
.opt-check {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 24px; height: 24px;
  border-radius: 50%;
  color: transparent;
  background: transparent;
  transition: all 0.3s cubic-bezier(0.25, 1.5, 0.5, 1);
  transform: scale(0.6);
}
.option.active .opt-check {
  color: #fff;
  background: linear-gradient(135deg, #fcd34d 0%, #fb923c 100%);
  transform: scale(1);
  box-shadow: 0 4px 10px rgba(251, 146, 60, 0.35);
}
/* ============ Footer 按钮 ============ */
.assess-footer,
.report-footer {
  position: relative;
  z-index: 1;
  display: flex;
  gap: 12px;
  justify-content: flex-end;
  margin-top: 6px;
}
.footer-btn {
  padding: 11px 24px;
  border: none;
  border-radius: 14px;
  font: inherit;
  font-size: 0.9rem;
  font-weight: 700;
  letter-spacing: 0.04em;
  cursor: pointer;
  transition: all 0.4s cubic-bezier(0.25, 1.5, 0.5, 1);
}
.footer-btn.ghost {
  color: #6b7280;
  background: rgba(255, 255, 255, 0.7);
  border: 1px solid rgba(255, 255, 255, 0.9);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.95);
}
.footer-btn.ghost:hover:not(:disabled) {
  color: #1f2937;
  background: rgba(255, 255, 255, 0.95);
}
.footer-btn.primary {
  color: #fff;
  background: linear-gradient(90deg, #fcd34d 0%, #fb923c 100%);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.5),
    0 12px 30px rgba(251, 146, 60, 0.35);
}
.footer-btn.primary:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.6),
    0 16px 40px rgba(251, 146, 60, 0.45);
}
.footer-btn:active:not(:disabled) { transform: scale(0.95); }
.footer-btn:disabled { opacity: 0.5; cursor: not-allowed; }
/* ============ Loading / Analyzing ============ */
.center-loading {
  position: relative;
  z-index: 1;
  padding: 40px 0;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  color: #6b7280;
  font-size: 0.88rem;
}
.dot-loader { display: inline-flex; gap: 5px; }
.dot-loader i {
  width: 6px; height: 6px;
  border-radius: 50%;
  background: linear-gradient(135deg, #fcd34d, #fb923c);
  animation: dotBlink 1.1s infinite ease-in-out;
}
.dot-loader i:nth-child(2) { animation-delay: 0.15s; }
.dot-loader i:nth-child(3) { animation-delay: 0.30s; }
@keyframes dotBlink {
  0%, 80%, 100% { opacity: 0.3; transform: scale(0.85); }
  40% { opacity: 1; transform: scale(1); }
}

.analyzing {
  position: relative;
  z-index: 1;
  padding: 40px 0 28px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 26px;
}
.scan-ring {
  width: 92px; height: 92px;
  border-radius: 50%;
  border: 4px solid rgba(251, 146, 60, 0.18);
  border-top-color: #fb923c;
  border-right-color: #fcd34d;
  animation: scanSpin 1.2s linear infinite;
  box-shadow: 0 0 36px rgba(251, 146, 60, 0.32);
}
@keyframes scanSpin { to { transform: rotate(360deg); } }
.analyzing-text { display: flex; flex-direction: column; gap: 8px; text-align: center; }
.analyzing-text .line { font-size: 0.82rem; color: #6b7280; letter-spacing: 0.02em; }
.analyzing-text .pulse { color: #c2410c; font-weight: 600; animation: pulseFade 1.4s ease-in-out infinite; }
@keyframes pulseFade { 0%, 100% { opacity: 0.5; } 50% { opacity: 1; } }
/* ============ Report ============ */
.report-header {
  position: relative;
  z-index: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
  text-align: center;
  margin-bottom: 18px;
}
.report-tag {
  font-family: 'SF Mono', ui-monospace, monospace;
  font-size: 0.66rem;
  letter-spacing: 0.24em;
  color: #b97011;
}
.report-id {
  font-family: 'SF Mono', ui-monospace, monospace;
  font-size: 0.7rem;
  color: #9ca3af;
  letter-spacing: 0.16em;
}
.report-body {
  position: relative;
  z-index: 1;
  flex: 1 1 auto;
  min-height: 0;
  overflow-y: auto;
  scrollbar-width: none;
  display: flex;
  flex-direction: column;
  gap: 18px;
  padding-bottom: 8px;
}
.report-body::-webkit-scrollbar { display: none; }

.personality-wrap {
  text-align: center;
  padding: 16px 18px 22px;
  border-radius: 22px;
  background: rgba(255, 251, 235, 0.7);
  border: 1px solid rgba(255, 255, 255, 0.85);
}
.personality-label {
  font-family: 'SF Mono', ui-monospace, monospace;
  font-size: 0.66rem;
  letter-spacing: 0.24em;
  color: #b97011;
  margin-bottom: 6px;
}
.personality-name {
  font-size: 1.5rem;
  font-weight: 800;
  letter-spacing: 0.06em;
  color: #1f2937;
}
.personality-underline {
  width: 64px; height: 3px;
  border-radius: 4px;
  margin: 10px auto 0;
  background: linear-gradient(90deg, #fcd34d, #fb923c);
}
.report-section {
  padding: 14px 16px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.55);
  border: 1px solid rgba(255, 255, 255, 0.85);
}
.section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.74rem;
  letter-spacing: 0.14em;
  color: #b97011;
  margin-bottom: 8px;
  font-weight: 700;
}
.section-title.warn { color: #b91c1c; }
.title-dot {
  width: 8px; height: 8px;
  border-radius: 50%;
  background: linear-gradient(135deg, #fcd34d, #fb923c);
  box-shadow: 0 0 10px rgba(251, 146, 60, 0.5);
}
.title-dot.red {
  background: #ef4444;
  box-shadow: 0 0 10px rgba(239, 68, 68, 0.5);
}
.section-text {
  font-size: 0.88rem;
  line-height: 1.75;
  color: #1f2937;
  white-space: pre-wrap;
  word-break: break-word;
}
.section-text.warn { color: #7f1d1d; }

.medal-award {
  padding: 16px 18px;
  border-radius: 22px;
  background: linear-gradient(135deg, rgba(254, 240, 138, 0.55), rgba(254, 215, 170, 0.55));
  border: 1px solid rgba(255, 255, 255, 0.9);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.95), 0 8px 22px rgba(234, 179, 8, 0.18);
}
.award-label {
  font-size: 0.74rem;
  letter-spacing: 0.16em;
  color: #b45309;
  font-weight: 700;
  margin-bottom: 10px;
}
.medal-card {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 12px 14px;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.55);
  border: 1px solid rgba(255, 255, 255, 0.85);
}
.medal-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 56px; height: 56px;
  border-radius: 50%;
  background: radial-gradient(circle at 30% 25%, #fff5c2, #ffc65e 70%, #d68a14);
  box-shadow: inset 0 2px 4px rgba(255, 255, 255, 0.7), 0 8px 18px rgba(234, 179, 8, 0.35);
  color: #fff;
}
.medal-card.silver .medal-icon {
  background: radial-gradient(circle at 30% 25%, #f8fafc, #cbd5e1 70%, #64748b);
  box-shadow: inset 0 2px 4px rgba(255, 255, 255, 0.7), 0 8px 18px rgba(100, 116, 139, 0.35);
}
.medal-card.bronze .medal-icon {
  background: radial-gradient(circle at 30% 25%, #fde68a, #d97706 70%, #92400e);
  box-shadow: inset 0 2px 4px rgba(255, 255, 255, 0.6), 0 8px 18px rgba(180, 83, 9, 0.35);
}
.medal-info { display: flex; flex-direction: column; gap: 2px; }
.medal-name { font-size: 0.98rem; font-weight: 700; color: #1f2937; }
.medal-tier {
  font-family: 'SF Mono', ui-monospace, monospace;
  font-size: 0.72rem;
  color: #6b7280;
  letter-spacing: 0.06em;
}

/* ============ Error ============ */
.error-box {
  position: relative;
  z-index: 1;
  text-align: center;
  padding: 32px 16px 8px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  align-items: center;
}
.error-title { font-size: 1.05rem; font-weight: 700; color: #b91c1c; }
.error-msg { font-size: 0.86rem; color: #6b7280; max-width: 320px; line-height: 1.7; }
</style>
