<template>
  <div class="abyss-root">
    <!-- 暖色极光背景 -->
    <div class="abyss-aurora" aria-hidden="true">
      <span class="blob blob-a"></span>
      <span class="blob blob-b"></span>
      <span class="blob blob-c"></span>
    </div>

    <!-- 顶部条 -->
    <header class="abyss-top liquid-glass">
      <button class="crumb-back spring-bounce" @click="exitGame">
        <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M15 18l-6-6 6-6"/>
        </svg>
        <span>{{ currentView === 'select' ? '返回大厅' : '退出本局' }}</span>
      </button>
      <div class="crumb-title">
        <span class="crumb-tag">ABYSS · SIMULATION</span>
        <h1>{{ headerTitle }}</h1>
      </div>
      <div class="crumb-score">
        <span class="score-label">作战积分</span>
        <span class="score-value">{{ totalScore }} / {{ MASTER_MEDAL_THRESHOLD }}</span>
        <div class="score-bar">
          <div class="score-fill" :style="{ width: scoreProgressPct + '%' }"></div>
        </div>
        <button
          type="button"
          class="medal-wall-btn spring-bounce"
          @click="showMedalWall = true"
        >
          <span class="medal-wall-emoji" aria-hidden="true">🏅</span>
          <span>勋章墙</span>
        </button>
      </div>
    </header>

    <transition name="view-swap" mode="out-in">
      <!-- ===== 视图 1:剧本选择 ===== -->
      <section v-if="currentView === 'select'" key="select" class="script-select">
        <p class="lobby-hint">沉浸式 AI 反诈剧本杀 · 通关一关即可解锁下一关 · 累计 100 分获得「反诈破局宗师」勋章</p>
        <div class="script-grid">
          <article
            v-for="s in scenarioList"
            :key="s.id"
            class="script-card spring-bounce"
            :class="s.isUnlocked ? 'liquid-glass' : 'script-card-locked'"
            :tabindex="s.isUnlocked ? 0 : -1"
            :aria-disabled="!s.isUnlocked"
            @click="startScript(s)"
            @keyup.enter="startScript(s)"
          >
            <div v-if="!s.isUnlocked" class="script-lock-overlay" aria-hidden="true">
              <div class="script-lock-icon">🔒</div>
              <span class="script-lock-text">需通过上一关解锁</span>
            </div>

            <span class="script-stage">第 {{ String(s.id).padStart(2, '0') }} 关</span>
            <div class="script-emoji" aria-hidden="true">{{ s.emoji }}</div>
            <h3 class="script-title">{{ s.name }}</h3>
            <p class="script-desc">{{ s.desc }}</p>
            <span class="script-cta">
              {{ s.isUnlocked ? '点击进入剧本 →' : '🔒 暂未解锁' }}
            </span>
          </article>
        </div>
      </section>

      <!-- ===== 视图 2：剧本对话 ===== -->
      <section v-else-if="currentView === 'play'" key="play" class="play-view">
        <div class="chat-stage liquid-glass">
          <header class="chat-header">
            <span class="scammer-avatar">{{ activeScript?.emoji || '🎭' }}</span>
            <div class="chat-meta">
              <span class="chat-role">{{ activeScript?.scammerRole || '可疑对象' }}</span>
              <span class="chat-name">{{ activeScript?.name || '反诈剧本杀' }}</span>
            </div>
            <span class="chat-status" :class="{ live: !isLoading && gameResult === 'playing' }">
              <i></i>{{ statusText }}
            </span>
          </header>

          <!-- 聊天气泡流 -->
          <div ref="streamRef" class="bubble-stream">
            <transition-group name="bubble" tag="div">
              <div
                v-for="(m, idx) in chatHistory"
                :key="idx"
                class="bubble-row"
                :class="m.role === 'player' ? 'right' : 'left'"
              >
                <span v-if="m.role !== 'player'" class="bubble-avatar bubble-avatar-scammer">
                  {{ activeScript?.emoji || '🎭' }}
                </span>
                <div
                  class="bubble"
                  :class="m.role === 'player' ? 'bubble-player' : 'bubble-scammer'"
                >
                  <p
                    class="bubble-text"
                    :class="{ cursor: m.isTyping }"
                  >{{ m.text }}</p>
                </div>
                <img
                  v-if="m.role === 'player'"
                  class="bubble-avatar bubble-avatar-player"
                  :src="playerAvatar"
                  :alt="username"
                />
              </div>
            </transition-group>

            <div v-if="isLoading" class="bubble-row left">
              <span class="bubble-avatar bubble-avatar-scammer">{{ activeScript?.emoji || '🎭' }}</span>
              <div class="bubble bubble-scammer typing">
                <span></span><span></span><span></span>
              </div>
            </div>
          </div>

          <!-- 流式琥珀色玻璃气泡警告(只在第 1 次危险时弹出,平滑撑开) -->
          <RiskWarningBubble
            v-model:visible="showWarning"
            :message="warningText"
          />

          <!-- 选项区:risk 字段对玩家不可见,只展示 text -->
          <transition name="fade-up">
            <div v-if="gameResult === 'playing' && currentOptions.length" class="option-panel">
              <button
                v-for="(opt, i) in currentOptions"
                :key="i"
                class="option-btn liquid-glass spring-bounce"
                :disabled="isLoading"
                @click="chooseOption(opt)"
              >
                <span class="option-index">{{ String.fromCharCode(65 + i) }}</span>
                <span class="option-text">{{ optionText(opt) }}</span>
              </button>
            </div>
          </transition>

          <!-- 胜利结算 -->
          <transition name="fade-up">
            <div v-if="gameResult === 'win'" class="report-card report-card-win liquid-glass-success">
              <div class="report-crest">🏆</div>
              <span class="report-tag report-tag-win">ABYSS · VICTORY</span>
              <h3 class="report-title">胜利通关 · 你识破了骗局</h3>
              <p class="report-bonus" v-if="lastWinPoints">
                +{{ lastWinPoints }} 反诈作战积分
              </p>
              <p v-if="nextUnlockedHint" class="report-unlock-hint">
                🔓 已解锁下一关:<b>{{ nextUnlockedHint }}</b>
              </p>
              <div class="report-body">
                <p v-for="(line, idx) in reportLines" :key="idx">{{ line }}</p>
              </div>
              <div class="report-actions">
                <button class="report-btn liquid-glass spring-bounce" @click="restartCurrent">
                  再玩一局
                </button>
                <button class="report-btn liquid-glass-success spring-bounce" @click="backToSelect">
                  挑战其他剧本
                </button>
              </div>
            </div>
          </transition>

          <!-- 失败结算 -->
          <transition name="fade-up">
            <div v-if="gameResult === 'lose'" class="report-card report-card-lose liquid-glass-danger">
              <div class="report-crest">💔</div>
              <span class="report-tag report-tag-lose">ABYSS · DEFEAT</span>
              <h3 class="report-title">遗憾落入陷阱</h3>
              <p class="report-bonus report-bonus-warn">
                这一次没能识破。复盘一下,下一次就能挡住。
              </p>
              <div class="report-body">
                <p v-for="(line, idx) in reportLines" :key="idx">{{ line }}</p>
              </div>
              <div class="report-actions">
                <button class="report-btn liquid-glass spring-bounce" @click="restartCurrent">
                  再玩一局
                </button>
                <button class="report-btn liquid-glass-danger spring-bounce" @click="backToSelect">
                  换个剧本练手
                </button>
              </div>
            </div>
          </transition>
        </div>
      </section>
    </transition>

    <!-- ===== 勋章墙 Modal ===== -->
    <transition name="fade-up">
      <div v-if="showMedalWall" class="medal-overlay" @click.self="showMedalWall = false">
        <div class="medal-modal liquid-glass">
          <header class="medal-modal-head">
            <span class="medal-modal-tag">ABYSS · HONOR WALL</span>
            <h3 class="medal-modal-title">🏅 勋章墙</h3>
            <button
              class="medal-modal-close"
              @click="showMedalWall = false"
              aria-label="关闭"
            >×</button>
          </header>

          <div class="medal-progress-block">
            <div class="medal-progress-row">
              <span>当前积分</span>
              <span class="medal-progress-value">
                {{ totalScore }} / {{ MASTER_MEDAL_THRESHOLD }}
              </span>
            </div>
            <div class="medal-progress-bar">
              <div
                class="medal-progress-fill"
                :style="{ width: scoreProgressPct + '%' }"
              ></div>
            </div>
          </div>

          <div class="medal-grid">
            <div
              class="medal-item"
              :class="masterMedalUnlocked ? 'medal-item-active' : 'medal-item-locked'"
            >
              <div class="medal-glow" v-if="masterMedalUnlocked"></div>
              <div class="medal-emoji">🏅</div>
              <h4 class="medal-name">反诈破局宗师</h4>
              <p class="medal-tip">
                {{ masterMedalUnlocked ? '已点亮 · 你已是这场战役的宗师' : '积分满 100 即可解锁' }}
              </p>
            </div>
          </div>

          <div class="medal-modal-foot">
            <button class="report-btn liquid-glass spring-bounce" @click="showMedalWall = false">
              收起勋章墙
            </button>
          </div>
        </div>
      </div>
    </transition>

    <!-- ===== 全局成就解锁动画 ===== -->
    <transition name="fade-up">
      <div v-if="showAchievement" class="achievement-overlay">
        <div class="achievement-card liquid-glass-gold">
          <div class="achievement-confetti" aria-hidden="true">
            <span v-for="i in 18" :key="i" :style="confettiStyle(i)"></span>
          </div>
          <div class="achievement-medal">🏅</div>
          <span class="achievement-tag">ACHIEVEMENT UNLOCKED</span>
          <h3 class="achievement-title">反诈破局宗师</h3>
          <p class="achievement-sub">恭喜你识破全部诈骗剧本,反诈段位拉满!</p>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref, computed, nextTick, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import http from '../services/http'
import { getUsername } from '../services/http'
import { toast } from '../services/toast'
import RiskWarningBubble from '../components/RiskWarningBubble.vue'

const router = useRouter()

/* ============================================================
   剧本元数据 + 线性解锁
   - id 升序为通关顺序;默认仅第 1 关解锁
   - 解锁状态 + 总积分均持久化到 localStorage,刷新不丢失
============================================================ */
const SCENARIO_DEFS = [
  {
    id: 1,
    key: 'shuadan',
    name: '刷单返利局',
    emoji: '💼',
    desc: '高佣金兼职广告把你拉进群,第一笔小额任务真的返了……接下来呢?',
    scammerRole: '某电商「任务派单员」',
    opener: '开始刷单返利局',
  },
  {
    id: 2,
    key: 'youxi_zhanghao',
    name: '游戏账号交易局',
    emoji: '🎮',
    desc: '"高价收号"或"低价出售稀有装备"——交易平台的链接是真的吗?',
    scammerRole: '陌生「玩家/中介」',
    opener: '开始游戏账号交易局',
  },
  {
    id: 3,
    key: 'kefu',
    name: '冒充客服退款局',
    emoji: '📦',
    desc: '"快递丢失主动赔付,请下载远程协助 App"——陷阱就藏在"好心"里。',
    scammerRole: '冒充「电商售后专员」',
    opener: '开始冒充客服退款局',
  },
  {
    id: 4,
    key: 'shazhupan',
    name: '杀猪盘局',
    emoji: '💞',
    desc: '陌生异性的暧昧聊天 + 内幕投资平台,温柔的镰刀正在悄悄落下。',
    scammerRole: '高大上「成功人士」',
    opener: '开始杀猪盘局',
  },
  {
    id: 5,
    key: 'xiaoyuandai',
    name: '校园贷/套路贷局',
    emoji: '📑',
    desc: '"低息免抵押,秒到账"——一旦签字,你将进入万劫不复的滚雪球。',
    scammerRole: '所谓「贷款专员」',
    opener: '开始校园贷套路贷局',
  },
]

const SCORE_PER_WIN = 20
const MASTER_MEDAL_THRESHOLD = 100

const STORAGE_KEY = computed(
  () => `abyss_scenario_progress::${getUsername() || 'guest'}`
)

function loadProgress() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY.value)
    if (!raw) return null
    const data = JSON.parse(raw)
    if (typeof data !== 'object' || data === null) return null
    return data
  } catch {
    return null
  }
}

function saveProgress() {
  const payload = {
    totalScore: totalScore.value,
    unlocked: scenarioList.value.map((s) => ({ id: s.id, isUnlocked: s.isUnlocked })),
    masterMedalUnlocked: masterMedalUnlocked.value,
  }
  try {
    localStorage.setItem(STORAGE_KEY.value, JSON.stringify(payload))
  } catch {
    /* localStorage 写满 / 隐私模式静默 */
  }
}

const scenarioList = ref(
  SCENARIO_DEFS.map((s, idx) => ({ ...s, isUnlocked: idx === 0 }))
)
const totalScore = ref(0)
const masterMedalUnlocked = ref(false)

// 勋章墙弹层 / 全局成就动画
const showMedalWall = ref(false)
const showAchievement = ref(false)

// 胜利结算面板上"下一关解锁提示"用
const nextUnlockedHint = ref('')

const scoreProgressPct = computed(
  () => Math.min(100, Math.round((totalScore.value / MASTER_MEDAL_THRESHOLD) * 100))
)

/* ============================================================
   状态
============================================================ */
const currentView = ref('select') // 'select' | 'play'
const activeScript = ref(null)
const chatHistory = ref([])       // [{ role: 'scammer'|'player'|'system', text }]
const currentOptions = ref([])
const isLoading = ref(false)
const warningMsg = ref('')
const gameResult = ref('playing') // 'playing' | 'win' | 'lose'
const reportData = ref('')        // 当 gameResult !== 'playing' 时填充
const lastWinPoints = ref(0)
const conversationId = ref(null)

// 前端强制计分板:每进新剧本清零
const dangerCount = ref(0)
const safeCount = ref(0)

// 流式琥珀色玻璃气泡警告(只在 dangerCount === 1 时弹出一次)
const showWarning = ref(false)
const warningText = ref('')

const streamRef = ref(null)

const username = computed(() => getUsername() || 'guest')
const playerAvatar = computed(
  () => `https://api.dicebear.com/7.x/notionists/svg?seed=${encodeURIComponent(username.value)}`
)
const reportLines = computed(() =>
  String(reportData.value || '')
    .split(/\r?\n/)
    .map((l) => l.trim())
    .filter(Boolean)
)
const headerTitle = computed(() => {
  if (currentView.value === 'select') return '反诈剧本杀 · 选择剧本'
  if (gameResult.value === 'win') return '反诈剧本杀 · 胜利通关'
  if (gameResult.value === 'lose') return '反诈剧本杀 · 落入陷阱'
  return '反诈剧本杀 · 沉浸推演中'
})
const statusText = computed(() => {
  if (gameResult.value === 'win') return '本局已胜利'
  if (gameResult.value === 'lose') return '本局已结束'
  if (isLoading.value) return 'AI 思考中…'
  return '在线 · 实时推演'
})

/* ============================================================
   滚动到底
============================================================ */
async function scrollToBottom() {
  await nextTick()
  const el = streamRef.value
  if (el) el.scrollTop = el.scrollHeight + 999
}
/* ============================================================
   单回合:把消息发给 /game/simulate,把响应渲染到聊天流
   关键:scammer_message 走真·逐字打字机,选项在打字结束后才弹出
============================================================ */
const PUNCT_PAUSE = ['，', '。', '！', '？', '\n']

function typewriteScammer(fullText) {
  // 推入空壳气泡(text:'',isTyping:true) → 立刻拿到 reactive proxy
  chatHistory.value.push({ role: 'scammer', text: '', isTyping: true })
  const idx = chatHistory.value.length - 1
  const targetMessage = chatHistory.value[idx]

  return new Promise((resolve) => {
    if (!fullText) {
      targetMessage.text = ''
      targetMessage.isTyping = false
      resolve()
      return
    }
    let i = 0
    const type = () => {
      if (i < fullText.length) {
        const ch = fullText.charAt(i)
        targetMessage.text += ch        // ← 通过 proxy setter,Vue 才能追踪到
        i++
        let d = 30 + Math.random() * 30
        if (PUNCT_PAUSE.includes(ch)) d += 150
        scrollToBottom()
        setTimeout(type, d)
      } else {
        targetMessage.isTyping = false
        scrollToBottom()
        resolve()
      }
    }
    type()
  })
}

async function sendTurn(userMessage, { hidden = false, displayText = null, localCounted = null } = {}) {
  if (isLoading.value) return
  if (!hidden) {
    // 玩家气泡只显示干净文本(displayText),隐藏隐形指令
    chatHistory.value.push({
      role: 'player',
      text: displayText ?? userMessage,
    })
    scrollToBottom()
  }

  isLoading.value = true
  currentOptions.value = []   // 隐藏底部按钮,直到 AI 打字结束
  // 玩家点了下一项,先把上一回合留着的预警气泡收起来
  showWarning.value = false

  try {
    const { data } = await http.post('/game/simulate', {
      user_message: userMessage,
      conversation_id: conversationId.value || undefined,
    })

    if (data?.conversation_id) {
      conversationId.value = data.conversation_id
    }

    // —— 新协议字段 ——
    const reply = String(data?.reply || data?.scammer_message || '').trim()
    const analysis = String(data?.analysis_message || '').trim()
    const isDangerous = !!data?.is_dangerous
    const isSafe = !!data?.is_safe
    const serverResult = String(data?.game_result || '').toLowerCase()

    // 三点 typing 指示器先撤掉,让位给真·打字机
    isLoading.value = false

    if (reply) {
      await typewriteScammer(reply)
    }

    // —— 后端计分同步:仅在前端没计过分时才追加(双重保险防重复)——
    if (isDangerous && localCounted !== 'danger') dangerCount.value += 1
    if (isSafe      && localCounted !== 'safe')   safeCount.value   += 1

    // —— 失败裁决:计分阈值 || 服务端判定 ——
    if (dangerCount.value >= 2 || serverResult === 'lose') {
      gameResult.value = 'lose'
      currentOptions.value = []
      reportData.value = analysis
        || data?.report
        || '很遗憾,这一次落入了陷阱。请记住这次的关键节点,下次一定能挡住。'
      toast.danger('💔 很遗憾,落入了陷阱')
      return
    }

    // —— 胜利裁决:计分阈值 || 服务端判定 ——
    if (safeCount.value >= 3 || serverResult === 'win') {
      gameResult.value = 'win'
      currentOptions.value = []
      reportData.value = analysis
        || data?.report
        || '恭喜你识破了这场骗局,你的反诈直觉非常敏锐。'
      await onWin()
      return
    }

    // —— 第 1 次危险:流式琥珀气泡警告 ——
    if (dangerCount.value === 1 && (isDangerous || localCounted === 'danger')) {
      warningText.value = analysis
        || '这一步操作存在风险,再走一步就可能落入陷阱。请提高警惕。'
      showWarning.value = true
      toast.warning('⚠️ 实时反诈预警')
    }

    // —— 仍然进行中:把后端给的选项弹出来 ——
    gameResult.value = 'playing'
    reportData.value = ''
    currentOptions.value = Array.isArray(data?.options) ? data.options : []
  } catch (e) {
    console.error('[AbyssGame] simulate failed', e)
    chatHistory.value.push({
      role: 'system',
      text: '(AI 链路异常,请稍后再试。如确有紧急情况请拨打 96110 反诈专线。)',
    })
    isLoading.value = false
  } finally {
    scrollToBottom()
  }
}

/* ============================================================
   胜利结算:加分 + 解锁下一关 + 满分勋章 + 持久化
============================================================ */
async function onWin() {
  if (!activeScript.value) return
  const lv = scenarioList.value.find((s) => s.id === activeScript.value.id)

  // 1. 加分
  const points = SCORE_PER_WIN
  lastWinPoints.value = points
  totalScore.value = Math.min(MASTER_MEDAL_THRESHOLD, totalScore.value + points)
  toast.success(`🏆 +${points} 反诈作战积分`)

  // 2. 解锁下一关
  nextUnlockedHint.value = ''
  if (lv) {
    const nextIdx = scenarioList.value.findIndex((s) => s.id === lv.id) + 1
    if (nextIdx > 0 && nextIdx < scenarioList.value.length) {
      const next = scenarioList.value[nextIdx]
      if (!next.isUnlocked) {
        next.isUnlocked = true
        nextUnlockedHint.value = next.name
        toast.success(`🔓 已解锁下一关:${next.name}`)
      } else {
        // 已经早就解过(重玩),依然给个提示
        nextUnlockedHint.value = next.name
      }
    }
  }

  // 3. 满分勋章
  if (totalScore.value >= MASTER_MEDAL_THRESHOLD && !masterMedalUnlocked.value) {
    masterMedalUnlocked.value = true
    showAchievement.value = true
    toast.success('🏅 反诈破局宗师 · 勋章已解锁!')
    setTimeout(() => { showAchievement.value = false }, 4500)
  }

  // 4. 持久化(本地 + 后端)
  saveProgress()
  try {
    await http.post('/game/submit', {
      current_stage: Math.max(1, lv?.id ?? 1),
      score: totalScore.value,
      unlocked_medals: masterMedalUnlocked.value
        ? [{ id: 'fanzha_master', name: '反诈破局宗师', icon: '🏅', tier: 'gold' }]
        : [],
    })
  } catch (e) {
    if (e?.response?.status === 401) return
    console.warn('[AbyssGame] /game/submit failed', e)
  }
}

/* ============================================================
   入口控制
============================================================ */
async function startScript(s) {
  // 锁关:点击未解锁卡片 → toast 提示而不是进入
  const lv = scenarioList.value.find((x) => x.id === s.id)
  if (!lv?.isUnlocked) {
    toast.warning('需通过上一关解锁')
    return
  }
  activeScript.value = s
  chatHistory.value = []
  currentOptions.value = []
  warningMsg.value = ''
  gameResult.value = 'playing'
  reportData.value = ''
  lastWinPoints.value = 0
  nextUnlockedHint.value = ''
  conversationId.value = null
  dangerCount.value = 0
  safeCount.value = 0
  showWarning.value = false
  warningText.value = ''
  currentView.value = 'play'
  await nextTick()
  await sendTurn(s.opener, { hidden: true })
}

/* ============================================================
   选项点击:前端硬控计分 + 隐形指令强制收束(双重保险)
   1. 玩家点击瞬间,前端按 opt.risk 增计;后端响应里若再来 is_dangerous/is_safe,
      用 localCounted 标记防止重复计分。
   2. 命中阈值后,把"系统最高指令"拼到 finalMessage 尾部偷偷发给 AI,
      让它必须输出对应的 game_result。
   3. 玩家气泡只渲染 option.text,risk 与隐形指令都不会落到 DOM。
============================================================ */
function optionText(opt) {
  if (typeof opt === 'string') return opt
  return String(opt?.text ?? '')
}

function optionRisk(opt) {
  if (typeof opt === 'string') return null
  const r = String(opt?.risk || '').toLowerCase()
  return r === 'high' || r === 'low' ? r : null
}

function chooseOption(opt) {
  if (isLoading.value || gameResult.value !== 'playing') return

  // 1. 取出可见文本(玩家气泡渲染用)
  const text = optionText(opt)
  if (!text) return

  // 2. 前端硬控计分:点击瞬间立即 ++,标记 localCounted 防止后端重复加
  const risk = optionRisk(opt)
  let localCounted = null
  if (risk === 'high') {
    dangerCount.value += 1
    localCounted = 'danger'
  } else if (risk === 'low') {
    safeCount.value += 1
    localCounted = 'safe'
  }

  // 3. 隐形指令注入:阈值命中即强制 AI 收束本回合
  let finalMessage = text
  if (dangerCount.value >= 2) {
    finalMessage +=
      '\n[系统最高指令:玩家已达到2次高危操作!你必须立刻停止废话,' +
      '输出 game_result: lose 并生成被骗 report!]'
  } else if (safeCount.value >= 3) {
    finalMessage +=
      '\n[系统最高指令:玩家已达到3次安全操作!你必须立刻输出 game_result: win 并生成通关 report!]'
  }

  // 4. 分流发送:user_message=finalMessage(带隐指),气泡=干净 text
  sendTurn(finalMessage, { displayText: text, localCounted })
}

function restartCurrent() {
  if (!activeScript.value) {
    backToSelect()
    return
  }
  startScript(activeScript.value)
}

function backToSelect() {
  currentView.value = 'select'
  chatHistory.value = []
  currentOptions.value = []
  warningMsg.value = ''
  gameResult.value = 'playing'
  reportData.value = ''
  lastWinPoints.value = 0
  nextUnlockedHint.value = ''
  conversationId.value = null
  dangerCount.value = 0
  safeCount.value = 0
  showWarning.value = false
  warningText.value = ''
  activeScript.value = null
}

function exitGame() {
  if (currentView.value === 'play') {
    backToSelect()
  } else {
    router.push('/chat')
  }
}

// 撒花粒子样式生成(纯随机偏移 + 颜色)
function confettiStyle(seed) {
  const colors = ['#ff7a50', '#f5a524', '#ffd36a', '#fde68a', '#fb7185', '#facc15']
  const left = ((seed * 53) % 100)
  const delay = ((seed * 31) % 14) / 10
  const dur = 1.6 + ((seed * 17) % 9) / 10
  const color = colors[seed % colors.length]
  const rotate = ((seed * 47) % 360)
  return {
    left: `${left}%`,
    background: color,
    animationDelay: `${delay}s`,
    animationDuration: `${dur}s`,
    transform: `rotate(${rotate}deg)`,
  }
}

onMounted(() => {
  // 从 localStorage 还原解锁 + 积分,保证刷新后进度不丢
  const saved = loadProgress()
  if (saved) {
    if (typeof saved.totalScore === 'number') {
      totalScore.value = Math.max(0, Math.min(MASTER_MEDAL_THRESHOLD, saved.totalScore))
    }
    if (Array.isArray(saved.unlocked)) {
      const map = new Map(saved.unlocked.map((u) => [u.id, !!u.isUnlocked]))
      scenarioList.value.forEach((s, idx) => {
        s.isUnlocked = idx === 0 ? true : (map.get(s.id) ?? false)
      })
    }
    masterMedalUnlocked.value =
      !!saved.masterMedalUnlocked || totalScore.value >= MASTER_MEDAL_THRESHOLD
  }
})
</script>

<style scoped>
/* ============ 根容器 ============ */
.abyss-root {
  position: relative;
  padding: 28px 32px 60px;
  min-height: 100%;
  color: #2d2416;
  background:
    radial-gradient(ellipse at top, #fff7ec 0%, transparent 60%),
    linear-gradient(180deg, #fffaf2 0%, #fdf3e3 100%);
  font-family: -apple-system, BlinkMacSystemFont, 'PingFang SC', 'Helvetica Neue', sans-serif;
}

/* ============ 极光背景 ============ */
.abyss-aurora {
  position: absolute; inset: 0; z-index: 0;
  overflow: hidden; pointer-events: none;
}
.abyss-aurora .blob {
  position: absolute;
  width: 384px; height: 384px;
  border-radius: 50%;
  filter: blur(64px);
  opacity: 0.6;
  mix-blend-mode: multiply;
  will-change: transform;
}
.abyss-aurora .blob-a {
  top: 25%; left: 25%;
  background: #ffd6a8;
  animation: abyssBlob 7s ease-in-out infinite;
}
.abyss-aurora .blob-b {
  top: 33%; right: 25%;
  background: #fef9c3;
  animation: abyssBlob 7s ease-in-out infinite;
  animation-delay: -2s;
}
.abyss-aurora .blob-c {
  bottom: 25%; left: 33%;
  background: #ffe4e6;
  animation: abyssBlob 7s ease-in-out infinite;
  animation-delay: -4s;
}
@keyframes abyssBlob {
  0%, 100% { transform: translate(0, 0) scale(1); }
  33%      { transform: translate(30px, -50px) scale(1.1); }
  66%      { transform: translate(-20px, 20px) scale(0.95); }
}
/* ============ 玻璃材质（统一） ============ */
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
  background: rgba(254, 226, 226, 0.65);
  backdrop-filter: blur(24px);
  -webkit-backdrop-filter: blur(24px);
  border: 1px solid rgba(255, 255, 255, 0.8);
  box-shadow:
    inset 0 2px 4px rgba(255, 255, 255, 1),
    inset 0 -2px 6px rgba(239, 68, 68, 0.2),
    0 8px 32px rgba(239, 68, 68, 0.25);
}
.liquid-glass-success {
  background: rgba(187, 247, 208, 0.55);
  backdrop-filter: blur(24px);
  -webkit-backdrop-filter: blur(24px);
  border: 1px solid rgba(255, 255, 255, 0.8);
  box-shadow:
    inset 0 2px 4px rgba(255, 255, 255, 1),
    inset 0 -2px 6px rgba(34, 197, 94, 0.2),
    0 8px 32px rgba(34, 197, 94, 0.22);
}
.liquid-glass-gold {
  background: rgba(254, 240, 138, 0.55);
  backdrop-filter: blur(24px);
  -webkit-backdrop-filter: blur(24px);
  border: 1px solid rgba(255, 255, 255, 0.9);
  box-shadow:
    inset 0 2px 4px rgba(255, 255, 255, 1),
    inset 0 -2px 6px rgba(234, 179, 8, 0.2),
    0 8px 32px rgba(234, 179, 8, 0.28);
}
.spring-bounce {
  transition: all 0.5s cubic-bezier(0.25, 1.5, 0.5, 1);
}
.spring-bounce:active:not(:disabled) {
  transform: scale(0.94) translateY(2px);
}

/* ============ 顶部条 ============ */
.abyss-top {
  position: relative;
  z-index: 1;
  display: grid;
  grid-template-columns: auto 1fr auto;
  align-items: center;
  gap: 18px;
  padding: 14px 22px;
  border-radius: 22px;
  margin-bottom: 22px;
}
.crumb-back {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  border: none;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.65);
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
  letter-spacing: 0.2em;
  color: #2d2416;
}
.crumb-score {
  text-align: right;
  min-width: 200px;
}
.score-label {
  display: block;
  font-size: 0.7rem;
  letter-spacing: 0.16em;
  color: #7a6a50;
  text-transform: uppercase;
}
.score-value {
  font-size: 0.95rem;
  font-weight: 600;
  color: #e58b1d;
}
/* ============ 视图切换 ============ */
.script-select,
.play-view {
  position: relative;
  z-index: 1;
}
.view-swap-enter-active,
.view-swap-leave-active {
  transition:
    opacity 0.45s cubic-bezier(0.22, 1, 0.36, 1),
    transform 0.45s cubic-bezier(0.22, 1, 0.36, 1),
    filter 0.45s ease;
}
.view-swap-enter-from { opacity: 0; transform: translateY(12px) scale(0.985); filter: blur(6px); }
.view-swap-leave-to   { opacity: 0; transform: translateY(-6px) scale(0.995); filter: blur(3px); }

/* ============ 剧本选择 ============ */
.lobby-hint {
  text-align: center;
  font-size: 0.95rem;
  color: #7a6a50;
  margin: 6px 0 22px;
  letter-spacing: 0.04em;
}
.script-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 18px;
}
.script-card {
  position: relative;
  padding: 22px 22px 18px;
  border-radius: 22px;
  cursor: pointer;
  text-align: left;
  outline: none;
}
.script-card:focus-visible {
  box-shadow:
    inset 0 2px 4px rgba(255, 255, 255, 0.9),
    0 0 0 3px rgba(245, 165, 36, 0.5);
}
.script-emoji {
  font-size: 2.2rem;
  line-height: 1;
  margin-bottom: 10px;
}
.script-title {
  margin: 0 0 6px;
  font-size: 1.08rem;
  font-weight: 600;
  color: #2d2416;
  letter-spacing: 0.04em;
}
.script-desc {
  margin: 0 0 14px;
  font-size: 0.86rem;
  line-height: 1.55;
  color: #6b5b40;
}
.script-cta {
  display: inline-block;
  font-size: 0.8rem;
  font-weight: 600;
  color: #e58b1d;
  letter-spacing: 0.06em;
}

/* ============ 对话舞台 ============ */
.chat-stage {
  border-radius: 28px;
  padding: 22px 22px 24px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  min-height: 560px;
}
.chat-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding-bottom: 14px;
  border-bottom: 1px dashed rgba(0, 0, 0, 0.08);
}
.scammer-avatar {
  width: 44px; height: 44px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.7);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.95);
}
.chat-meta { flex: 1; display: flex; flex-direction: column; gap: 2px; }
.chat-role {
  font-size: 0.72rem;
  letter-spacing: 0.18em;
  color: #a07b3a;
  text-transform: uppercase;
}
.chat-name {
  font-size: 1rem;
  font-weight: 600;
  color: #2d2416;
}
.chat-status {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 0.78rem;
  color: #7a6a50;
  padding: 4px 10px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.55);
  border: 1px solid rgba(255, 255, 255, 0.8);
}
.chat-status i {
  width: 8px; height: 8px;
  border-radius: 50%;
  background: #cbb38a;
}
.chat-status.live i {
  background: #43c779;
  box-shadow: 0 0 0 4px rgba(67, 199, 121, 0.18);
}
/* ============ 气泡流 ============ */
.bubble-stream {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 14px;
  max-height: 56vh;
  min-height: 280px;
  overflow-y: auto;
  padding: 8px 4px 4px;
  scrollbar-width: thin;
  scrollbar-color: rgba(0,0,0,0.15) transparent;
}
.bubble-stream::-webkit-scrollbar { width: 8px; }
.bubble-stream::-webkit-scrollbar-thumb {
  background: rgba(0, 0, 0, 0.12);
  border-radius: 4px;
}
.bubble-row {
  display: flex;
  align-items: flex-end;
  gap: 10px;
  max-width: 100%;
}
.bubble-row.left { justify-content: flex-start; }
.bubble-row.right { justify-content: flex-end; }
.bubble-avatar {
  width: 36px; height: 36px;
  border-radius: 50%;
  flex-shrink: 0;
  background: rgba(255, 255, 255, 0.7);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 1.15rem;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.9);
  object-fit: cover;
}
.bubble-avatar-player {
  background: #fff;
  border: 1px solid rgba(255, 255, 255, 0.8);
}
.bubble {
  position: relative;
  max-width: 72%;
  padding: 11px 14px;
  border-radius: 16px;
  line-height: 1.6;
  font-size: 0.94rem;
  word-wrap: break-word;
  white-space: pre-wrap;
}
.bubble-scammer {
  background: rgba(255, 255, 255, 0.78);
  color: #2d2416;
  border-top-left-radius: 4px;
  border: 1px solid rgba(255, 255, 255, 0.85);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.9),
    0 6px 20px rgba(0, 0, 0, 0.05);
}
.bubble-player {
  background: linear-gradient(135deg, #ffd36a, #f5a524);
  color: #4a2f00;
  border-top-right-radius: 4px;
  border: 1px solid rgba(255, 255, 255, 0.6);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.7),
    0 6px 18px rgba(245, 165, 36, 0.3);
}
.bubble-text {
  margin: 0;
}

/* 打字机光标 */
.bubble-text.cursor::after {
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
.bubble.typing {
  display: inline-flex;
  gap: 4px;
  align-items: center;
}
.bubble.typing span {
  width: 6px; height: 6px;
  border-radius: 50%;
  background: #b89b6c;
  animation: typingDot 1.4s infinite ease-in-out;
}
.bubble.typing span:nth-child(2) { animation-delay: 0.18s; }
.bubble.typing span:nth-child(3) { animation-delay: 0.36s; }
@keyframes typingDot {
  0%, 80%, 100% { transform: scale(0.6); opacity: 0.4; }
  40%           { transform: scale(1);   opacity: 1;   }
}

.bubble-enter-active { transition: all 0.4s cubic-bezier(0.25, 1.5, 0.5, 1); }
.bubble-enter-from   { opacity: 0; transform: translateY(8px) scale(0.96); }

/* ============ 警示弹窗 ============ */
.warning-pop {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 14px 16px 14px 14px;
  border-radius: 18px;
}
.warning-icon {
  font-size: 1.6rem;
  line-height: 1;
  flex-shrink: 0;
}
.warning-body { flex: 1; }
.warning-body h4 {
  margin: 0 0 4px;
  font-size: 0.92rem;
  color: #b91c1c;
  letter-spacing: 0.06em;
}
.warning-body p {
  margin: 0;
  font-size: 0.86rem;
  line-height: 1.55;
  color: #5b2222;
}
.warning-close {
  background: transparent;
  border: none;
  font-size: 1.2rem;
  color: #b91c1c;
  cursor: pointer;
  line-height: 1;
}
/* ============ 选项区 ============ */
.option-panel {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding-top: 8px;
}
.option-btn {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 13px 16px;
  border-radius: 16px;
  border: 1px solid rgba(255, 255, 255, 0.6);
  font: inherit;
  font-size: 0.94rem;
  color: #2d2416;
  text-align: left;
  cursor: pointer;
  width: 100%;
}
.option-btn:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}
.option-index {
  width: 28px; height: 28px;
  border-radius: 10px;
  background: rgba(245, 165, 36, 0.18);
  color: #b8730d;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-family: 'SF Mono', ui-monospace, monospace;
  font-size: 0.78rem;
  flex-shrink: 0;
}
.option-text {
  flex: 1;
  line-height: 1.5;
}

/* ============ 结算报告 ============ */
.report-card {
  border-radius: 24px;
  padding: 24px 24px 20px;
  text-align: center;
  position: relative;
  overflow: hidden;
}
.report-card-win {
  border: 1px solid rgba(95, 191, 138, 0.45);
}
.report-card-lose {
  border: 1px solid rgba(217, 74, 103, 0.45);
}
.report-crest {
  font-size: 2.4rem;
  line-height: 1;
  margin-bottom: 6px;
}
.report-tag {
  display: inline-block;
  font-family: 'SF Mono', ui-monospace, monospace;
  font-size: 0.7rem;
  letter-spacing: 0.32em;
  color: #a07b3a;
  margin-bottom: 6px;
}
.report-tag-win  { color: #2f8f5d; }
.report-tag-lose { color: #b1394d; }
.report-title {
  margin: 0 0 8px;
  font-size: 1.2rem;
  font-weight: 700;
  color: #2d2416;
  letter-spacing: 0.1em;
}
.report-bonus {
  margin: 0 0 14px;
  font-size: 0.92rem;
  font-weight: 600;
  color: #2f8f5d;
  letter-spacing: 0.04em;
}
.report-bonus-warn {
  color: #b1394d;
  font-weight: 500;
}
.report-body {
  text-align: left;
  background: rgba(255, 255, 255, 0.55);
  border: 1px solid rgba(255, 255, 255, 0.75);
  border-radius: 16px;
  padding: 14px 16px;
  margin: 0 auto 16px;
  max-width: 720px;
}
.report-body p {
  margin: 0 0 8px;
  font-size: 0.92rem;
  line-height: 1.7;
  color: #4a3b1c;
}
.report-body p:last-child { margin-bottom: 0; }
.report-actions {
  display: flex;
  justify-content: center;
  flex-wrap: wrap;
  gap: 12px;
}
.report-btn {
  padding: 10px 20px;
  border-radius: 14px;
  border: 1px solid rgba(255, 255, 255, 0.6);
  background: rgba(255, 255, 255, 0.6);
  font: inherit;
  font-weight: 600;
  font-size: 0.9rem;
  color: #2d2416;
  cursor: pointer;
}

/* ============ 通用淡入 ============ */
.fade-up-enter-active,
.fade-up-leave-active {
  transition: opacity 0.35s ease, transform 0.35s ease;
}
.fade-up-enter-from { opacity: 0; transform: translateY(8px); }
.fade-up-leave-to   { opacity: 0; transform: translateY(-4px); }

/* ============ 响应式 ============ */
@media (max-width: 720px) {
  .abyss-root { padding: 18px 14px 40px; }
  .abyss-top { grid-template-columns: auto 1fr; }
  .crumb-score { display: none; }
  .chat-stage { padding: 16px 14px; min-height: 520px; }
  .bubble { max-width: 82%; font-size: 0.9rem; }
  .script-grid { grid-template-columns: 1fr; }
}

/* ============ 顶部积分进度条 + 勋章墙按钮 ============ */
.crumb-score {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 4px;
  min-width: 220px;
}
.score-bar {
  width: 180px;
  height: 6px;
  border-radius: 4px;
  background: rgba(0, 0, 0, 0.06);
  overflow: hidden;
}
.score-fill {
  height: 100%;
  background: linear-gradient(90deg, #ffd36a, #f5a524 70%, #ff7a50);
  transition: width 0.6s cubic-bezier(0.25, 1.5, 0.5, 1);
}
.medal-wall-btn {
  margin-top: 6px;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border: 1px solid rgba(255, 255, 255, 0.7);
  border-radius: 999px;
  background: linear-gradient(135deg, rgba(255, 235, 174, 0.85), rgba(255, 200, 130, 0.85));
  font: inherit;
  font-size: 0.78rem;
  font-weight: 600;
  color: #6b3e0a;
  letter-spacing: 0.04em;
  cursor: pointer;
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.95),
    0 4px 14px rgba(245, 165, 36, 0.25);
}
.medal-wall-emoji { font-size: 0.95rem; line-height: 1; }

/* ============ 锁定剧本卡 ============ */
.script-card { position: relative; }
.script-stage {
  position: absolute;
  top: 14px; right: 16px;
  font-family: 'SF Mono', ui-monospace, monospace;
  font-size: 0.7rem;
  letter-spacing: 0.16em;
  color: #a07b3a;
}
.script-card-locked {
  background: rgba(220, 215, 205, 0.45);
  backdrop-filter: blur(10px) grayscale(0.55);
  -webkit-backdrop-filter: blur(10px) grayscale(0.55);
  border: 1px solid rgba(255, 255, 255, 0.4);
  cursor: not-allowed;
  position: relative;
  overflow: hidden;
  filter: saturate(0.6);
  box-shadow: inset 0 2px 6px rgba(0, 0, 0, 0.06);
}
.script-card-locked .script-emoji,
.script-card-locked .script-title,
.script-card-locked .script-desc,
.script-card-locked .script-cta,
.script-card-locked .script-stage {
  opacity: 0.55;
}
.script-card-locked .script-cta { color: #8a7458; }
.script-lock-overlay {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 6px;
  background:
    repeating-linear-gradient(
      45deg,
      rgba(0, 0, 0, 0.04),
      rgba(0, 0, 0, 0.04) 10px,
      rgba(255, 255, 255, 0.08) 10px,
      rgba(255, 255, 255, 0.08) 20px
    );
  border-radius: inherit;
  pointer-events: none;
  z-index: 2;
}
.script-lock-icon {
  font-size: 2rem;
  filter: drop-shadow(0 4px 12px rgba(0, 0, 0, 0.15));
}
.script-lock-text {
  font-size: 0.78rem;
  letter-spacing: 0.08em;
  color: #6b5b40;
  background: rgba(255, 255, 255, 0.6);
  padding: 4px 10px;
  border-radius: 999px;
  border: 1px solid rgba(255, 255, 255, 0.7);
}

/* ============ 胜利面板下一关解锁提示 ============ */
.report-unlock-hint {
  margin: -2px 0 14px;
  padding: 8px 14px;
  display: inline-block;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.65);
  border: 1px solid rgba(255, 255, 255, 0.8);
  font-size: 0.86rem;
  color: #4a3b1c;
  letter-spacing: 0.02em;
}
.report-unlock-hint b { color: #b8730d; font-weight: 700; }

/* ============ 勋章墙 Modal ============ */
.medal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(45, 36, 22, 0.4);
  backdrop-filter: blur(6px);
  -webkit-backdrop-filter: blur(6px);
  z-index: 200;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
}
.medal-modal {
  position: relative;
  width: min(520px, 100%);
  max-height: 88vh;
  overflow-y: auto;
  border-radius: 28px;
  padding: 26px 26px 22px;
  display: flex;
  flex-direction: column;
  gap: 18px;
}
.medal-modal-head {
  text-align: center;
  position: relative;
  padding-bottom: 14px;
  border-bottom: 1px dashed rgba(0, 0, 0, 0.08);
}
.medal-modal-tag {
  display: block;
  font-family: 'SF Mono', ui-monospace, monospace;
  font-size: 0.7rem;
  letter-spacing: 0.32em;
  color: #a07b3a;
}
.medal-modal-title {
  margin: 4px 0 0;
  font-size: 1.2rem;
  font-weight: 700;
  letter-spacing: 0.12em;
  color: #2d2416;
}
.medal-modal-close {
  position: absolute;
  top: -4px; right: -4px;
  width: 32px; height: 32px;
  border-radius: 50%;
  border: 1px solid rgba(0, 0, 0, 0.08);
  background: rgba(255, 255, 255, 0.8);
  font-size: 1rem;
  color: #5b5040;
  cursor: pointer;
  line-height: 1;
}

.medal-progress-block {
  background: rgba(255, 255, 255, 0.55);
  border: 1px solid rgba(255, 255, 255, 0.75);
  border-radius: 18px;
  padding: 14px 16px;
}
.medal-progress-row {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  font-size: 0.85rem;
  color: #6b5b40;
  margin-bottom: 8px;
  letter-spacing: 0.04em;
}
.medal-progress-value {
  font-family: 'SF Mono', ui-monospace, monospace;
  font-size: 0.95rem;
  font-weight: 600;
  color: #e58b1d;
}
.medal-progress-bar {
  height: 8px;
  border-radius: 4px;
  background: rgba(0, 0, 0, 0.06);
  overflow: hidden;
}
.medal-progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #ffd36a, #f5a524 70%, #ff7a50);
  transition: width 0.7s cubic-bezier(0.25, 1.5, 0.5, 1);
}

.medal-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 14px;
}
.medal-item {
  position: relative;
  text-align: center;
  padding: 22px 18px 18px;
  border-radius: 22px;
  overflow: hidden;
  border: 1px solid rgba(255, 255, 255, 0.7);
  background: rgba(255, 255, 255, 0.55);
}
.medal-item-locked {
  background: rgba(220, 215, 205, 0.5);
  filter: grayscale(0.6) saturate(0.65);
}
.medal-item-locked .medal-emoji {
  filter: grayscale(0.85);
  opacity: 0.55;
}
.medal-item-active {
  background: linear-gradient(135deg, rgba(255, 235, 174, 0.7), rgba(255, 200, 130, 0.7));
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.9),
    0 10px 32px rgba(245, 165, 36, 0.32);
  animation: medalIn 0.6s cubic-bezier(0.25, 1.5, 0.5, 1);
}
@keyframes medalIn {
  0%   { transform: scale(0.7); opacity: 0; }
  60%  { transform: scale(1.05); opacity: 1; }
  100% { transform: scale(1); }
}
.medal-glow {
  position: absolute;
  inset: 0;
  border-radius: inherit;
  background: radial-gradient(circle at 50% 35%, rgba(255, 215, 130, 0.6), transparent 65%);
  pointer-events: none;
  animation: medalGlow 2.4s ease-in-out infinite;
}
@keyframes medalGlow {
  0%, 100% { opacity: 0.7; transform: scale(1); }
  50%      { opacity: 1;   transform: scale(1.05); }
}
.medal-emoji {
  font-size: 2.6rem;
  line-height: 1;
}
.medal-name {
  margin: 8px 0 4px;
  font-size: 1.02rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  color: #2d2416;
}
.medal-tip {
  margin: 0;
  font-size: 0.82rem;
  color: #6b5b40;
}
.medal-modal-foot {
  display: flex;
  justify-content: center;
}

/* ============ 全局成就动画 ============ */
.achievement-overlay {
  position: fixed;
  inset: 0;
  z-index: 300;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(45, 36, 22, 0.35);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  pointer-events: none;
}
.achievement-card {
  position: relative;
  border-radius: 28px;
  padding: 32px 36px 28px;
  text-align: center;
  min-width: 320px;
  overflow: hidden;
  animation: achievementPop 0.6s cubic-bezier(0.25, 1.5, 0.5, 1);
}
@keyframes achievementPop {
  0%   { transform: scale(0.6) translateY(40px); opacity: 0; }
  60%  { transform: scale(1.06); opacity: 1; }
  100% { transform: scale(1); }
}
.achievement-medal {
  font-size: 3.2rem;
  line-height: 1;
  margin-bottom: 6px;
  filter: drop-shadow(0 6px 18px rgba(245, 165, 36, 0.45));
}
.achievement-tag {
  display: block;
  font-family: 'SF Mono', ui-monospace, monospace;
  font-size: 0.7rem;
  letter-spacing: 0.32em;
  color: #a07b3a;
  margin-bottom: 4px;
}
.achievement-title {
  margin: 0 0 6px;
  font-size: 1.4rem;
  font-weight: 800;
  letter-spacing: 0.16em;
  color: #2d2416;
}
.achievement-sub {
  margin: 0;
  color: #6b5b40;
  font-size: 0.92rem;
}
.achievement-confetti {
  position: absolute;
  inset: 0;
  overflow: hidden;
  pointer-events: none;
}
.achievement-confetti span {
  position: absolute;
  top: -10px;
  width: 8px;
  height: 14px;
  border-radius: 2px;
  opacity: 0.9;
  animation-name: confettiFall;
  animation-timing-function: cubic-bezier(0.25, 0.8, 0.5, 1);
  animation-iteration-count: infinite;
}
@keyframes confettiFall {
  0%   { transform: translateY(-20px) rotate(0deg);   opacity: 0; }
  10%  { opacity: 1; }
  100% { transform: translateY(280px) rotate(720deg); opacity: 0; }
}
</style>


