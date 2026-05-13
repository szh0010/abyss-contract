<template>
  <div class="abyss-root">
    <!-- 暖色极光背景：与主站保持一致的奶油沙色 + 流体光晕 -->
    <div class="abyss-aurora" aria-hidden="true">
      <span class="blob blob-a"></span>
      <span class="blob blob-b"></span>
      <span class="blob blob-c"></span>
    </div>

    <!-- ============== 顶部面包屑 ============== -->
    <header class="abyss-top liquid-glass">
      <button class="crumb-back spring-bounce" @click="backToLobby">
        <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M15 18l-6-6 6-6"/>
        </svg>
        <span>返回大厅</span>
      </button>
      <div class="crumb-title">
        <span class="crumb-tag">ABYSS · OPS</span>
        <h1>反诈作战大厅</h1>
      </div>
      <div class="crumb-score">
        <span class="score-label">作战积分</span>
        <span class="score-value">{{ totalScore }} / 100</span>
        <div class="score-bar">
          <div class="score-fill" :style="{ width: scorePct + '%' }"></div>
        </div>
      </div>
    </header>

    <!-- ============== 关卡选择：作战大厅 ============== -->
    <transition name="view-swap" mode="out-in">
      <!-- ===== 视图 1：关卡列表 ===== -->
      <section v-if="currentView === 'level-select'" key="select" class="level-select">
        <p class="lobby-hint">三场实战推演 · 累计 100 分解锁「首席反诈专家」勋章</p>

        <div class="level-grid">
          <article
            v-for="lv in levels"
            :key="lv.id"
            class="level-card spring-bounce"
            :class="[
              lv.completed ? 'liquid-glass-success' : (lv.isUnlocked ? 'liquid-glass' : 'locked-level'),
            ]"
            :tabindex="lv.isUnlocked ? 0 : -1"
            @click="enterLevel(lv)"
          >
            <!-- 铁链封印（未解锁时挂上） -->
            <div v-if="!lv.isUnlocked" class="chain-seal" aria-hidden="true">
              <span class="chain-link chain-link-h"></span>
              <span class="chain-link chain-link-v"></span>
              <div class="seal-lock">
                <svg viewBox="0 0 24 24" width="26" height="26" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                  <rect x="4" y="11" width="16" height="10" rx="2"/>
                  <path d="M8 11V7a4 4 0 0 1 8 0v4"/>
                </svg>
              </div>
            </div>

            <header class="lv-head">
              <span class="lv-idx">第 {{ String(lv.id).padStart(2, '0') }} 关</span>
              <span class="lv-points">+{{ lv.points }}</span>
            </header>
            <h3 class="lv-title">{{ lv.title }}</h3>
            <p class="lv-desc">{{ lv.desc }}</p>
            <footer class="lv-foot">
              <span v-if="lv.completed" class="status status-done">已通关</span>
              <span v-else-if="lv.isUnlocked" class="status status-open">点击进入</span>
              <span v-else class="status status-lock">前置未通关</span>
            </footer>
          </article>
        </div>
      </section>

      <!-- ===== 视图 2：对话交互 ===== -->
      <section v-else-if="currentView === 'game'" key="game" class="game-view">
        <div class="game-stage liquid-glass">
          <header class="game-header">
            <span class="scammer-tag">来电/消息 · 可疑对象</span>
            <h2 class="scammer-name">{{ activeLevel.scammerName }}</h2>
            <span class="mission-tag">MISSION {{ String(activeLevel.id).padStart(2, '0') }}</span>
          </header>

          <!-- 骗子台词气泡 -->
          <div class="script-column">
            <transition-group name="bubble" tag="div" class="bubble-stream">
              <div
                v-for="(line, idx) in revealedScript"
                :key="`${activeLevel.id}-${idx}`"
                class="bubble liquid-glass-danger"
              >
                <span class="bubble-tail"></span>
                <p class="bubble-text">{{ line }}</p>
              </div>
            </transition-group>
            <div v-if="isTyping" class="bubble typing">
              <span></span><span></span><span></span>
            </div>
          </div>

          <!-- 玩家选项 -->
          <transition name="fade-up">
            <div v-if="!isTyping && !feedback" class="option-panel">
              <button
                v-for="(opt, i) in activeLevel.options"
                :key="i"
                class="option-btn liquid-glass spring-bounce"
                @click="selectOption(opt)"
              >
                <span class="option-index">{{ String.fromCharCode(65 + i) }}</span>
                <span class="option-text">{{ opt.text }}</span>
              </button>
            </div>
          </transition>

          <!-- 结果反馈 -->
          <transition name="fade-up">
            <div
              v-if="feedback"
              class="feedback-card"
              :class="feedback.type === 'success' ? 'liquid-glass-success' : 'liquid-glass-danger'"
            >
              <div class="feedback-head">
                <span class="feedback-dot"></span>
                <h4>{{ feedback.type === 'success' ? '研判成功 · 你拆穿了骗局' : '险情触发 · 模拟资金失守' }}</h4>
              </div>
              <p class="feedback-text">{{ feedback.desc }}</p>
              <div class="feedback-actions">
                <button
                  v-if="feedback.type === 'success'"
                  class="next-btn liquid-glass-gold spring-bounce"
                  @click="afterSuccess"
                >
                  {{ isLastLevel ? '查看通关战报' : '进入下一关' }}
                </button>
                <button
                  v-else
                  class="retry-btn liquid-glass spring-bounce"
                  @click="retryLevel"
                >重新推演</button>
                <button class="ghost-btn" @click="backToSelect">返回关卡大厅</button>
              </div>
            </div>
          </transition>
        </div>
      </section>

      <!-- ===== 视图 3：通关结算 ===== -->
      <section v-else-if="currentView === 'game-clear'" key="clear" class="clear-view">
        <div class="clear-card liquid-glass-gold">
          <div class="clear-halo"></div>
          <div class="clear-crest">
            <span class="crest-emoji">🏆</span>
          </div>
          <p class="clear-tag">CHIEF · ANTI-FRAUD EXPERT</p>
          <h2 class="clear-title">首席反诈专家</h2>
          <p class="clear-sub">
            你以满分 <b>{{ totalScore }}</b> 通过了全部三场实战推演。<br />
            勋章已自动归档至你的荣誉墙。
          </p>

          <ul class="clear-stats">
            <li v-for="lv in levels" :key="lv.id">
              <span class="stat-idx">#{{ lv.id }}</span>
              <span class="stat-name">{{ lv.title }}</span>
              <span class="stat-pts">+{{ lv.points }}</span>
            </li>
          </ul>

          <div class="clear-actions">
            <button class="clear-btn liquid-glass spring-bounce" @click="restartAll">再练一次</button>
            <button class="clear-btn liquid-glass-success spring-bounce" @click="backToLobby">回到反诈大厅</button>
          </div>
        </div>
      </section>
    </transition>
  </div>
</template>

<!-- SCRIPT_PLACEHOLDER -->
<script setup>
import { ref, computed, watch, onMounted, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import { useMedalStore } from '../stores/medalStore'
import { toast } from '../services/toast'

const router = useRouter()
const medalStore = useMedalStore()

/* ============================================================
   关卡数据 · 由需求方指定，原样使用
============================================================ */
const currentView = ref('level-select') // 'level-select' | 'game' | 'game-clear'
const totalScore = ref(0)
const levels = ref([
  {
    id: 1,
    title: '破晓的夺命 Call',
    desc: '校园贷注销陷阱，目标锁定社会新鲜人。',
    points: 30,
    isUnlocked: true,
    completed: false,
    scammerName: '「京东金融」客服',
    script: [
      '同学您好，系统监测到您大学期间绑定的「校园贷」帐户处于活跃状态。',
      '若不立即注销，明早将上报央行征信系统，这将直接导致您无法办理入职手续！',
    ],
    options: [
      { text: '😱 怎么注销？需要我转帐配合吗？', type: 'fail',    desc: '你表露了恐慌，骗子立刻发送了钓鱼连结...' },
      { text: '🧐 请提供你的客服工号，我将拨打 96110 核实。', type: 'success', desc: '极致冷静。面对官方反诈热线的威慑，骗子瞬间挂断。' },
    ],
  },
  {
    id: 2,
    title: '不存在的完美总裁',
    desc: '杀猪盘投资陷阱，披著情感外衣的镰刀。',
    points: 30,
    isUnlocked: false,
    completed: false,
    scammerName: '投行高管-Alex',
    script: [
      '宝贝，我最近发现我们公司底层交易协议有个漏洞，收益率极高。',
      '这是我帮你建的内部帐户，你先打 5 万进来，我们一起规划未来。',
    ],
    options: [
      { text: '😍 哇，你好厉害，帐号发我！',          type: 'fail',    desc: '被「爱情」冲昏头脑，资金打入空壳帐户，对方人间蒸发。' },
      { text: '🤔 我查了下这个网站的 ICP 备案，根本没有注册资讯？', type: 'success', desc: '数字侦探出击！识破虚假投资网站，保住存款。' },
    ],
  },
  {
    id: 3,
    title: '末路资金保卫战',
    desc: '冒充公检法，极限施压与屏幕共享危机。',
    points: 40,
    isUnlocked: false,
    completed: false,
    scammerName: '市公安局-李警官',
    script: [
      '我是市局刑侦大队。你的银行卡涉嫌跨国洗钱案！',
      '现在立刻下载这款「安全防护APP」并开启萤幕共享，配合资金清查，否则立刻逮捕！',
    ],
    options: [
      { text: '😭 警察叔叔我没犯罪！我马上配合下载！', type: 'fail',    desc: '开启萤幕共享后，你的验证码被对方一览无遗，存款瞬间被清空。' },
      { text: '🛑 警方办案绝不会透过线上要求转帐和萤幕共享，我现在自己去派出所！', type: 'success', desc: '绝对理智！斩断远程操控，你成功防御了最高级别的诈骗攻击。' },
    ],
  },
])

const activeLevelId = ref(null)
const activeLevel = computed(
  () => levels.value.find((l) => l.id === activeLevelId.value) || levels.value[0]
)
const isLastLevel = computed(
  () => activeLevel.value?.id === levels.value[levels.value.length - 1].id
)
const scorePct = computed(() => Math.min(100, Math.round((totalScore.value / 100) * 100)))

/* ============================================================
   骗子台词逐条「打字机」节奏
============================================================ */
const revealedScript = ref([])
const isTyping = ref(false)
const feedback = ref(null)
let typingTimer = null

function startScript() {
  clearTimeout(typingTimer)
  revealedScript.value = []
  feedback.value = null
  isTyping.value = true
  const lines = activeLevel.value.script
  let i = 0
  const tick = () => {
    if (i >= lines.length) {
      isTyping.value = false
      return
    }
    revealedScript.value = [...revealedScript.value, lines[i]]
    i += 1
    typingTimer = setTimeout(tick, 1100)
  }
  // 起手稍稍延迟，给玻璃面板的进入动效让位
  typingTimer = setTimeout(tick, 350)
}

onBeforeUnmount(() => clearTimeout(typingTimer))

/* ============================================================
   视图切换 / 关卡控制
============================================================ */
function enterLevel(lv) {
  if (!lv.isUnlocked) {
    toast.warning('请先通过前一关解锁此任务')
    return
  }
  activeLevelId.value = lv.id
  currentView.value = 'game'
  startScript()
}

function backToSelect() {
  currentView.value = 'level-select'
  feedback.value = null
}

function backToLobby() {
  router.push('/chat')
}

function retryLevel() {
  startScript()
}

/* ============================================================
   选项判定 · 通关结算 · 勋章解锁
============================================================ */
function selectOption(opt) {
  if (isTyping.value || feedback.value) return
  feedback.value = { type: opt.type, desc: opt.desc }

  if (opt.type !== 'success') return

  const lv = activeLevel.value
  if (!lv.completed) {
    lv.completed = true
    totalScore.value += lv.points
    // 解锁下一关
    const nextIdx = levels.value.findIndex((l) => l.id === lv.id) + 1
    if (nextIdx < levels.value.length) {
      levels.value[nextIdx].isUnlocked = true
    }
    toast.success(`+${lv.points} 作战积分`)
  }
}

function afterSuccess() {
  if (totalScore.value >= 100) {
    triggerClear()
    return
  }
  // 自动跳到第一个未完成的关卡，没有则回大厅
  const next = levels.value.find((l) => !l.completed && l.isUnlocked)
  if (next) {
    enterLevel(next)
  } else {
    backToSelect()
  }
}

function triggerClear() {
  // 解锁「首席反诈专家」勋章 → 主大厅勋章墙实时联动
  const newlyAdded = medalStore.unlock({
    id: 'expert',
    icon: '🏆',
    name: '首席反诈专家',
    tier: 'gold',
  })
  if (newlyAdded) {
    toast.success('🏆 解锁勋章：首席反诈专家')
  }
  currentView.value = 'game-clear'
}

function restartAll() {
  totalScore.value = 0
  levels.value.forEach((lv, idx) => {
    lv.completed = false
    lv.isUnlocked = idx === 0
  })
  feedback.value = null
  currentView.value = 'level-select'
}

// 进入页面时把当前用户的勋章拉一遍（防跨账号脏读）
onMounted(() => medalStore.syncWithCurrentUser())

watch(activeLevelId, () => (feedback.value = null))
</script>
<!-- STYLE_PLACEHOLDER -->
<style scoped>
/* ============================================================
   反诈作战大厅 · 液态玻璃 · 物理弹簧 · 铁链封印
============================================================ */
.abyss-root {
  position: relative;
  z-index: 1;
  min-height: 100vh;
  width: 100%;
  padding: 32px clamp(20px, 5vw, 64px) 56px;
  font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display',
               'PingFang SC', 'Helvetica Neue', sans-serif;
  color: #1b1b1f;
  box-sizing: border-box;
  overflow: hidden;
  /* 奶油沙色渐变：与主站 body 同款暖底 */
  background: linear-gradient(to bottom right, #FFFCF5 0%, #FDF5E6 100%);
}

/* ============ 极光流体（暖橘 / 浅黄 / 柔粉） ============ */
.abyss-aurora {
  position: absolute;
  inset: 0;
  z-index: 0;
  overflow: hidden;
  pointer-events: none;
}
.abyss-aurora .blob {
  position: absolute;
  width: 384px;       /* Tailwind w-96 */
  height: 384px;      /* Tailwind h-96 */
  border-radius: 50%;
  filter: blur(64px); /* Tailwind blur-3xl */
  opacity: 0.6;       /* Tailwind opacity-60 */
  mix-blend-mode: multiply;
  will-change: transform;
}
.abyss-aurora .blob-a {
  top: 25%; left: 25%;
  background: #ffd6a8;  /* orange-200 暖色 */
  animation: abyssBlob 7s ease-in-out infinite;
}
.abyss-aurora .blob-b {
  top: 33%; right: 25%;
  background: #fef9c3;  /* yellow-100 */
  animation: abyssBlob 7s ease-in-out infinite;
  animation-delay: -2s;
}
.abyss-aurora .blob-c {
  bottom: 25%; left: 33%;
  background: #ffe4e6;  /* rose-100 */
  animation: abyssBlob 7s ease-in-out infinite;
  animation-delay: -4s;
}
@keyframes abyssBlob {
  0%, 100% { transform: translate(0, 0) scale(1); }
  33%      { transform: translate(30px, -50px) scale(1.1); }
  66%      { transform: translate(-20px, 20px) scale(0.95); }
}

/* 顶部 / 中央内容放到光晕之上 */
.abyss-top,
.level-select,
.game-view,
.clear-view {
  position: relative;
  z-index: 1;
}

/* --- 核心魔法类（与设计稿一致，样式可被全局覆盖） --- */
.liquid-glass {
  background: rgba(255, 255, 255, 0.4);
  backdrop-filter: blur(24px);
  -webkit-backdrop-filter: blur(24px);
  border: 1px solid rgba(255, 255, 255, 0.6);
  box-shadow:
    inset 0 2px 4px rgba(255, 255, 255, 0.9),
    inset 0 -2px 6px rgba(0, 0, 0, 0.05),
    0 8px 32px rgba(0, 0, 0, 0.08);
}
.liquid-glass-danger {
  background: rgba(254, 226, 226, 0.6);
  backdrop-filter: blur(24px);
  -webkit-backdrop-filter: blur(24px);
  border: 1px solid rgba(255, 255, 255, 0.8);
  box-shadow:
    inset 0 2px 4px rgba(255, 255, 255, 1),
    inset 0 -2px 6px rgba(239, 68, 68, 0.2),
    0 8px 32px rgba(239, 68, 68, 0.3);
}
.liquid-glass-gold {
  background: rgba(254, 240, 138, 0.6);
  backdrop-filter: blur(24px);
  -webkit-backdrop-filter: blur(24px);
  border: 1px solid rgba(255, 255, 255, 0.9);
  box-shadow:
    inset 0 2px 4px rgba(255, 255, 255, 1),
    inset 0 -2px 6px rgba(234, 179, 8, 0.2),
    0 8px 32px rgba(234, 179, 8, 0.3);
}
.locked-level {
  background: rgba(200, 200, 200, 0.3);
  backdrop-filter: blur(8px) grayscale(0.8);
  -webkit-backdrop-filter: blur(8px) grayscale(0.8);
  border: 1px solid rgba(255, 255, 255, 0.3);
  position: relative;
  overflow: hidden;
  cursor: not-allowed;
  box-shadow: inset 0 2px 10px rgba(0, 0, 0, 0.1);
}
.locked-level::after {
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0; bottom: 0;
  background: repeating-linear-gradient(
    45deg,
    rgba(0, 0, 0, 0.05),
    rgba(0, 0, 0, 0.05) 10px,
    rgba(255, 255, 255, 0.1) 10px,
    rgba(255, 255, 255, 0.1) 20px
  );
  pointer-events: none;
  z-index: 1;
}
.spring-bounce {
  transition: all 0.5s cubic-bezier(0.25, 1.5, 0.5, 1);
}
.spring-bounce:active:not(:disabled) {
  transform: scale(0.92) translateY(2px);
  box-shadow:
    inset 0 4px 8px rgba(0, 0, 0, 0.1),
    0 2px 8px rgba(0, 0, 0, 0.05);
}

/* ============ 顶部条 ============ */
.abyss-top {
  display: grid;
  grid-template-columns: auto 1fr auto;
  align-items: center;
  gap: 18px;
  padding: 14px 22px;
  border-radius: 22px;
  margin-bottom: 28px;
}
.crumb-back {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  border: none;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.6);
  color: #333;
  font: inherit;
  font-weight: 500;
  font-size: 0.85rem;
  cursor: pointer;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.95);
}
.crumb-title { text-align: center; }
.crumb-tag {
  display: block;
  font-family: 'SF Mono', ui-monospace, monospace;
  font-size: 0.64rem;
  letter-spacing: 0.28em;
  color: #7a6a50;
}
.crumb-title h1 {
  margin-top: 4px;
  font-size: 1.08rem;
  font-weight: 600;
  letter-spacing: 0.24em;
  color: #2d2416;
}
.crumb-score {
  text-align: right;
  min-width: 180px;
}
.score-label {
  display: block;
  font-size: 0.7rem;
  letter-spacing: 0.16em;
  color: #7a6a50;
  text-transform: uppercase;
}
.score-value {
  font-family: 'SF Mono', ui-monospace, monospace;
  font-size: 1rem;
  font-weight: 600;
  color: #e58b1d;
}
.score-bar {
  margin-top: 6px;
  width: 180px;
  height: 6px;
  border-radius: 4px;
  background: rgba(0, 0, 0, 0.06);
  overflow: hidden;
  margin-left: auto;
}
.score-fill {
  height: 100%;
  background: linear-gradient(90deg, #ffd36a, #f5a524 70%, #ff7a50);
  transition: width 0.6s cubic-bezier(0.25, 1.5, 0.5, 1);
}

/* ============ 视图切换 ============ */
.view-swap-enter-active,
.view-swap-leave-active {
  transition:
    opacity 0.45s cubic-bezier(0.22, 1, 0.36, 1),
    transform 0.45s cubic-bezier(0.22, 1, 0.36, 1),
    filter 0.45s ease;
}
.view-swap-enter-from { opacity: 0; transform: translateY(12px) scale(0.985); filter: blur(6px); }
.view-swap-leave-to   { opacity: 0; transform: translateY(-6px) scale(0.995); filter: blur(3px); }

/* ============ 关卡列表 ============ */
.lobby-hint {
  text-align: center;
  font-size: 0.86rem;
  color: #6c5b40;
  letter-spacing: 0.06em;
  margin-bottom: 26px;
}
.level-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 22px;
}
.level-card {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 22px 22px 18px;
  border-radius: 24px;
  cursor: pointer;
  outline: none;
  min-height: 200px;
}
.level-card:not(.locked-level):hover {
  transform: translateY(-2px);
}
.lv-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.lv-idx {
  font-family: 'SF Mono', ui-monospace, monospace;
  font-size: 0.72rem;
  letter-spacing: 0.18em;
  color: #7a6a50;
}
.lv-points {
  font-family: 'SF Mono', ui-monospace, monospace;
  font-size: 0.78rem;
  font-weight: 600;
  color: #e58b1d;
  padding: 2px 10px;
  background: rgba(255, 200, 110, 0.18);
  border-radius: 8px;
}
.lv-title {
  font-size: 1.1rem;
  font-weight: 600;
  letter-spacing: 0.04em;
  color: #2d2416;
}
.lv-desc {
  font-size: 0.86rem;
  line-height: 1.6;
  color: #5b4c34;
  flex: 1;
}
.lv-foot {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  margin-top: 6px;
}
.status {
  font-size: 0.72rem;
  font-weight: 500;
  letter-spacing: 0.1em;
  padding: 4px 10px;
  border-radius: 8px;
}
.status-open { color: #1e7fb6; background: rgba(14, 165, 233, 0.12); }
.status-done { color: #2f8b58; background: rgba(34, 197, 94, 0.14); }
.status-lock { color: #777; background: rgba(0, 0, 0, 0.08); }

/* 铁链封印 */
.chain-seal {
  position: absolute;
  inset: 0;
  z-index: 2;
  pointer-events: none;
}
.chain-link {
  position: absolute;
  background:
    repeating-linear-gradient(
      90deg,
      rgba(60, 60, 70, 0.85) 0 14px,
      rgba(110, 110, 130, 0.85) 14px 18px,
      rgba(60, 60, 70, 0.85) 18px 32px,
      rgba(30, 30, 40, 0.85) 32px 36px
    );
  box-shadow:
    inset 0 1px 1px rgba(255, 255, 255, 0.35),
    inset 0 -1px 2px rgba(0, 0, 0, 0.45),
    0 4px 10px rgba(0, 0, 0, 0.25);
}
.chain-link-h {
  top: 50%; left: -10%;
  width: 120%; height: 14px;
  transform: translateY(-50%) rotate(-6deg);
}
.chain-link-v {
  left: 50%; top: -10%;
  width: 14px; height: 120%;
  transform: translateX(-50%) rotate(8deg);
}
.seal-lock {
  position: absolute;
  top: 50%; left: 50%;
  transform: translate(-50%, -50%);
  width: 56px; height: 56px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  color: #f4f4f4;
  background: radial-gradient(circle at 35% 30%, #4d4d57, #1c1c22 70%);
  box-shadow:
    inset 0 1px 1px rgba(255, 255, 255, 0.4),
    inset 0 -2px 4px rgba(0, 0, 0, 0.6),
    0 6px 18px rgba(0, 0, 0, 0.35);
}

/* ============ 对话视图 ============ */
.game-view {
  display: flex;
  justify-content: center;
}
.game-stage {
  position: relative;
  width: min(840px, 100%);
  padding: 28px 28px 24px;
  border-radius: 28px;
}
.game-header {
  display: grid;
  grid-template-columns: auto 1fr auto;
  gap: 12px;
  align-items: baseline;
  padding-bottom: 14px;
  margin-bottom: 18px;
  border-bottom: 1px dashed rgba(0, 0, 0, 0.08);
}
.scammer-tag,
.mission-tag {
  font-family: 'SF Mono', ui-monospace, monospace;
  font-size: 0.66rem;
  letter-spacing: 0.18em;
  color: #b34155;
  text-transform: uppercase;
}
.mission-tag { color: #7a6a50; text-align: right; }
.scammer-name {
  font-size: 1rem;
  font-weight: 600;
  letter-spacing: 0.06em;
  color: #2d2416;
}

/* 骗子气泡流 */
.script-column { display: flex; flex-direction: column; gap: 12px; }
.bubble-stream { display: flex; flex-direction: column; gap: 12px; }
.bubble {
  position: relative;
  max-width: 80%;
  padding: 12px 16px;
  border-radius: 18px 18px 18px 4px;
  font-size: 0.92rem;
  line-height: 1.7;
  color: #5a1313;
  letter-spacing: 0.01em;
}
.bubble-tail {
  position: absolute;
  left: -6px; bottom: 0;
  width: 14px; height: 14px;
  background: inherit;
  border-left: 1px solid rgba(255, 255, 255, 0.8);
  border-bottom: 1px solid rgba(255, 255, 255, 0.8);
  border-bottom-left-radius: 4px;
  transform: rotate(45deg);
}
.bubble.typing {
  width: 60px;
  display: inline-flex;
  gap: 6px;
  align-items: center;
  justify-content: center;
  padding: 12px 14px;
  background: rgba(254, 226, 226, 0.6);
  backdrop-filter: blur(24px);
  -webkit-backdrop-filter: blur(24px);
}
.bubble.typing span {
  width: 6px; height: 6px; border-radius: 50%;
  background: #b84a4a;
  animation: typing 1.1s infinite ease-in-out;
}
.bubble.typing span:nth-child(2) { animation-delay: 0.18s; }
.bubble.typing span:nth-child(3) { animation-delay: 0.36s; }
@keyframes typing {
  0%, 80%, 100% { transform: scale(0.7); opacity: 0.4; }
  40% { transform: scale(1); opacity: 1; }
}

.bubble-enter-active { transition: all 0.5s cubic-bezier(0.25, 1.5, 0.5, 1); }
.bubble-enter-from   { opacity: 0; transform: translateY(8px) scale(0.94); }

/* 选项 */
.option-panel {
  margin-top: 28px;
  display: grid;
  gap: 12px;
}
.option-btn {
  display: grid;
  grid-template-columns: 36px 1fr;
  align-items: center;
  gap: 14px;
  width: 100%;
  padding: 14px 18px;
  border: none;
  border-radius: 18px;
  cursor: pointer;
  font: inherit;
  font-size: 0.95rem;
  text-align: left;
  color: #2d2416;
}
.option-btn:hover { transform: translateY(-1px); }
.option-index {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px; height: 28px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.8);
  font-family: 'SF Mono', ui-monospace, monospace;
  font-weight: 600;
  color: #e58b1d;
}
.option-text { line-height: 1.6; }

/* 反馈面板 */
.feedback-card {
  margin-top: 22px;
  padding: 20px 22px;
  border-radius: 22px;
}
.feedback-head {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
}
.feedback-head h4 {
  font-size: 0.95rem;
  font-weight: 600;
  letter-spacing: 0.04em;
}
.feedback-dot {
  width: 10px; height: 10px;
  border-radius: 50%;
}
.liquid-glass-success .feedback-dot {
  background: #14b8a6;
  box-shadow: 0 0 12px rgba(20, 184, 166, 0.5);
}
.liquid-glass-danger .feedback-dot {
  background: #e11d48;
  box-shadow: 0 0 12px rgba(225, 29, 72, 0.5);
}
.feedback-text {
  font-size: 0.92rem;
  line-height: 1.7;
  color: #3a2c19;
}
.feedback-actions {
  margin-top: 16px;
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}
.next-btn,
.retry-btn {
  padding: 10px 22px;
  border: none;
  border-radius: 14px;
  font: inherit;
  font-size: 0.9rem;
  font-weight: 600;
  letter-spacing: 0.06em;
  color: #2d2416;
  cursor: pointer;
}
.ghost-btn {
  padding: 10px 18px;
  border: none;
  border-radius: 14px;
  background: transparent;
  font: inherit;
  font-size: 0.85rem;
  color: #6c5b40;
  cursor: pointer;
}
.ghost-btn:hover { color: #2d2416; text-decoration: underline; }

.fade-up-enter-active { transition: all 0.45s cubic-bezier(0.22, 1, 0.36, 1); }
.fade-up-enter-from   { opacity: 0; transform: translateY(8px); }

/* ============ 通关结算 ============ */
.clear-view {
  display: flex;
  justify-content: center;
}
.clear-card {
  position: relative;
  width: min(620px, 100%);
  padding: 44px 40px 34px;
  border-radius: 32px;
  text-align: center;
  overflow: hidden;
}
.clear-halo {
  position: absolute;
  inset: -60px;
  background: radial-gradient(circle at 50% 20%, rgba(255, 220, 120, 0.55), transparent 65%);
  filter: blur(30px);
  pointer-events: none;
  animation: haloPulse 4s ease-in-out infinite alternate;
}
@keyframes haloPulse {
  0%   { opacity: 0.6; transform: scale(1); }
  100% { opacity: 0.95; transform: scale(1.06); }
}
.clear-crest {
  position: relative;
  z-index: 1;
  width: 82px; height: 82px;
  margin: 0 auto 18px;
  border-radius: 50%;
  background: radial-gradient(circle at 30% 25%, #fff5c2, #ffc65e 70%, #d68a14);
  box-shadow:
    inset 0 3px 6px rgba(255, 255, 255, 0.7),
    0 18px 38px rgba(234, 179, 8, 0.45);
  display: flex;
  align-items: center;
  justify-content: center;
  animation: crestSpring 1s cubic-bezier(0.25, 1.5, 0.5, 1);
}
@keyframes crestSpring {
  0%   { transform: scale(0.4) rotate(-12deg); opacity: 0; }
  55%  { transform: scale(1.12) rotate(4deg); opacity: 1; }
  100% { transform: scale(1);                             }
}
.crest-emoji { font-size: 2rem; }
.clear-tag {
  position: relative; z-index: 1;
  font-family: 'SF Mono', ui-monospace, monospace;
  font-size: 0.74rem;
  letter-spacing: 0.28em;
  color: #a66a0d;
}
.clear-title {
  position: relative; z-index: 1;
  margin-top: 6px;
  font-size: 1.6rem;
  font-weight: 700;
  letter-spacing: 0.2em;
  color: #5f3c06;
}
.clear-sub {
  position: relative; z-index: 1;
  margin-top: 14px;
  font-size: 0.9rem;
  line-height: 1.8;
  color: #4b3710;
}
.clear-stats {
  position: relative; z-index: 1;
  list-style: none;
  margin: 22px 0 26px;
  padding: 14px 18px;
  background: rgba(255, 255, 255, 0.55);
  border-radius: 18px;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.95);
}
.clear-stats li {
  display: grid;
  grid-template-columns: 48px 1fr auto;
  gap: 10px;
  padding: 6px 0;
  font-size: 0.86rem;
  align-items: center;
  color: #4b3710;
}
.stat-idx { font-family: 'SF Mono', ui-monospace, monospace; color: #a66a0d; }
.stat-pts { font-family: 'SF Mono', ui-monospace, monospace; color: #b97011; font-weight: 600; }
.clear-actions {
  position: relative; z-index: 1;
  display: flex;
  justify-content: center;
  gap: 12px;
  flex-wrap: wrap;
}
.clear-btn {
  padding: 11px 22px;
  border: none;
  border-radius: 14px;
  font: inherit;
  font-size: 0.9rem;
  font-weight: 600;
  letter-spacing: 0.08em;
  color: #2d2416;
  cursor: pointer;
}

@media (max-width: 720px) {
  .abyss-top { grid-template-columns: 1fr; gap: 10px; text-align: center; }
  .crumb-score { text-align: center; }
  .score-bar { margin: 6px auto 0; }
  .game-stage { padding: 22px 18px; }
  .bubble { max-width: 92%; }
}
</style>

