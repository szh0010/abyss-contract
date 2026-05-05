<template>
  <div class="game-page" :class="[dangerClass, stageThemeClass]">
    <!-- Glitch 故障转场层 -->
    <div class="glitch-overlay" v-if="showGlitch">
      <div class="glitch-bar glitch-bar-1"></div>
      <div class="glitch-bar glitch-bar-2"></div>
      <div class="glitch-bar glitch-bar-3"></div>
      <div class="glitch-text" data-text="SYSTEM ERROR">SYSTEM ERROR</div>
    </div>

    <!-- 呼吸灯边框（stage_trap 阶段） -->
    <div class="pressure-border" v-if="gameStage === 'stage_trap'"></div>

    <!-- 借款弹窗 -->
    <LoanDialog :visible="showLoanDialog" @accept="onAcceptLoan" />

    <!-- 终局冻结 -->
    <FrozenScreen :visible="showFrozenScreen" @restart="restartGame" />

    <!-- ========== 规则说明弹窗（首次进入扑克） ========== -->
    <transition name="rules-fade">
      <div v-if="showRules" class="rules-overlay" @click.self="closeRules">
        <div class="rules-box">
          <div class="rules-header">
            <span class="rules-icon">♠</span>
            <h2 class="rules-title">印第安扑克 · 规则速览</h2>
            <span class="rules-icon">♦</span>
          </div>

          <div class="rules-body">
            <div class="rule-item">
              <span class="rule-num">01</span>
              <div class="rule-content">
                <p class="rule-title">看得见对方，看不见自己</p>
                <p class="rule-desc">你和 K 各抽一张牌贴在额头上。你能看到 K 的牌，但看不到自己的。</p>
              </div>
            </div>

            <div class="rule-item">
              <span class="rule-num">02</span>
              <div class="rule-content">
                <p class="rule-title">1 最小，10 最大</p>
                <p class="rule-desc">牌面数字 1-10，摊牌后数字大的赢得底池。</p>
              </div>
            </div>

            <div class="rule-item">
              <span class="rule-num">03</span>
              <div class="rule-content">
                <p class="rule-title">三种操作</p>
                <p class="rule-desc">
                  <span class="op-tag op-call">跟 注</span> 不加钱，等对方决定 ·
                  <span class="op-tag op-raise">加 注</span> 加筹码施压对方 ·
                  <span class="op-tag op-fold">弃 牌</span> 放弃本局，输掉底池
                </p>
              </div>
            </div>

            <div class="rule-item">
              <span class="rule-num">04</span>
              <div class="rule-content">
                <p class="rule-title">开牌时机</p>
                <p class="rule-desc">一方选择<b>跟注</b>时立刻开牌比大小，弃牌则直接结算。</p>
              </div>
            </div>

            <div class="rule-tip">
              💡 核心：你只能通过<b class="tip-highlight">K 的牌大小</b>和<b class="tip-highlight">他的下注行为</b>推测自己的牌。
            </div>
          </div>

          <button class="rules-btn" @click="closeRules">
            明 白 了 · 开 始 游 戏
          </button>
        </div>
      </div>
    </transition>
    <!-- ========== VN MODE: 剧本对话 ========== -->
    <template v-if="mode === 'vn'">
      <header class="game-header">
        <h1 class="game-logo">深渊契约</h1>
        <div class="header-right">
          <span class="mental-badge" :style="{ color: mentalColor, borderColor: mentalColor }">{{ mentalState }}</span>
        </div>
      </header>

      <div class="status-board" v-if="currentNode && !currentNode.ending">
        <div class="stat-box">
          <span class="stat-label">债 务</span>
          <span class="stat-value debt-value">¥ {{ vnDebt.toLocaleString() }}</span>
        </div>
        <div class="stat-divider"></div>
        <div class="stat-box">
          <span class="stat-label">贪 婪 值</span>
          <div class="greed-track">
            <div class="greed-fill" :style="{ width: greed + '%' }"></div>
          </div>
          <span class="stat-value greed-value">{{ greed }} / 100</span>
        </div>
      </div>

      <div class="vn-main">
        <div class="dialogue-box">
          <div class="speaker-row" v-if="currentNode">
            <div class="speaker-avatar" :class="currentNode.speaker">
              {{ currentNode.speaker === 'K' ? 'K' : (currentNode.speaker === 'narrator' ? '▪' : '?') }}
            </div>
            <span class="speaker-name">
              {{ currentNode.speaker === 'K' ? '代理人 K' : (currentNode.speaker === 'narrator' ? '旁白' : currentNode.speaker) }}
            </span>
          </div>
          <div class="dialogue-text" v-if="currentNode" v-html="formatText(displayedText)"></div>
        </div>

        <div class="choices-area" v-if="typingDone && currentNode && currentNode.choices && currentNode.choices.length > 0 && !currentNode.ending">
          <button v-for="(choice, idx) in currentNode.choices" :key="idx"
                  class="choice-btn" :class="'choice-' + idx"
                  @click="pickChoice(choice)">
            <span class="choice-idx">{{ idx + 1 }}</span>
            <span class="choice-text">{{ choice.text }}</span>
          </button>
        </div>

        <div v-if="currentNode && currentNode.ending" class="ending-box" :class="'ending-' + currentNode.ending">
          <h2 class="ending-title">{{ currentNode.ending_title }}</h2>
          <p class="ending-message" v-html="formatText(currentNode.ending_message || '')"></p>
          <button class="restart-btn" @click="restartGame">重新开始</button>
        </div>
      </div>
    </template>

    <!-- ========== POKER MODE: 印第安扑克 ========== -->
    <template v-if="mode === 'poker'">
      <header class="game-header poker-header">
        <h1 class="game-logo">{{ stageTitle || '印第安扑克' }}</h1>
        <div class="header-right-poker">
          <span class="stage-badge" :class="'badge-' + gameStage">{{ stageShortName }}</span>
          <span class="round-badge">第 {{ pokerRound }} 局</span>
        </div>
      </header>

      <!-- 阶段提示条 -->
      <div class="stage-hint-bar" v-if="stageHint" :class="'hint-' + gameStage">
        {{ stageHint }}
      </div>

      <div class="poker-board">
        <div class="poker-status">
          <div class="chips-box player-chips-box">
            <span class="chips-label">你的筹码</span>
            <span class="chips-value player-color">¥{{ playerChips.toLocaleString() }}</span>
            <!-- 负债显示（CONTRACT 阶段后出现） -->
            <span class="debt-display" v-if="debt > 0">
              负债: -¥{{ debt.toLocaleString() }}
            </span>
          </div>
          <div class="pot-box">
            <span class="pot-label">底 池</span>
            <span class="pot-value">¥{{ pot.toLocaleString() }}</span>
          </div>
          <div class="chips-box k-chips-box">
            <span class="chips-label">K 的筹码</span>
            <span class="chips-value k-color">¥{{ kChips.toLocaleString() }}</span>
          </div>
        </div>

        <div class="cards-area">
          <div class="card-slot player-card-slot">
            <div class="card card-hidden">
              <span class="card-label">你的牌</span>
              <span class="card-number">?</span>
              <span class="card-hint">（你看不到）</span>
            </div>
          </div>
          <div class="vs-badge">VS</div>
          <div class="card-slot k-card-slot">
            <div class="card card-visible">
              <span class="card-label">K 的牌</span>
              <span class="card-number k-number">{{ kCard }}</span>
              <span class="card-hint">（你能看到）</span>
            </div>
          </div>
        </div>

        <div class="k-taunt" v-if="kTaunt">
          <div class="taunt-avatar">K</div>
          <div class="taunt-bubble">{{ kTaunt }}</div>
        </div>

        <div class="action-log" v-if="actionLog.length > 0">
          <div v-for="(log, i) in actionLog" :key="i" class="log-entry" :class="log.role">
            {{ log.text }}
          </div>
        </div>

        <div class="poker-actions" v-if="!pokerRoundOver && !pokerLoading && pokerStarted">
          <button class="poker-btn fold-btn" @click="pokerAction('fold')">弃 牌</button>
          <button class="poker-btn call-btn" @click="pokerAction('call')" :disabled="playerChips <= 0">跟 注</button>
          <div class="raise-group">
            <input type="number" v-model.number="raiseAmount" min="1000" :max="maxRaise" step="1000" class="raise-input" :disabled="playerChips <= 0"/>
            <button class="poker-btn raise-btn" @click="pokerAction('raise')" :disabled="raiseAmount < 1000 || playerChips <= 0 || raiseAmount > maxRaise">加 注</button>
          </div>
          <span class="chips-warn" v-if="playerChips <= 2000">⚠ 筹码即将耗尽</span>
        </div>

        <div class="poker-actions" v-if="!pokerStarted && !pokerLoading">
          <button class="poker-btn deal-btn" @click="dealCards">发 牌</button>
        </div>

        <div v-if="pokerLoading" class="poker-loading">
          <div class="typing-dots"><span></span><span></span><span></span></div>
          <span>K 正在思考...</span>
        </div>

        <div class="round-result" v-if="pokerRoundOver">
          <div class="result-card" :class="'result-' + roundWinner">
            <template v-if="roundWinner === 'player'">
              <h3>你赢了这局！</h3>
              <p>你的牌: {{ playerCard }} &nbsp;vs&nbsp; K的牌: {{ kCard }}</p>
            </template>
            <template v-else-if="roundWinner === 'k'">
              <h3>K 赢了这局</h3>
              <p>你的牌: {{ playerCard }} &nbsp;vs&nbsp; K的牌: {{ kCard }}</p>
            </template>
            <template v-else-if="roundWinner === 'draw'">
              <h3>平局</h3>
              <p>双方牌面相同</p>
            </template>
            <template v-else>
              <h3>{{ roundWinner === 'k' ? 'K 赢了' : '你弃牌了' }}</h3>
            </template>
            <button class="poker-btn next-round-btn" v-if="!pokerGameOver" @click="nextRound">下一局</button>
            <button class="poker-btn next-round-btn" v-else @click="endPokerGame">结算</button>
          </div>
        </div>
      </div>
    </template>

    <footer class="game-footer">
      <p>反赌博教育作品 | 报警 110 | 法律援助 12348 | 反诈热线 96110</p>
    </footer>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import storyData from '../data/story.json'
import LoanDialog from '../components/LoanDialog.vue'
import FrozenScreen from '../components/FrozenScreen.vue'

const router = useRouter()

// ===== 模式控制 =====
const mode = ref('poker')  // 直接进入扑克模式测试新架构

// ===== 状态机核心变量 =====
const gameStage = ref('stage_bait')
const stageTitle = ref('序曲：新手福利')
const stageHint = ref('前3局必赢，体验赚钱的快感！')
const baitWins = ref(0)
const hookRounds = ref(0)
const debt = ref(0)
const loanAccepted = ref(false)
const showLoanDialog = ref(false)
const showFrozenScreen = ref(false)
const showGlitch = ref(false)
const showRules = ref(true)  // 首次进入显示规则

function closeRules() {
  showRules.value = false
}

const stageShortName = computed(() => {
  const m = {
    stage_bait: '序曲',
    stage_hook: '第一幕',
    stage_trap: '第二幕',
    stage_contract: '第三幕',
    stage_verdict: '终局',
  }
  return m[gameStage.value] || ''
})

const stageThemeClass = computed(() => `theme-${gameStage.value}`)

// ===== VN 状态 =====
const vnDebt = ref(500000)
const greed = ref(0)
const currentNodeId = ref(storyData.meta.initial_node)
const currentNode = computed(() => storyData.nodes[currentNodeId.value] || null)
const displayedText = ref('')
const typingDone = ref(false)
let typingTimer = null

const mentalState = computed(() => {
  if (greed.value < 25) return '清醒'
  if (greed.value < 50) return '动摇'
  if (greed.value < 80) return '迷失'
  return '失控'
})

const mentalColor = computed(() => {
  const m = { '清醒': '#27ae60', '动摇': '#f39c12', '迷失': '#e67e22', '失控': '#e74c3c' }
  return m[mentalState.value] || '#888'
})

const dangerClass = computed(() => {
  if (greed.value >= 80) return 'danger-critical'
  if (greed.value >= 50) return 'danger-high'
  return ''
})

function formatText(text) {
  if (!text) return ''
  return text.replace(/\n/g, '<br>').replace(/（([^）]+)）/g, '<em class="action">（$1）</em>')
}

function startTyping(text) {
  displayedText.value = ''
  typingDone.value = false
  let i = 0
  if (typingTimer) clearInterval(typingTimer)
  typingTimer = setInterval(() => {
    if (i < text.length) {
      displayedText.value += text[i]
      i++
    } else {
      clearInterval(typingTimer)
      typingDone.value = true
    }
  }, 30)
}

watch(currentNodeId, () => {
  const node = currentNode.value
  if (node && node.text) {
    startTyping(node.text)
  }
  // 检查是否进入扑克模式
  if (node && node.flag === 'enter_poker') {
    // 会在选项被点击时处理
  }
}, { immediate: true })

function pickChoice(choice) {
  // 贪婪值变化
  if (choice.greed_change) {
    greed.value = Math.max(0, Math.min(100, greed.value + choice.greed_change))
  }

  // 检查是否触发扑克
  if (choice.flag === 'start_poker') {
    mode.value = 'poker'
    initPoker()
    return
  }

  // 检查是否是结局
  if (choice.flag === 'ending') {
    currentNodeId.value = choice.next
    return
  }

  // 正常跳转
  if (choice.next === 'POKER_MODE') {
    mode.value = 'poker'
    initPoker()
    return
  }

  currentNodeId.value = choice.next
}

// ===== POKER 状态 =====
const pokerRound = ref(0)
const playerChips = ref(50000)
const kChips = ref(50000)
const pot = ref(0)
const playerCard = ref(0)
const kCard = ref(0)
const kTaunt = ref('')
const raiseAmount = ref(2000)
const pokerStarted = ref(false)
const pokerRoundOver = ref(false)
const pokerLoading = ref(false)
const pokerGameOver = ref(false)
const roundWinner = ref('')
const actionLog = ref([])

const maxRaise = computed(() => Math.max(0, Math.min(playerChips.value, kChips.value)))

function initPoker() {
  pokerRound.value = 0
  playerChips.value = 10000  // stage_bait 初始筹码
  kChips.value = 50000
  pot.value = 0
  playerCard.value = 0
  kCard.value = 0
  kTaunt.value = '（K在远处看着你，嘴角微扬）先从小的玩起，热热身。'
  pokerStarted.value = false
  pokerRoundOver.value = false
  pokerGameOver.value = false
  actionLog.value = []
  // 状态机重置
  gameStage.value = 'stage_bait'
  stageTitle.value = '序曲：新手福利'
  stageHint.value = '前3局必赢，体验赚钱的快感！'
  baitWins.value = 0
  hookRounds.value = 0
  debt.value = 0
  loanAccepted.value = false
  showLoanDialog.value = false
  showFrozenScreen.value = false
}

async function dealCards() {
  pokerLoading.value = true
  pokerRoundOver.value = false
  roundWinner.value = ''
  actionLog.value = []
  kTaunt.value = ''

  try {
    const res = await fetch('/api/minigame/start', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        player_chips: playerChips.value,
        k_chips: kChips.value,
        game_stage: gameStage.value,
        bait_wins: baitWins.value,
        hook_rounds: hookRounds.value,
      })
    })

    if (!res.ok) {
      // 后端拒绝发牌（通常是筹码耗尽）
      const errData = await res.json().catch(() => ({}))
      console.warn('[发牌被拒]', errData)
      // 如果玩家筹码为 0 且在 trap 或更后的阶段，触发套路贷
      if (playerChips.value <= 0 && (gameStage.value === 'stage_trap' || gameStage.value === 'stage_hook')) {
        gameStage.value = 'stage_contract'
        stageTitle.value = '第三幕：最后的机会'
        stageHint.value = '接受借款，翻本在此一举'
        showLoanDialog.value = true
        pokerLoading.value = false
        return
      }
      kTaunt.value = '（K 冷笑）你连发牌的筹码都没有了。'
      pokerLoading.value = false
      return
    }

    const data = await res.json()

    pokerRound.value++
    playerCard.value = data.player_card
    kCard.value = data.k_card
    pot.value = data.pot
    playerChips.value = data.player_chips ?? playerChips.value
    kChips.value = data.k_chips ?? kChips.value
    pokerStarted.value = true
    kTaunt.value = '牌已发出。看看我头上是什么？'
    // 同步阶段信息
    if (data.game_stage) gameStage.value = data.game_stage
    if (data.stage_title) stageTitle.value = data.stage_title
    if (data.stage_hint) stageHint.value = data.stage_hint
    actionLog.value.push({ role: 'system', text: `第 ${pokerRound.value} 局开始 | 底注各 ${data.ante} | 底池 ${data.pot}` })
  } catch (e) {
    console.error(e)
    kTaunt.value = '（系统错误——牌局连接中断）'
  } finally {
    pokerLoading.value = false
  }
}

async function pokerAction(action) {
  pokerLoading.value = true

  // 限制下注不超过玩家筹码
  let bet = 0
  if (action === 'raise') {
    bet = Math.max(1000, Math.min(raiseAmount.value, playerChips.value, kChips.value))
    if (bet > playerChips.value || playerChips.value < 1000) {
      pokerLoading.value = false
      kTaunt.value = '你的筹码不够加注了。'
      return
    }
  }

  // 筹码不足时强制拒绝操作（双重保险）
  if ((action === 'call' || action === 'raise') && playerChips.value <= 0) {
    pokerLoading.value = false
    kTaunt.value = '你已经没有筹码了。'
    return
  }

  if (action === 'fold') {
    actionLog.value.push({ role: 'player', text: '你弃牌了' })
  } else if (action === 'raise') {
    actionLog.value.push({ role: 'player', text: `你加注 ¥${bet.toLocaleString()}` })
  } else if (action === 'call') {
    actionLog.value.push({ role: 'player', text: '你跟注' })
  }

  try {
    const res = await fetch('/api/minigame/action', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        round_id: pokerRound.value,
        player_card: playerCard.value,
        k_card: kCard.value,
        pot: pot.value,
        player_chips: playerChips.value,
        k_chips: kChips.value,
        player_action: action,
        player_bet: bet,
        round_history: actionLog.value.map(l => l.text),
        game_stage: gameStage.value,
        bait_wins: baitWins.value,
        hook_rounds: hookRounds.value,
        loan_accepted: loanAccepted.value,
      })
    })
    const data = await res.json()

    kTaunt.value = data.taunt
    pot.value = data.new_pot
    playerChips.value = data.player_chips
    kChips.value = data.k_chips

    // ===== 状态机字段同步 =====
    if (data.bait_wins !== undefined) baitWins.value = data.bait_wins
    if (data.hook_rounds !== undefined) hookRounds.value = data.hook_rounds

    // ===== 阶段流转处理 =====
    if (data.stage_changed && data.game_stage !== gameStage.value) {
      const oldStage = gameStage.value
      const newStage = data.game_stage

      // 进入 stage_hook：触发 Glitch 故障特效
      if (newStage === 'stage_hook') {
        await triggerGlitchTransition()
      }

      gameStage.value = newStage
      if (data.stage_title) stageTitle.value = data.stage_title
      if (data.stage_hint) stageHint.value = data.stage_hint

      // 进入 stage_contract：弹出借款协议
      if (newStage === 'stage_contract') {
        await nextTick()
        setTimeout(() => {
          showLoanDialog.value = true
        }, 800)
      }
    }

    if (data.k_action === 'RAISE' || data.k_action === 'raise') {
      actionLog.value.push({ role: 'k', text: `K 加注 ¥${data.k_bet.toLocaleString()}` })
    } else if (data.k_action === 'CALL' || data.k_action === 'call') {
      actionLog.value.push({ role: 'k', text: 'K 跟注' })
    } else if (data.k_action === 'FOLD' || data.k_action === 'fold') {
      actionLog.value.push({ role: 'k', text: 'K 弃牌' })
    } else if (data.k_action === 'WIN' || data.k_action === 'win') {
      actionLog.value.push({ role: 'k', text: 'K 获胜（你弃牌）' })
    }

    if (data.round_over) {
      pokerRoundOver.value = true
      roundWinner.value = data.winner
      pokerStarted.value = false
    }

    // 破产判定（后端返回的 game_over 字段）
    if (data.game_over) {
      pokerGameOver.value = true
      pokerRoundOver.value = true
      pokerStarted.value = false
      // 筹码强制归零显示
      if (data.game_over_reason === 'player_bankrupt') {
        playerChips.value = 0
      } else if (data.game_over_reason === 'k_bankrupt') {
        kChips.value = 0
      }
      // ===== 终局冻结：账户冻结（stage_verdict） =====
      if (data.game_over_reason === 'account_frozen') {
        setTimeout(() => {
          showFrozenScreen.value = true
        }, 1200)
      }
    }
  } catch (e) {
    console.error(e)
    kTaunt.value = '（连接中断了……）'
  } finally {
    pokerLoading.value = false
  }
}

function nextRound() {
  pokerRoundOver.value = false
  roundWinner.value = ''
  pokerStarted.value = false
  kTaunt.value = '下一局。'
  actionLog.value = []
}

function endPokerGame() {
  mode.value = 'vn'
  if (kChips.value <= 0) {
    currentNodeId.value = 'poker_end_win'
  } else {
    currentNodeId.value = 'poker_end_lose'
  }
}

function restartGame() {
  router.push('/')
}

// ===== Glitch 故障转场 =====
function triggerGlitchTransition() {
  return new Promise((resolve) => {
    showGlitch.value = true
    setTimeout(() => {
      showGlitch.value = false
      resolve()
    }, 1600)
  })
}

// ===== 接受借款协议 =====
function onAcceptLoan() {
  loanAccepted.value = true
  showLoanDialog.value = false
  playerChips.value = 100000
  debt.value = 100000
  kTaunt.value = '（K露出诡异的笑容）好孩子。现在，我们继续玩。'
  pokerRoundOver.value = false
  pokerGameOver.value = false
  actionLog.value.push({ role: 'system', text: '✓ 借款协议已签订 | 到账 ¥100,000 | 负债 ¥100,000' })
}

onMounted(() => {
  const name = sessionStorage.getItem('abyss_player_name') || '无名者'
  initPoker()
})
</script>

<style scoped>
/* ======== 全局容器 ======== */
.game-page {
  width: 100%;
  max-width: 800px;
  height: 100vh;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  background: #050508;
  color: #e0e0e0;
  font-family: 'Noto Serif SC', 'SimSun', serif;
  position: relative;
  overflow: hidden;
}
.game-page.danger-high { background: linear-gradient(180deg, #050508, #0a0508); }
.game-page.danger-critical { background: linear-gradient(180deg, #080205, #0d0408); animation: dangerPulse 4s ease-in-out infinite; }
@keyframes dangerPulse {
  0%,100% { box-shadow: inset 0 0 60px rgba(139,0,0,0.05); }
  50% { box-shadow: inset 0 0 100px rgba(139,0,0,0.15); }
}

/* ======== Header ======== */
.game-header { display:flex; justify-content:space-between; align-items:center; padding:12px 20px; border-bottom:1px solid rgba(139,0,0,0.2); background:rgba(5,5,8,0.95); z-index:10; flex-shrink:0; }
.game-logo { font-size:1.1rem; color:#8b0000; letter-spacing:0.4rem; font-weight:700; margin:0; text-shadow:0 0 10px rgba(139,0,0,0.3); }
.mental-badge { font-size:0.75rem; padding:3px 12px; border:1px solid; letter-spacing:0.15rem; }
.round-badge { font-size:0.8rem; color:#d4af37; border:1px solid rgba(212,175,55,0.3); padding:3px 12px; }

/* ======== Status Board ======== */
.status-board { display:flex; align-items:center; padding:12px 20px; background:rgba(12,12,18,0.9); border-bottom:1px solid rgba(40,40,60,0.3); gap:20px; flex-shrink:0; }
.stat-box { flex:1; display:flex; flex-direction:column; gap:4px; }
.stat-divider { width:1px; height:36px; background:rgba(60,60,80,0.3); }
.stat-label { font-size:0.65rem; color:#555; letter-spacing:0.3rem; }
.stat-value { font-family:'Courier New',monospace; font-weight:700; }
.debt-value { font-size:1.2rem; color:#ff3333; }
.greed-value { font-size:0.85rem; color:#d4af37; }
.greed-track { width:100%; height:4px; background:#1a1a25; border-radius:2px; overflow:hidden; }
.greed-fill { height:100%; background:linear-gradient(90deg,#d4af37,#ff3333); border-radius:2px; transition:width 0.8s; }

/* ======== VN Main ======== */
.vn-main { flex:1; display:flex; flex-direction:column; overflow-y:auto; padding:20px; gap:20px; }
.dialogue-box { background:linear-gradient(135deg,rgba(30,5,5,0.6),rgba(15,5,5,0.4)); border:1px solid rgba(139,0,0,0.2); border-radius:4px; padding:0; }
.speaker-row { display:flex; align-items:center; gap:10px; padding:12px 18px; border-bottom:1px solid rgba(139,0,0,0.15); }
.speaker-avatar { width:32px; height:32px; border-radius:4px; display:flex; align-items:center; justify-content:center; font-weight:700; font-size:0.85rem; }
.speaker-avatar.K { background:linear-gradient(135deg,#1a0000,#330000); color:#ff4c4c; border:1px solid rgba(139,0,0,0.5); }
.speaker-avatar.narrator { background:#1a1a22; color:#888; border:1px solid #333; }
.speaker-name { font-size:0.9rem; color:#ccc; font-weight:700; }
.dialogue-text { padding:20px; font-size:0.95rem; line-height:2; color:#d4c4c4; min-height:120px; }
.dialogue-text :deep(.action) { color:#777; font-style:italic; font-size:0.9em; }

/* ======== Choices ======== */
.choices-area { display:flex; flex-direction:column; gap:10px; animation:fadeIn 0.5s ease; }
.choice-btn { display:flex; align-items:center; gap:14px; width:100%; padding:14px 18px; background:rgba(15,15,22,0.8); border:1px solid rgba(60,60,80,0.3); color:#ccc; font-size:0.92rem; font-family:inherit; text-align:left; cursor:pointer; transition:all 0.3s; border-radius:3px; line-height:1.6; }
.choice-btn:hover { transform:translateX(4px); border-color:rgba(139,0,0,0.5); background:rgba(25,10,10,0.8); }
.choice-idx { width:26px; height:26px; display:flex; align-items:center; justify-content:center; font-weight:700; font-size:0.8rem; border-radius:3px; flex-shrink:0; background:rgba(139,0,0,0.15); color:#ff4c4c; border:1px solid rgba(139,0,0,0.3); }
.choice-text { flex:1; }
@keyframes fadeIn { from{opacity:0;transform:translateY(10px)} to{opacity:1;transform:translateY(0)} }

/* ======== Ending ======== */
.ending-box { text-align:center; padding:3rem 2rem; animation:fadeIn 1s ease; }
.ending-box.ending-good_early,.ending-box.ending-good { border:1px solid rgba(39,174,96,0.3); background:rgba(0,30,15,0.3); border-radius:4px; }
.ending-box.ending-good_early .ending-title,.ending-box.ending-good .ending-title { color:#4cff88; text-shadow:0 0 20px rgba(76,255,136,0.4); }
.ending-box.ending-bad { border:1px solid rgba(139,0,0,0.3); background:rgba(30,0,0,0.3); border-radius:4px; }
.ending-box.ending-bad .ending-title { color:#ff3333; text-shadow:0 0 20px rgba(255,51,51,0.4); }
.ending-title { font-size:1.6rem; letter-spacing:0.3rem; margin-bottom:1.5rem; }
.ending-message { font-size:0.9rem; color:#999; line-height:2; margin-bottom:2rem; text-align:left; }
.restart-btn { padding:12px 40px; background:transparent; border:1px solid #555; color:#999; font-size:0.9rem; font-family:inherit; letter-spacing:0.3rem; cursor:pointer; transition:all 0.3s; }
.restart-btn:hover { color:#fff; border-color:#999; }

/* ======== POKER ======== */
.poker-board { flex:1; display:flex; flex-direction:column; padding:16px 20px; gap:16px; overflow-y:auto; }
.poker-status { display:flex; justify-content:space-between; align-items:center; gap:10px; }
.chips-box { flex:1; display:flex; flex-direction:column; align-items:center; gap:4px; padding:10px; background:rgba(12,12,18,0.8); border:1px solid rgba(40,40,60,0.3); border-radius:4px; }
.chips-label { font-size:0.65rem; color:#666; letter-spacing:0.2rem; }
.chips-value { font-family:'Courier New',monospace; font-size:1.1rem; font-weight:700; }
.player-color { color:#4caf50; }
.k-color { color:#ff4c4c; }
.pot-box { display:flex; flex-direction:column; align-items:center; gap:4px; padding:12px 20px; background:linear-gradient(135deg,rgba(50,40,0,0.4),rgba(30,20,0,0.3)); border:1px solid rgba(212,175,55,0.3); border-radius:4px; }
.pot-label { font-size:0.65rem; color:#d4af37; letter-spacing:0.3rem; }
.pot-value { font-family:'Courier New',monospace; font-size:1.3rem; font-weight:700; color:#d4af37; text-shadow:0 0 8px rgba(212,175,55,0.3); }

/* Cards */
.cards-area { display:flex; align-items:center; justify-content:center; gap:24px; padding:20px 0; }
.card-slot { flex:1; max-width:160px; }
.card { display:flex; flex-direction:column; align-items:center; justify-content:center; padding:20px 10px; border-radius:8px; min-height:140px; }
.card-hidden { background:linear-gradient(135deg,#1a1a25,#12121e); border:2px solid #333; box-shadow:inset 0 0 20px rgba(0,0,0,0.5); }
.card-visible { background:linear-gradient(135deg,rgba(30,5,5,0.8),rgba(20,0,0,0.6)); border:2px solid rgba(139,0,0,0.4); box-shadow:0 0 15px rgba(139,0,0,0.15); }
.card-label { font-size:0.7rem; color:#666; letter-spacing:0.15rem; margin-bottom:8px; }
.card-number { font-family:'Courier New',monospace; font-size:2.5rem; font-weight:700; color:#888; }
.card-number.k-number { color:#ff4c4c; text-shadow:0 0 10px rgba(255,76,76,0.3); }
.card-hint { font-size:0.65rem; color:#555; margin-top:6px; }
.vs-badge { font-size:1rem; color:#555; font-weight:700; letter-spacing:0.2rem; }

/* K Taunt */
.k-taunt { display:flex; align-items:flex-start; gap:12px; padding:12px 16px; background:linear-gradient(135deg,rgba(30,5,5,0.5),rgba(15,5,5,0.3)); border:1px solid rgba(139,0,0,0.2); border-radius:4px; animation:fadeIn 0.4s ease; }
.taunt-avatar { width:28px; height:28px; border-radius:4px; background:linear-gradient(135deg,#1a0000,#330000); color:#ff4c4c; display:flex; align-items:center; justify-content:center; font-weight:700; font-size:0.75rem; flex-shrink:0; border:1px solid rgba(139,0,0,0.4); }
.taunt-bubble { font-size:0.9rem; color:#e8cccc; line-height:1.6; }

/* Action Log */
.action-log { display:flex; flex-direction:column; gap:4px; padding:8px 12px; background:rgba(10,10,15,0.5); border:1px solid rgba(40,40,60,0.2); border-radius:4px; max-height:100px; overflow-y:auto; font-size:0.8rem; }
.log-entry { padding:2px 0; }
.log-entry.system { color:#555; }
.log-entry.player { color:#4caf50; }
.log-entry.k { color:#ff4c4c; }

/* Poker Actions */
.poker-actions { display:flex; gap:10px; align-items:center; justify-content:center; flex-wrap:wrap; padding:10px 0; }
.poker-btn { padding:12px 24px; font-family:inherit; font-size:0.9rem; letter-spacing:0.2rem; border-radius:3px; cursor:pointer; transition:all 0.3s; border:1px solid; }
.fold-btn { background:transparent; border-color:#555; color:#888; }
.fold-btn:hover { border-color:#999; color:#ccc; }
.call-btn { background:rgba(39,174,96,0.15); border-color:rgba(39,174,96,0.4); color:#4caf50; }
.call-btn:hover { background:rgba(39,174,96,0.25); box-shadow:0 0 10px rgba(39,174,96,0.2); }
.raise-btn { background:linear-gradient(180deg,#8b0000,#4a0000); border-color:rgba(255,76,76,0.3); color:#fff; }
.raise-btn:hover:not(:disabled) { box-shadow:0 0 12px rgba(139,0,0,0.3); }
.raise-btn:disabled { opacity:0.5; cursor:not-allowed; }
.deal-btn { background:linear-gradient(180deg,rgba(212,175,55,0.3),rgba(150,120,30,0.2)); border-color:rgba(212,175,55,0.4); color:#d4af37; padding:14px 40px; font-size:1rem; }
.deal-btn:hover { box-shadow:0 0 15px rgba(212,175,55,0.2); }
.next-round-btn { margin-top:12px; background:transparent; border-color:#555; color:#ccc; }
.raise-group { display:flex; gap:6px; align-items:center; }
.raise-input { width:90px; padding:10px 8px; background:rgba(15,15,22,0.9); border:1px solid #333; border-radius:3px; color:#d4af37; font-family:'Courier New',monospace; font-size:0.9rem; text-align:center; }
.raise-input:focus { border-color:rgba(139,0,0,0.5); outline:none; }

/* Loading */
.poker-loading { display:flex; align-items:center; justify-content:center; gap:10px; padding:16px; color:#888; font-size:0.85rem; }
.typing-dots { display:flex; gap:4px; }
.typing-dots span { width:5px; height:5px; border-radius:50%; background:#ff4c4c; animation:dotBounce 1.4s ease-in-out infinite; }
.typing-dots span:nth-child(2) { animation-delay:0.2s; }
.typing-dots span:nth-child(3) { animation-delay:0.4s; }
@keyframes dotBounce { 0%,80%,100%{transform:translateY(0);opacity:0.3} 40%{transform:translateY(-6px);opacity:1} }

/* Round Result */
.round-result { display:flex; justify-content:center; padding:10px 0; }
.result-card { text-align:center; padding:20px 30px; border-radius:4px; animation:fadeIn 0.6s ease; }
.result-card h3 { font-size:1.1rem; margin-bottom:8px; letter-spacing:0.2rem; }
.result-card p { font-size:0.85rem; color:#999; }
.result-player { border:1px solid rgba(39,174,96,0.3); background:rgba(0,30,15,0.3); }
.result-player h3 { color:#4cff88; }
.result-k { border:1px solid rgba(139,0,0,0.3); background:rgba(30,0,0,0.3); }
.result-k h3 { color:#ff4c4c; }
.result-draw { border:1px solid rgba(212,175,55,0.3); background:rgba(30,25,0,0.3); }
.result-draw h3 { color:#d4af37; }

/* ======== Footer ======== */
.game-footer { text-align:center; padding:8px 0; background:rgba(5,5,8,0.95); border-top:1px solid rgba(40,40,60,0.2); flex-shrink:0; }
.game-footer p { font-size:0.65rem; color:#ff4c4c; opacity:0.5; margin:0; }

/* ========================================================
   ★★★ 状态机主题切换 ★★★
   ======================================================== */

/* 阶段短名称徽章 */
.header-right-poker { display:flex; align-items:center; gap:10px; }
.stage-badge {
  font-size:0.7rem;
  padding:3px 10px;
  letter-spacing:0.2rem;
  border:1px solid;
  font-family:'Courier New', monospace;
}
.badge-stage_bait { color:#ffd700; border-color:#8b6914; background:rgba(139,105,20,0.15); }
.badge-stage_hook { color:#ff4c4c; border-color:#8b0000; background:rgba(139,0,0,0.15); }
.badge-stage_trap { color:#ff3333; border-color:#ff3333; background:rgba(139,0,0,0.3); animation:badgeWarn 1.2s ease-in-out infinite; }
.badge-stage_contract { color:#ffd700; border-color:#ffd700; background:rgba(139,0,0,0.3); }
.badge-stage_verdict { color:#888; border-color:#333; background:#000; }

@keyframes badgeWarn {
  0%,100% { box-shadow:0 0 5px rgba(255,51,51,0.3); }
  50% { box-shadow:0 0 15px rgba(255,51,51,0.8); }
}

/* 阶段提示条 */
.stage-hint-bar {
  padding:8px 20px;
  font-size:0.8rem;
  letter-spacing:0.15rem;
  text-align:center;
  border-bottom:1px solid;
  flex-shrink:0;
}
.hint-stage_bait { background:linear-gradient(90deg, rgba(50,40,0,0.3), rgba(80,60,0,0.5), rgba(50,40,0,0.3)); color:#ffd700; border-bottom-color:rgba(212,175,55,0.3); }
.hint-stage_hook { background:linear-gradient(90deg, rgba(30,0,0,0.6), rgba(60,0,0,0.8), rgba(30,0,0,0.6)); color:#ff9999; border-bottom-color:rgba(139,0,0,0.4); }
.hint-stage_trap { background:linear-gradient(90deg, rgba(60,0,0,0.6), rgba(100,0,0,0.9), rgba(60,0,0,0.6)); color:#ff3333; border-bottom-color:#ff3333; font-weight:700; animation:trapHintPulse 1.5s ease-in-out infinite; }
.hint-stage_contract { background:linear-gradient(90deg, rgba(60,40,0,0.5), rgba(100,70,0,0.7), rgba(60,40,0,0.5)); color:#ffd700; border-bottom-color:#d4af37; }
.hint-stage_verdict { background:#000; color:#666; border-bottom-color:#333; }

@keyframes trapHintPulse {
  0%,100% { opacity:1; }
  50% { opacity:0.7; }
}

/* ======== 负债显示 ======== */
.debt-display {
  display:block;
  font-size:0.8rem;
  color:#ff3333;
  font-family:'Courier New',monospace;
  margin-top:4px;
  animation:debtBlink 1.4s ease-in-out infinite;
  text-shadow:0 0 10px rgba(255,51,51,0.6);
  letter-spacing:0.1rem;
}
@keyframes debtBlink {
  0%,100% { opacity:1; text-shadow:0 0 10px rgba(255,51,51,0.6); }
  50% { opacity:0.5; text-shadow:0 0 20px rgba(255,51,51,1); }
}

/* ========================================================
   ★★★ 阶段主题色 ★★★
   ======================================================== */

/* stage_bait: 金碧辉煌 */
.game-page.theme-stage_bait {
  background:linear-gradient(180deg, #0a0805 0%, #1a1405 50%, #0a0805 100%);
}
.game-page.theme-stage_bait::before {
  content:'';
  position:absolute;
  inset:0;
  background:radial-gradient(ellipse at top, rgba(212,175,55,0.08), transparent 60%);
  pointer-events:none;
  z-index:0;
}
.theme-stage_bait .game-logo { color:#ffd700 !important; text-shadow:0 0 15px rgba(255,215,0,0.5) !important; }

/* stage_hook: 暗黑猩红 */
.game-page.theme-stage_hook {
  background:linear-gradient(180deg, #050000 0%, #150000 50%, #050000 100%);
}
.theme-stage_hook .game-logo { color:#ff3333 !important; text-shadow:0 0 20px rgba(255,51,51,0.6) !important; }

/* stage_trap: 警告红 + 呼吸灯（见下方） */
.game-page.theme-stage_trap {
  background:linear-gradient(180deg, #080000 0%, #200000 50%, #080000 100%);
}
.theme-stage_trap .game-logo { color:#ff0000 !important; text-shadow:0 0 25px rgba(255,0,0,0.8) !important; animation:logoShake 0.3s ease-in-out infinite; }

@keyframes logoShake {
  0%,100% { transform:translateX(0); }
  25% { transform:translateX(-1px); }
  75% { transform:translateX(1px); }
}

/* stage_contract: 金色诱惑 */
.game-page.theme-stage_contract {
  background:linear-gradient(180deg, #0a0805 0%, #1a0f00 50%, #0a0805 100%);
}

/* stage_verdict: 冷色冻结 */
.game-page.theme-stage_verdict {
  background:#000 !important;
  filter:grayscale(100%);
  pointer-events:none;
}

/* ========================================================
   ★★★ 呼吸灯边框（stage_trap）★★★
   ======================================================== */
.pressure-border {
  position:fixed;
  inset:0;
  pointer-events:none;
  z-index:200;
  box-shadow:
    inset 0 0 60px rgba(139,0,0,0.6),
    inset 0 0 120px rgba(255,0,0,0.3);
  animation:pressurePulse 2s ease-in-out infinite;
}
@keyframes pressurePulse {
  0%,100% {
    box-shadow:
      inset 0 0 40px rgba(139,0,0,0.4),
      inset 0 0 100px rgba(255,0,0,0.2);
  }
  50% {
    box-shadow:
      inset 0 0 100px rgba(255,0,0,0.9),
      inset 0 0 200px rgba(255,0,0,0.5);
  }
}

.pressure-border::before,
.pressure-border::after {
  content:'';
  position:absolute;
  left:0;
  right:0;
  height:4px;
  background:linear-gradient(90deg, transparent, #ff0000, transparent);
  animation:scanBar 3s linear infinite;
}
.pressure-border::before { top:0; }
.pressure-border::after { bottom:0; animation-delay:1.5s; }

@keyframes scanBar {
  0% { opacity:0; transform:scaleX(0.3); }
  50% { opacity:1; transform:scaleX(1); }
  100% { opacity:0; transform:scaleX(0.3); }
}

/* ========================================================
   ★★★ Glitch 故障特效（stage_hook 切入时）★★★
   ======================================================== */
.glitch-overlay {
  position:fixed;
  inset:0;
  z-index:9000;
  background:rgba(0,0,0,0.6);
  pointer-events:none;
  overflow:hidden;
  animation:glitchBg 1.6s ease;
}

@keyframes glitchBg {
  0% { background:rgba(0,0,0,0); }
  10% { background:rgba(255,0,0,0.3); }
  15% { background:rgba(0,255,255,0.2); }
  20% { background:rgba(0,0,0,0.9); }
  30% { background:rgba(139,0,0,0.6); }
  50% { background:rgba(0,0,0,0.7); }
  100% { background:rgba(0,0,0,0); }
}

.glitch-bar {
  position:absolute;
  left:0;
  right:0;
  height:40px;
  background:linear-gradient(90deg, transparent, #ff0000, transparent);
  opacity:0.8;
  mix-blend-mode:screen;
}

.glitch-bar-1 {
  top:20%;
  animation:glitchBarMove 0.15s steps(2) infinite;
  background:linear-gradient(90deg, transparent, rgba(255,0,0,0.6), transparent);
}
.glitch-bar-2 {
  top:50%;
  height:6px;
  animation:glitchBarMove 0.1s steps(3) infinite reverse;
  background:linear-gradient(90deg, transparent, rgba(0,255,255,0.5), transparent);
}
.glitch-bar-3 {
  top:75%;
  height:20px;
  animation:glitchBarMove 0.2s steps(2) infinite;
  background:linear-gradient(90deg, transparent, rgba(255,255,255,0.4), transparent);
}

@keyframes glitchBarMove {
  0% { transform:translateX(-30px) skewX(0deg); }
  50% { transform:translateX(30px) skewX(-20deg); }
  100% { transform:translateX(-30px) skewX(0deg); }
}

.glitch-text {
  position:absolute;
  top:50%;
  left:50%;
  transform:translate(-50%, -50%);
  font-size:3rem;
  font-weight:700;
  color:#ff3333;
  font-family:'Courier New',monospace;
  letter-spacing:0.8rem;
  text-shadow:
    2px 0 #00ffff,
    -2px 0 #ff00ff;
  animation:glitchText 0.15s steps(2) infinite;
}

.glitch-text::before,
.glitch-text::after {
  content:attr(data-text);
  position:absolute;
  top:0;
  left:0;
  width:100%;
  height:100%;
}

.glitch-text::before {
  color:#00ffff;
  z-index:-1;
  animation:glitchOffset1 0.3s steps(3) infinite alternate;
}

.glitch-text::after {
  color:#ff00ff;
  z-index:-1;
  animation:glitchOffset2 0.3s steps(3) infinite alternate;
}

@keyframes glitchText {
  0%,100% { opacity:1; transform:translate(-50%, -50%); }
  50% { opacity:0.8; transform:translate(-50%, -50%) skewX(-3deg); }
}

@keyframes glitchOffset1 {
  0% { transform:translate(-2px, 0); }
  100% { transform:translate(3px, -2px); }
}
@keyframes glitchOffset2 {
  0% { transform:translate(3px, 0); }
  100% { transform:translate(-2px, 2px); }
}

/* ========================================================
   ★★★ 规则说明弹窗 ★★★
   ======================================================== */
.rules-overlay {
  position:fixed;
  inset:0;
  z-index:400;
  background:rgba(0,0,0,0.92);
  backdrop-filter:blur(8px);
  display:flex;
  align-items:center;
  justify-content:center;
  font-family:'Noto Serif SC','SimSun',serif;
}

.rules-box {
  width:92%;
  max-width:540px;
  padding:35px 40px;
  background:linear-gradient(135deg, #0a0a15 0%, #15151f 50%, #0a0a15 100%);
  border:2px solid #d4af37;
  box-shadow:0 0 60px rgba(212,175,55,0.4), inset 0 0 30px rgba(212,175,55,0.1);
  animation:rulesIn 0.6s cubic-bezier(0.19, 1, 0.22, 1);
  position:relative;
}

@keyframes rulesIn {
  0% { opacity:0; transform:scale(0.9) translateY(20px); }
  100% { opacity:1; transform:scale(1) translateY(0); }
}

.rules-header {
  display:flex;
  align-items:center;
  justify-content:center;
  gap:15px;
  margin-bottom:25px;
  padding-bottom:15px;
  border-bottom:1px solid rgba(212,175,55,0.3);
}

.rules-icon {
  color:#d4af37;
  font-size:1.4rem;
}

.rules-title {
  font-size:1.3rem;
  color:#ffd700;
  letter-spacing:0.3rem;
  margin:0;
  text-shadow:0 0 15px rgba(255,215,0,0.4);
}

.rules-body {
  color:#ccc;
}

.rule-item {
  display:flex;
  gap:16px;
  margin-bottom:18px;
  align-items:flex-start;
}

.rule-num {
  flex-shrink:0;
  width:36px;
  height:36px;
  line-height:34px;
  text-align:center;
  background:linear-gradient(135deg, #8b6914, #4a3a0a);
  border:1px solid #d4af37;
  color:#ffd700;
  font-family:'Courier New',monospace;
  font-size:0.85rem;
  font-weight:700;
  letter-spacing:0.05rem;
}

.rule-content { flex:1; }

.rule-title {
  color:#ffd700;
  font-size:0.95rem;
  margin:0 0 4px 0;
  letter-spacing:0.1rem;
  font-weight:700;
}

.rule-desc {
  color:#aaa;
  font-size:0.85rem;
  margin:0;
  line-height:1.7;
}

.op-tag {
  display:inline-block;
  padding:1px 8px;
  font-size:0.75rem;
  border:1px solid;
  margin:0 2px;
  letter-spacing:0.1rem;
}
.op-tag.op-call { color:#4caf50; border-color:rgba(76,175,80,0.5); }
.op-tag.op-raise { color:#ff6b6b; border-color:rgba(255,107,107,0.5); }
.op-tag.op-fold { color:#888; border-color:#555; }

.rule-tip {
  margin-top:20px;
  padding:12px 15px;
  background:rgba(212,175,55,0.08);
  border-left:3px solid #d4af37;
  font-size:0.82rem;
  color:#d4c4a0;
  line-height:1.8;
}

.tip-highlight {
  color:#ffd700;
  font-weight:700;
}

.rules-btn {
  width:100%;
  padding:14px;
  margin-top:25px;
  background:linear-gradient(180deg, rgba(212,175,55,0.25), rgba(139,105,20,0.15));
  border:1px solid #d4af37;
  color:#ffd700;
  font-size:1rem;
  font-family:inherit;
  letter-spacing:0.5rem;
  cursor:pointer;
  transition:all 0.3s;
}

.rules-btn:hover {
  background:linear-gradient(180deg, rgba(212,175,55,0.4), rgba(139,105,20,0.25));
  box-shadow:0 0 25px rgba(212,175,55,0.5);
  color:#fff;
}

.rules-fade-enter-active,
.rules-fade-leave-active {
  transition:opacity 0.4s ease;
}
.rules-fade-enter-from,
.rules-fade-leave-to {
  opacity:0;
}
</style>
