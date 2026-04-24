<template>
  <div class="game-page" :class="dangerClass">
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
          <span class="stat-value debt-value">¥ {{ debt.toLocaleString() }}</span>
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
        <h1 class="game-logo">印第安扑克</h1>
        <span class="round-badge">第 {{ pokerRound }} 局</span>
      </header>

      <div class="poker-board">
        <div class="poker-status">
          <div class="chips-box player-chips-box">
            <span class="chips-label">你的筹码</span>
            <span class="chips-value player-color">¥{{ playerChips.toLocaleString() }}</span>
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
          <button class="poker-btn call-btn" @click="pokerAction('call')">跟 注</button>
          <div class="raise-group">
            <input type="number" v-model.number="raiseAmount" min="1000" :max="Math.min(playerChips, kChips)" step="1000" class="raise-input"/>
            <button class="poker-btn raise-btn" @click="pokerAction('raise')" :disabled="raiseAmount < 1000">加 注</button>
          </div>
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

const router = useRouter()

// ===== 模式控制 =====
const mode = ref('vn')  // 'vn' | 'poker'

// ===== VN 状态 =====
const debt = ref(500000)
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

function initPoker() {
  pokerRound.value = 0
  playerChips.value = 50000
  kChips.value = 50000
  pot.value = 0
  playerCard.value = 0
  kCard.value = 0
  kTaunt.value = '（K洗着牌，指间的纸牌翻飞如蝶）准备好了？'
  pokerStarted.value = false
  pokerRoundOver.value = false
  pokerGameOver.value = false
  actionLog.value = []
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
      })
    })
    const data = await res.json()

    pokerRound.value++
    playerCard.value = data.player_card
    kCard.value = data.k_card
    pot.value = data.pot
    playerChips.value = data.player_chips
    kChips.value = data.k_chips
    pokerStarted.value = true
    kTaunt.value = '牌已发出。看看我头上是什么？'
    actionLog.value.push({ role: 'system', text: `第 ${pokerRound.value} 局开始 | 底注各 1000 | 底池 ${data.pot}` })
  } catch (e) {
    console.error(e)
    kTaunt.value = '（系统错误——牌局连接中断）'
  } finally {
    pokerLoading.value = false
  }
}

async function pokerAction(action) {
  pokerLoading.value = true

  const bet = action === 'raise' ? Math.max(1000, raiseAmount.value) : 0

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
        pot: action === 'raise' ? pot.value + bet : pot.value,
        player_chips: action === 'raise' ? playerChips.value - bet : playerChips.value,
        k_chips: kChips.value,
        player_action: action,
        player_bet: bet,
        round_history: actionLog.value.map(l => l.text),
      })
    })
    const data = await res.json()

    kTaunt.value = data.taunt
    pot.value = data.new_pot
    playerChips.value = data.player_chips
    kChips.value = data.k_chips

    if (data.k_action === 'raise') {
      actionLog.value.push({ role: 'k', text: `K 加注 ¥${data.k_bet.toLocaleString()}` })
    } else if (data.k_action === 'call') {
      actionLog.value.push({ role: 'k', text: 'K 跟注' })
    } else if (data.k_action === 'fold') {
      actionLog.value.push({ role: 'k', text: 'K 弃牌' })
    } else if (data.k_action === 'win') {
      actionLog.value.push({ role: 'k', text: 'K 获胜（你弃牌）' })
    }

    if (data.round_over) {
      pokerRoundOver.value = true
      roundWinner.value = data.winner
      pokerStarted.value = false

      if (playerChips.value <= 0 || kChips.value <= 0) {
        pokerGameOver.value = true
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

onMounted(() => {
  const name = sessionStorage.getItem('abyss_player_name') || '无名者'
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
</style>
