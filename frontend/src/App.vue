<template>
  <div
    id="abyss-app"
    class="min-h-screen flex flex-col relative overflow-hidden bg-gradient-to-br from-[#FFFCF5] to-[#FDF5E6]"
    :class="{ 'game-mode': isGameMode, 'blank-mode': isBlankLayout }"
  >
    <!-- ============ 全站暖色流体光晕 ============ -->
    <div class="aurora" aria-hidden="true">
      <span class="blob blob-a"></span>
      <span class="blob blob-b"></span>
      <span class="blob blob-c"></span>
      <span class="grain"></span>
    </div>

    <!-- ============ 主内容区：flex-grow 把 Footer 挤到底部 ============ -->
    <main class="app-main flex-grow flex flex-col relative z-10">
      <!-- 登录等无壳布局 -->
      <template v-if="isBlankLayout">
      <router-view v-slot="{ Component }">
        <transition name="fade" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </template>

    <!-- 游戏全屏 -->
    <template v-else-if="isGameMode">
      <router-view v-slot="{ Component }">
        <transition name="fade" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </template>

    <!-- ============ 主大厅：左侧资产翼 + 中央舞台 ============ -->
    <template v-else>
      <div class="shell">
        <!-- ===== 左：个人资产翼 ===== -->
        <aside class="rail liquid-surface">
          <!-- 用户（group-hover 纯 CSS 悬浮菜单） -->
          <div class="user-pop group">
            <header class="user-block">
              <div class="avatar-wrap">
                <div class="avatar">
                  <img
                    :src="avatarUrl"
                    :alt="`${playerName} 的头像`"
                    class="avatar-img"
                    draggable="false"
                  />
                </div>
                <div class="avatar-aura"></div>
              </div>
              <div class="user-meta">
                <div class="user-name">{{ playerName }}</div>
                <div class="user-sub">
                  {{ personalityType || '尚未评估人格' }}
                </div>
              </div>
            </header>

            <!-- 悬浮面板：默认 opacity-0 invisible scale-75，group-hover 时 scale-100 -->
            <div class="user-menu liquid-glass">
              <button
                class="menu-logout liquid-glass-danger spring-bounce"
                @click="handleLogout"
              >
                <svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/>
                  <path d="M16 17l5-5-5-5"/>
                  <path d="M21 12H9"/>
                </svg>
                <span>退出登录</span>
              </button>
            </div>
          </div>

          <!-- MBTI 人格评估主 CTA -->
          <button class="liquid-btn mbti-btn" @click="openAssessment">
            <span class="mbti-spark">
              <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"/>
              </svg>
            </span>
            <span class="mbti-text">
              {{ personalityType ? '重新评估人格' : '反诈 MBTI 测试' }}
            </span>
          </button>

          <!-- 勋章库 -->
          <section class="medal-section">
            <div class="section-label">
              <span>荣誉勋章库</span>
              <span class="section-count">{{ unlockedCount }} / {{ medals.length }}</span>
            </div>
            <div class="medal-grid">
              <div
                v-for="m in medals"
                :key="m.id"
                class="medal-cell"
                :class="[m.tier, { locked: !m.unlocked, fresh: freshMedalIds.has(m.id) }]"
                :title="m.unlocked ? `${m.name} · ${tierLabel(m.tier)}` : '未获得'"
              >
                <div class="medal-icon">
                  <template v-if="['shield','star','eye','bolt'].includes(m.icon)">
                    <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
                      <path v-if="m.icon === 'shield'" d="M12 2 L20 5 V12 C20 17 16 21 12 22 C8 21 4 17 4 12 V5 Z"/>
                      <path v-else-if="m.icon === 'star'" d="M12 2 L14.5 9 L22 9.3 L16 14 L18 21.5 L12 17.3 L6 21.5 L8 14 L2 9.3 L9.5 9 Z"/>
                      <path v-else-if="m.icon === 'eye'" d="M12 5 C5 5 2 12 2 12 C2 12 5 19 12 19 C19 19 22 12 22 12 C22 12 19 5 12 5 Z M12 15 A3 3 0 1 1 12 9 A3 3 0 0 1 12 15 Z"/>
                      <path v-else d="M13 2 L4 14 H11 L10 22 L20 10 H13 Z"/>
                    </svg>
                  </template>
                  <span v-else class="medal-emoji">{{ m.icon }}</span>
                </div>
                <div class="medal-name">{{ m.unlocked ? m.name : '未解锁' }}</div>
              </div>
            </div>
          </section>

          <div class="rail-sep"></div>

          <!-- 导航 -->
          <nav class="rail-nav">
            <router-link to="/chat" class="nav-row" active-class="active">
              <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">
                <path d="M4 6h16v10H8l-4 4V6z"/>
              </svg>
              <span>反诈客服</span>
            </router-link>
            <router-link to="/game" class="nav-row" active-class="active">
              <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="12" cy="12" r="9"/>
                <path d="M12 3v18M3 12h18"/>
              </svg>
              <span>情景模拟</span>
            </router-link>
            <router-link to="/forum" class="nav-row" active-class="active">
              <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">
                <path d="M12 3a9 9 0 0 1 9 9c0 5-4 8-9 8a9 9 0 0 1-3.6-.74L3 21l1.74-5.4A9 9 0 0 1 12 3z"/>
                <path d="M8 11h8M8 14h6"/>
              </svg>
              <span>深渊树洞</span>
            </router-link>
          </nav>

          <!-- 深渊入口：常态克制 / hover 暗红呼吸 -->
          <button class="abyss-card" @click="enterAbyss" title="深渊契约 · 实战模拟">
            <div class="abyss-inner">
              <div class="abyss-glow"></div>
              <div class="abyss-head">
                <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M12 2a7 7 0 0 1 7 7c0 5-4 8-7 13-3-5-7-8-7-13a7 7 0 0 1 7-7z"/>
                  <circle cx="12" cy="9" r="2"/>
                </svg>
                <span class="abyss-tag">CLASSIFIED</span>
              </div>
              <div class="abyss-title">深渊契约</div>
              <div class="abyss-sub">沉浸式闯关 · 识破千层套路</div>
            </div>
          </button>
        </aside>

        <!-- ===== 中：Spotlight + 客服中枢 ===== -->
        <main class="stage">
          <!-- 顶部：可疑链接/话术 举报探针 -->
          <section class="spotlight">
            <div class="spot-field liquid-surface" :class="{ active: spotFocus || spotInput.length > 0 }">
              <svg class="spot-icon" viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="11" cy="11" r="7"/>
                <path d="M20 20l-3.5-3.5"/>
              </svg>
              <input
                v-model="spotInput"
                class="spot-input"
                type="text"
                placeholder="可疑链接 / 话术一键举报研判，DeepSeek 为您分析…"
                @focus="spotFocus = true"
                @blur="spotFocus = false"
                @keyup.enter="runSpotlight"
              />
              <button
                class="liquid-btn spot-submit"
                :disabled="spotLoading || !spotInput.trim()"
                @click="runSpotlight"
              >
                <span v-if="!spotLoading">研判</span>
                <span v-else class="spot-spinner"></span>
              </button>
            </div>

            <transition name="drop">
              <div v-if="spotResult" class="spot-result liquid-surface" :class="`risk-${spotResult.risk}`">
                <div class="spot-result-head">
                  <span class="risk-dot"></span>
                  <span class="risk-label">{{ riskLabel(spotResult.risk) }}</span>
                  <button class="spot-close" @click="spotResult = null" aria-label="关闭">×</button>
                </div>
                <p class="spot-result-body">{{ spotResult.answer }}</p>
              </div>
            </transition>
          </section>

          <!-- AI 客服中枢 -->
          <section class="cabin liquid-surface">
            <router-view v-slot="{ Component }">
              <transition name="fade" mode="out-in">
                <component :is="Component" />
              </transition>
            </router-view>
          </section>
        </main>
      </div>

      <AssessmentModal
        :visible="assessVisible"
        @close="assessVisible = false"
        @completed="onAssessCompleted"
      />
    </template>
    </main>

    <!-- ============ 合规 Footer · 液态玻璃备案信息 ============ -->
    <footer class="site-footer w-full py-6 mt-auto text-center relative z-20">
      <div class="footer-pill liquid-glass">
        <div class="footer-row">
          <span>版权所有 © 2026 反诈王牌</span>
          <span class="footer-sep"></span>
          <a
            href="https://beian.miit.gov.cn/"
            target="_blank"
            rel="noreferrer"
            class="footer-link"
          >
            闽ICP备2026016245号-1
          </a>
        </div>
        <div class="footer-row">
          <img src="/police-icon.png" alt="公安警徽" class="footer-police" />
          <a
            href="https://beian.mps.gov.cn/#/query/webSearch"
            target="_blank"
            rel="noreferrer"
            class="footer-link"
          >
            闽公网安备35078402010138号
          </a>
        </div>
      </div>
    </footer>

    <!-- 全局 Toast（所有布局共用） -->
    <GlobalToast />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AssessmentModal from './components/AssessmentModal.vue'
import GlobalToast from './components/GlobalToast.vue'
import http, { getUser, getUsername, clearAuth } from './services/http'
import { useMedalStore } from './stores/medalStore'

const route = useRoute()
const router = useRouter()
const medalStore = useMedalStore()

const isGameMode = computed(() => route.path.startsWith('/game/intro'))
const isBlankLayout = computed(() => route.meta?.layout === 'blank')

/* ========== 账号 ========== */
// 真实用户名：优先 localStorage(abyss_username) → user.username → JWT sub
// 全都没有则显示「未登录」
const storedUsername = ref(getUsername())
const playerName = computed(() => storedUsername.value || '未登录')

// DiceBear 动态卡通头像：用用户名作为 seed，保证千人千面
const avatarUrl = computed(() => {
  const seed = encodeURIComponent(storedUsername.value || 'Felix')
  return `https://api.dicebear.com/7.x/notionists/svg?seed=${seed}&backgroundColor=transparent`
})

/* ========== 退出登录（group-hover 菜单由纯 CSS 控制显隐） ========== */
function handleLogout() {
  clearAuth()                              // 清掉 abyss_token + abyss_user + abyss_username
  storedUsername.value = ''                // 头像与昵称立即回落默认
  router.push({ name: 'Login' })           // 跳回登录页
}

/* ========== 人格 & 勋章（真实数据 + 8 槽位荣誉墙） ========== */
const personalityType = ref(null)
const traitAnalysis = ref(null)
const unlockedMedals = ref([])
const assessVisible = ref(false)
const freshMedalIds = ref(new Set())

// 预置 8 个荣誉槽——已解锁的会覆盖对应位置
const MEDAL_SLOTS = [
  { id: 'slot_iron_guardian',   name: '钢铁哨兵', icon: 'shield', tier: 'gold' },
  { id: 'slot_composure_shield',name: '镇静之心', icon: 'shield', tier: 'silver' },
  { id: 'slot_heart_guard',     name: '情感之盾', icon: 'star',   tier: 'silver' },
  { id: 'slot_independent_mind',name: '独立心智', icon: 'star',   tier: 'bronze' },
  { id: 'slot_privacy_ward',    name: '隐私守护', icon: 'eye',    tier: 'silver' },
  { id: 'slot_high_yield_trap', name: '识破贪念', icon: 'eye',    tier: 'bronze' },
  { id: 'slot_observer',        name: '清醒观察', icon: 'bolt',   tier: 'silver' },
  { id: 'slot_abyss_survivor',  name: '深渊归来', icon: 'bolt',   tier: 'gold' },
]
const VALID_ICONS = ['shield', 'star', 'eye', 'bolt']
const VALID_TIERS = ['gold', 'silver', 'bronze']

function normalizeMedal(m) {
  return {
    ...m,
    icon: VALID_ICONS.includes(m.icon) ? m.icon : 'star',
    tier: VALID_TIERS.includes(m.tier) ? m.tier : 'bronze',
    unlocked: true,
  }
}

const medals = computed(() => {
  // 合并：后端解锁的 + 本地（Pinia/localStorage）解锁的
  const backendUnlocked = unlockedMedals.value.map(normalizeMedal)
  const localUnlocked = medalStore.unlockedMedals.map((m) => ({
    ...m,
    tier: VALID_TIERS.includes(m.tier) ? m.tier : 'gold',
    unlocked: true,
  }))
  const seen = new Set()
  const unlocked = [...backendUnlocked, ...localUnlocked].filter((m) => {
    if (seen.has(m.id)) return false
    seen.add(m.id)
    return true
  })
  const unlockedIds = new Set(unlocked.map((m) => m.id))
  const fillers = MEDAL_SLOTS
    .filter((s) => !unlockedIds.has(s.id))
    .map((s) => ({ ...s, unlocked: false }))
  const needed = Math.max(0, 8 - unlocked.length)
  return [...unlocked, ...fillers.slice(0, needed)]
})

const unlockedCount = computed(
  () => new Set([
    ...unlockedMedals.value.map((m) => m.id),
    ...medalStore.unlockedMedals.map((m) => m.id),
  ]).size
)

function tierLabel(t) {
  return { gold: 'GOLD', silver: 'SILVER', bronze: 'BRONZE' }[t] || ''
}

async function loadProfile() {
  if (!getUser()) return
  try {
    const { data } = await http.get('/assess/profile')
    personalityType.value = data.personality_type
    traitAnalysis.value = data.trait_analysis
    unlockedMedals.value = (data.medals || []).filter(m => m.unlocked)
  } catch (e) {
    if (e?.response?.status === 401) return
    console.warn('加载人格档案失败', e)
  }
}

function openAssessment() {
  assessVisible.value = true
}

function onAssessCompleted(data) {
  personalityType.value = data.personality_type
  traitAnalysis.value = data.trait_analysis

  const before = new Set(unlockedMedals.value.map(m => m.id))
  const next = (data.all_medals || []).filter(m => m.unlocked)
  unlockedMedals.value = next

  const freshCopy = new Set(freshMedalIds.value)
  for (const m of next) {
    if (!before.has(m.id)) freshCopy.add(m.id)
  }
  freshMedalIds.value = freshCopy
  setTimeout(() => { freshMedalIds.value = new Set() }, 2400)
}

/* ========== Spotlight：一键举报 → DeepSeek 研判 ========== */
const spotInput = ref('')
const spotFocus = ref(false)
const spotLoading = ref(false)
const spotResult = ref(null)

function riskLabel(r) {
  return { high: '高危 · 建议立即阻断', mid: '可疑 · 需人工复核', low: '低风险' }[r] || '研判结果'
}

function mapRisk(level) {
  if (!level) return 'low'
  const l = String(level).toLowerCase()
  if (l.includes('high') || l === '高') return 'high'
  if (l.includes('mid') || l.includes('medium') || l === '中') return 'mid'
  return 'low'
}

async function runSpotlight() {
  const text = spotInput.value.trim()
  if (!text || spotLoading.value) return
  spotLoading.value = true
  spotResult.value = null
  try {
    const { data } = await http.post('/chat/ask', {
      question: `请研判以下内容的诈骗风险并给出简短建议：${text}`,
    })
    spotResult.value = {
      risk: mapRisk(data.risk_level),
      answer: (data.answer || '').slice(0, 280),
    }
  } catch (e) {
    if (e?.response?.status === 401) return
    spotResult.value = {
      risk: 'low',
      answer: '研判失败：请检查网络或稍后重试。',
    }
  } finally {
    spotLoading.value = false
  }
}

/* ========== 深渊契约入口 ========== */
function enterAbyss() {
  router.push('/game')
}

// 每次切路由重新同步 localStorage 中的用户名（登录/登出后生效）
watch(
  () => route.fullPath,
  () => {
    storedUsername.value = getUsername()
    medalStore.syncWithCurrentUser()
  }
)

// 已登录态变化时拉一次服务端勋章 + 进度（用于跨设备 / 跨登录持久化）
watch(
  storedUsername,
  (name) => {
    if (name) {
      medalStore.hydrateFromServer()
    }
  },
  { immediate: false }
)

onMounted(() => {
  medalStore.syncWithCurrentUser()
  if (storedUsername.value) {
    medalStore.hydrateFromServer()
  }
  loadProfile()
})
</script>

<style>
/* ============================================================
   全局基础 · 暖色 · 正能量反诈
============================================================ */
* { margin: 0; padding: 0; box-sizing: border-box; }

:root {
  /* 基底暖色 */
  --bg-cream:   #fbf6ee;
  --bg-paper:   #fff8ed;
  --bg-warm:    #fff0db;

  /* 玻璃与边线 */
  --glass-pane: rgba(255, 253, 248, 0.55);
  --glass-high: rgba(255, 255, 255, 0.85);
  --glass-edge: rgba(255, 185, 120, 0.22);

  /* 文字 */
  --ink-0: #2d2416;
  --ink-1: #463727;
  --ink-2: #7e6a4f;
  --ink-3: #b8a583;
  --ink-4: rgba(70, 55, 39, 0.12);

  /* 主题色 */
  --warm-gold:   #e8a948;
  --warm-amber:  #ff9a56;
  --warm-peach:  #ffc88c;
  --warm-sunset: #ff7a50;

  --success: #5fbf8a;
  --warning: #f5a524;
  --danger:  #d94a67;

  /* 阴影 */
  --shadow-soft:
    0 10px 34px rgba(200, 140, 70, 0.10),
    0 2px 8px rgba(180, 120, 60, 0.06);
  --shadow-lift:
    0 22px 60px rgba(200, 130, 60, 0.16),
    0 6px 16px rgba(180, 110, 50, 0.08);

  /* 弹簧曲线 */
  --spring: cubic-bezier(0.25, 1.5, 0.5, 1);
  --ease-ios: cubic-bezier(0.4, 0, 0.2, 1);
}

html, body, #app { height: 100%; }
body {
  font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'SF Pro Text',
               'Inter', 'PingFang SC', 'Helvetica Neue', sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  color: var(--ink-1);
  letter-spacing: 0.005em;
  /* 奶油沙色渐变 · Tailwind: bg-gradient-to-br from-[#FFFCF5] to-[#FDF5E6] */
  min-height: 100vh;
  background: linear-gradient(to bottom right, #FFFCF5 0%, #FDF5E6 100%);
  background-attachment: fixed;
}

#abyss-app {
  position: relative;
  min-height: 100vh;
  width: 100%;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

/* 游戏模式：覆盖全站暖色，走深渊暗色基调 */
#abyss-app.game-mode {
  background: #050508;
}
#abyss-app.game-mode .aurora { display: none; }

/* ============================================================
   流体光晕 · 极光极浅（暖橘 / 浅黄 / 柔粉）
============================================================ */
.aurora {
  position: fixed;
  inset: 0;
  z-index: 0;
  overflow: hidden;
  pointer-events: none;
}
.aurora .blob {
  position: absolute;
  border-radius: 50%;
  filter: blur(64px);              /* Tailwind blur-3xl */
  opacity: 0.6;                    /* Tailwind opacity-60 */
  mix-blend-mode: multiply;        /* mix-blend-multiply */
  will-change: transform;
}
.aurora .blob-a {
  width: 640px; height: 640px;
  top: -160px; left: -120px;
  background: radial-gradient(circle, #FFD6A8 0%, transparent 70%);
  animation: drift-a 30s ease-in-out infinite alternate;
}
.aurora .blob-b {
  width: 720px; height: 720px;
  bottom: -220px; right: -180px;
  background: radial-gradient(circle, #FFF0C2 0%, transparent 70%);
  animation: drift-b 36s ease-in-out infinite alternate;
}
.aurora .blob-c {
  width: 500px; height: 500px;
  top: 40%; left: 55%;
  background: radial-gradient(circle, #FFD6DC 0%, transparent 70%);
  animation: drift-c 44s ease-in-out infinite alternate;
}
@keyframes drift-a {
  0%   { transform: translate(0, 0) scale(1); }
  100% { transform: translate(80px, 60px) scale(1.1); }
}
@keyframes drift-b {
  0%   { transform: translate(0, 0) scale(1); }
  100% { transform: translate(-100px, -40px) scale(1.08); }
}
@keyframes drift-c {
  0%   { transform: translate(-50%, -50%) scale(1); }
  100% { transform: translate(-30%, -60%) scale(1.15); }
}
.aurora .grain {
  position: absolute;
  inset: 0;
  background-image: url('data:image/svg+xml,%3Csvg viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg"%3E%3Cfilter id="n"%3E%3CfeTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="2"/%3E%3C/filter%3E%3Crect width="100%25" height="100%25" filter="url(%23n)" opacity="0.35"/%3E%3C/svg%3E');
  opacity: 0.03;
  mix-blend-mode: multiply;
}

/* ============================================================
   核心魔法类 · Liquid Glass + Spring Bounce
   （严格按设计稿参数，不做二次调参）
============================================================ */
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
    inset 0 -2px 6px rgba(239, 68, 68, 0.1),
    0 8px 24px rgba(239, 68, 68, 0.15);
}

.spring-bounce {
  transition: all 0.5s cubic-bezier(0.25, 1.5, 0.5, 1);
}
.spring-bounce:active {
  transform: scale(0.92) translateY(2px);
}

/* ============================================================
   液态玻璃基类
   - 白色半透明 + 模糊 + 高光内阴影 + 暖边
   - :active 弹簧阻力回弹
============================================================ */
.liquid-surface {
  background: var(--glass-pane);
  backdrop-filter: blur(22px) saturate(180%);
  -webkit-backdrop-filter: blur(22px) saturate(180%);
  box-shadow:
    inset 0 1px 0 var(--glass-high),
    inset 0 -0.5px 0 rgba(255, 255, 255, 0.4),
    inset 0 0 0 0.5px var(--glass-edge),
    var(--shadow-soft);
}

.liquid-btn {
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 12px 20px;
  border: none;
  outline: none;
  cursor: pointer;
  font-family: inherit;
  font-size: 0.9rem;
  font-weight: 500;
  letter-spacing: 0.04em;
  color: var(--ink-0);
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.6);
  backdrop-filter: blur(18px) saturate(180%);
  -webkit-backdrop-filter: blur(18px) saturate(180%);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.95),
    inset 0 -1px 0 rgba(255, 255, 255, 0.4),
    inset 0 0 0 0.5px rgba(255, 180, 120, 0.25),
    0 10px 26px rgba(200, 130, 60, 0.14),
    0 2px 6px rgba(180, 110, 50, 0.08);
  transition: transform 0.4s var(--spring),
              background 0.3s var(--ease-ios),
              box-shadow 0.3s var(--ease-ios),
              color 0.25s ease;
}
.liquid-btn:hover:not(:disabled) {
  background: rgba(255, 255, 255, 0.82);
  transform: translateY(-1px);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 1),
    inset 0 0 0 0.5px rgba(255, 154, 86, 0.45),
    0 16px 40px rgba(255, 154, 86, 0.22),
    0 4px 10px rgba(200, 130, 60, 0.12);
  color: var(--warm-sunset);
}
.liquid-btn:active:not(:disabled) {
  transform: scale(0.92);
  transition: all 0.4s var(--spring);
}
.liquid-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* ============================================================
   主壳
============================================================ */
.shell {
  position: relative;
  z-index: 1;
  display: grid;
  grid-template-columns: 280px minmax(0, 1fr);
  gap: 18px;
  flex: 1 1 auto;
  min-height: 0;
  padding: 18px 24px 18px 18px;
}

/* ============================================================
   左：资产翼
============================================================ */
.rail {
  display: flex;
  flex-direction: column;
  padding: 22px 18px 18px;
  border-radius: 28px;
  gap: 18px;
  /* 固定最大宽度，防止被内部勋章墙撑爆 */
  width: 100%;
  max-width: 280px;
  min-width: 0;
  /* 去掉 overflow:hidden，否则 user-menu 会被裁掉 */
  overflow: visible;
  position: relative;
  z-index: 2;
}

/* 用户块 */
.user-block {
  display: flex;
  align-items: center;
  gap: 12px;
}
.avatar-wrap {
  position: relative;
  width: 48px; height: 48px;
}
.avatar {
  position: relative;
  z-index: 1;
  width: 48px; height: 48px;
  border-radius: 16px;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #ffb578, var(--warm-sunset));
  box-shadow:
    0 10px 24px rgba(255, 130, 70, 0.35),
    inset 0 1px 0 rgba(255, 255, 255, 0.4);
}
.avatar-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  border-radius: 16px;
  user-select: none;
  -webkit-user-drag: none;
  pointer-events: none;
}
.avatar-aura {
  position: absolute;
  inset: -6px;
  border-radius: 22px;
  background: radial-gradient(circle, rgba(255, 170, 90, 0.35), transparent 65%);
  filter: blur(10px);
}
.user-meta { min-width: 0; flex: 1; }
.user-name {
  font-size: 0.96rem;
  font-weight: 600;
  color: var(--ink-0);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.user-sub {
  font-size: 0.74rem;
  color: var(--ink-2);
  margin-top: 3px;
  letter-spacing: 0.02em;
}

/* ============================================================
   头像 Hover 菜单 · 纯 CSS group-hover + 弹簧弹出
============================================================ */
.user-pop {
  position: relative;
}
/* 允许 group-hover 持续触发：从头像到菜单的 14px 间隙加一块透明的 hit 区域 */
.user-pop.group::after {
  content: '';
  position: absolute;
  top: 0;
  left: 100%;
  width: 18px;
  height: 100%;
  pointer-events: none;
}
.user-pop.group:hover::after,
.user-pop.group:focus-within::after {
  pointer-events: auto;
}

.user-menu {
  position: absolute;
  top: 0;
  left: calc(100% + 14px);
  z-index: 40;
  min-width: 172px;
  padding: 8px;
  border-radius: 18px;
  transform-origin: left center;

  /* 默认：opacity-0 invisible scale-75 */
  opacity: 0;
  visibility: hidden;
  transform: scale(0.75) translateX(-6px);

  /* 弹簧过渡 · duration-500 · cubic-bezier(0.25, 1.5, 0.5, 1) */
  transition:
    opacity 0.5s cubic-bezier(0.25, 1.5, 0.5, 1),
    transform 0.5s cubic-bezier(0.25, 1.5, 0.5, 1),
    visibility 0s linear 0.5s;   /* 先等 opacity 走完再隐藏 */
}

/* group-hover → opacity-100 visible scale-100 */
.user-pop.group:hover .user-menu,
.user-pop.group:focus-within .user-menu {
  opacity: 1;
  visibility: visible;
  transform: scale(1) translateX(0);
  transition:
    opacity 0.5s cubic-bezier(0.25, 1.5, 0.5, 1),
    transform 0.5s cubic-bezier(0.25, 1.5, 0.5, 1),
    visibility 0s linear 0s;
}

/* 退出登录按钮 · liquid-glass-danger + spring-bounce（类已在全局） */
.menu-logout {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 11px 16px;
  border-radius: 12px;
  color: #dc2626;
  font-family: inherit;
  font-size: 0.86rem;
  font-weight: 700;      /* 淡红色加粗 */
  letter-spacing: 0.04em;
  cursor: pointer;
}
.menu-logout:hover {
  /* 轻微液态反光变化 */
  background: rgba(254, 226, 226, 0.85);
  box-shadow:
    inset 0 2px 4px rgba(255, 255, 255, 1),
    inset 0 -2px 8px rgba(239, 68, 68, 0.18),
    0 10px 28px rgba(239, 68, 68, 0.22);
  color: #b91c1c;
}

/* MBTI 主 CTA */
.mbti-btn {
  width: 100%;
  padding: 14px 16px;
  font-size: 0.88rem;
  font-weight: 500;
  letter-spacing: 0.05em;
  color: var(--warm-sunset);
  background: linear-gradient(135deg, rgba(255, 240, 220, 0.9), rgba(255, 215, 170, 0.7));
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 1),
    inset 0 0 0 0.5px rgba(255, 154, 86, 0.38),
    0 12px 28px rgba(255, 154, 86, 0.22),
    0 3px 8px rgba(200, 120, 60, 0.1);
}
.mbti-btn:hover:not(:disabled) {
  color: #fff;
  background: linear-gradient(135deg, #ffb578, var(--warm-sunset));
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.5),
    0 16px 40px rgba(255, 122, 80, 0.45);
}
.mbti-spark { display: inline-flex; }

/* 勋章 */
.medal-section {
  flex-shrink: 0;
  min-width: 0;
  max-width: 100%;
}
.section-label {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.7rem;
  font-weight: 500;
  letter-spacing: 0.14em;
  color: var(--ink-2);
  text-transform: uppercase;
  margin-bottom: 12px;
  padding: 0 2px;
}
.section-count {
  font-family: 'SF Mono', ui-monospace, monospace;
  font-size: 0.72rem;
  color: var(--warm-sunset);
  padding: 2px 8px;
  background: rgba(255, 154, 86, 0.12);
  border-radius: 8px;
  letter-spacing: 0.05em;
}
/* 自适应容器：固定最大高度 + 垂直滚动 + 隐藏滚动条 */
.medal-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 8px;
  max-height: 200px;
  overflow-y: auto;
  overflow-x: hidden;
  /* Firefox */
  scrollbar-width: none;
  /* IE / 旧 Edge */
  -ms-overflow-style: none;
  padding-right: 2px;
}
/* WebKit 内核隐藏 */
.medal-grid::-webkit-scrollbar { width: 0; height: 0; display: none; }
.medal-cell {
  aspect-ratio: 1/1.1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4px;
  padding: 8px 4px 6px;
  border-radius: 12px;
  min-width: 0;
  background: rgba(255, 255, 255, 0.45);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.9),
    inset 0 0 0 0.5px rgba(255, 180, 120, 0.18);
  transition: transform 0.4s var(--spring);
}
.medal-cell:hover { transform: translateY(-2px) scale(1.04); }
.medal-icon { display: flex; align-items: center; justify-content: center; min-height: 22px; }
.medal-emoji { font-size: 1.05rem; line-height: 1; filter: drop-shadow(0 1px 2px rgba(0,0,0,0.18)); }
.medal-name {
  font-size: 0.62rem;
  font-weight: 500;
  letter-spacing: 0.02em;
  color: var(--ink-1);
  max-width: 100%;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.medal-cell.gold   { color: #d99a2e; box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.95), inset 0 0 0 0.5px rgba(217, 154, 46, 0.4), 0 4px 14px rgba(230, 170, 60, 0.2); }
.medal-cell.silver { color: #9c8b70; }
.medal-cell.bronze { color: #b47a42; }
.medal-cell.locked {
  color: var(--ink-3);
  background: rgba(255, 255, 255, 0.25);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.55);
}
.medal-cell.locked .medal-name { color: var(--ink-3); }
.medal-cell.fresh {
  animation: medalPop 1.8s cubic-bezier(0.22, 1, 0.36, 1);
}
@keyframes medalPop {
  0%   { transform: scale(0.4) rotate(-12deg); opacity: 0; filter: brightness(1.6); }
  55%  { transform: scale(1.18) rotate(4deg);  opacity: 1; }
  100% { transform: scale(1);                   filter: brightness(1); }
}

/* 分隔 */
.rail-sep {
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(200, 150, 100, 0.25), transparent);
}

/* 导航 */
.rail-nav {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.nav-row {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 11px 14px;
  border-radius: 14px;
  color: var(--ink-2);
  text-decoration: none;
  font-size: 0.88rem;
  font-weight: 500;
  letter-spacing: 0.02em;
  transition: all 0.3s var(--ease-ios);
}
.nav-row:hover {
  color: var(--ink-0);
  background: rgba(255, 255, 255, 0.5);
}
.nav-row.active {
  color: var(--warm-sunset);
  background: rgba(255, 255, 255, 0.72);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.95),
    inset 0 0 0 0.5px rgba(255, 154, 86, 0.28),
    0 4px 14px rgba(255, 154, 86, 0.12);
}

/* 深渊入口：常态克制 / hover 暗红呼吸 */
.abyss-card {
  margin-top: auto;
  width: 100%;
  padding: 0;
  border: none;
  background: transparent;
  cursor: pointer;
  font-family: inherit;
}
.abyss-inner {
  position: relative;
  padding: 14px 16px;
  border-radius: 18px;
  color: var(--ink-1);
  text-align: left;
  background: linear-gradient(160deg, rgba(255, 250, 240, 0.6), rgba(255, 225, 210, 0.35));
  backdrop-filter: blur(14px) saturate(150%);
  -webkit-backdrop-filter: blur(14px) saturate(150%);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.95),
    inset 0 0 0 0.5px rgba(200, 120, 80, 0.12),
    0 6px 18px rgba(180, 100, 70, 0.1);
  overflow: hidden;
  transition: all 0.4s var(--ease-ios);
}
.abyss-glow {
  position: absolute;
  inset: 0;
  border-radius: 18px;
  background: radial-gradient(ellipse at top right, rgba(217, 74, 103, 0.22), transparent 65%);
  opacity: 0;
  transition: opacity 0.5s var(--ease-ios);
  pointer-events: none;
}
.abyss-card:hover .abyss-inner {
  color: #732330;
  background: linear-gradient(160deg, rgba(255, 235, 230, 0.85), rgba(255, 200, 195, 0.65));
  animation: abyssBreath 2.6s ease-in-out infinite;
}
.abyss-card:hover .abyss-glow { opacity: 1; }
.abyss-card:active .abyss-inner {
  transform: scale(0.96);
  transition: transform 0.4s var(--spring);
}
@keyframes abyssBreath {
  0%, 100% {
    box-shadow:
      inset 0 1px 0 rgba(255, 255, 255, 0.9),
      inset 0 0 0 0.5px rgba(217, 74, 103, 0.3),
      0 6px 18px rgba(180, 50, 70, 0.12);
  }
  50% {
    box-shadow:
      inset 0 1px 0 rgba(255, 255, 255, 0.9),
      inset 0 0 0 0.5px rgba(217, 74, 103, 0.55),
      0 10px 32px rgba(217, 74, 103, 0.32),
      0 0 42px rgba(217, 74, 103, 0.18);
  }
}
.abyss-head {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 6px;
}
.abyss-tag {
  font-family: 'SF Mono', ui-monospace, monospace;
  font-size: 0.6rem;
  font-weight: 500;
  letter-spacing: 0.2em;
  color: var(--ink-2);
}
.abyss-card:hover .abyss-tag { color: #a8334a; }
.abyss-title {
  font-size: 1.05rem;
  font-weight: 600;
  letter-spacing: 0.3em;
  margin-bottom: 4px;
}
.abyss-sub {
  font-size: 0.7rem;
  color: var(--ink-2);
  line-height: 1.5;
  font-weight: 300;
}
.abyss-card:hover .abyss-sub { color: rgba(115, 35, 48, 0.72); }

/* ============================================================
   中：舞台
============================================================ */
.stage {
  display: flex;
  flex-direction: column;
  gap: 14px;
  min-width: 0;
}

/* ---------- Spotlight ---------- */
.spotlight {
  display: flex;
  flex-direction: column;
  align-items: center;
}
.spot-field {
  width: 100%;
  max-width: 820px;
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 12px 12px 12px 22px;
  border-radius: 22px;
  transition: all 0.35s var(--ease-ios);
}
.spot-field.active {
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.95),
    inset 0 0 0 0.5px rgba(255, 154, 86, 0.55),
    0 18px 46px rgba(255, 154, 86, 0.2),
    0 4px 12px rgba(200, 120, 60, 0.1);
}
.spot-icon { color: var(--ink-3); flex-shrink: 0; }
.spot-field.active .spot-icon { color: var(--warm-sunset); }

.spot-input {
  flex: 1;
  border: none;
  background: transparent;
  color: var(--ink-0);
  font-size: 0.98rem;
  font-family: inherit;
  outline: none;
  letter-spacing: 0.01em;
}
.spot-input::placeholder {
  color: var(--ink-3);
  font-weight: 300;
}

.spot-submit {
  padding: 10px 18px;
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--warm-sunset);
  border-radius: 14px;
}

.spot-spinner {
  width: 14px; height: 14px;
  border: 2px solid rgba(255, 154, 86, 0.25);
  border-top-color: var(--warm-sunset);
  border-radius: 50%;
  animation: spin 0.9s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

/* Spotlight 结果 */
.spot-result {
  width: 100%;
  max-width: 820px;
  margin-top: 10px;
  padding: 14px 18px;
  border-radius: 18px;
}
.spot-result-head {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 8px;
  font-size: 0.78rem;
  letter-spacing: 0.04em;
}
.risk-dot { width: 7px; height: 7px; border-radius: 50%; }
.risk-label { flex: 1; color: var(--ink-1); font-weight: 500; }

.spot-result.risk-high .risk-dot  { background: var(--danger); box-shadow: 0 0 10px rgba(217, 74, 103, 0.55); }
.spot-result.risk-high .risk-label{ color: #a8334a; }
.spot-result.risk-mid  .risk-dot  { background: var(--warning); box-shadow: 0 0 10px rgba(245, 165, 36, 0.5); }
.spot-result.risk-mid  .risk-label{ color: #b47014; }
.spot-result.risk-low  .risk-dot  { background: var(--success); box-shadow: 0 0 8px rgba(95, 191, 138, 0.5); }
.spot-result.risk-low  .risk-label{ color: #3c8e64; }

.spot-close {
  border: none;
  background: transparent;
  color: var(--ink-3);
  cursor: pointer;
  font-size: 1.2rem;
  line-height: 1;
  padding: 2px 8px;
  border-radius: 6px;
  transition: all 0.2s;
}
.spot-close:hover { color: var(--ink-0); background: rgba(255, 255, 255, 0.55); }

.spot-result-body {
  font-size: 0.88rem;
  line-height: 1.75;
  color: var(--ink-1);
  font-weight: 400;
}

.drop-enter-active { transition: all 0.35s cubic-bezier(0.22, 1, 0.36, 1); }
.drop-leave-active { transition: all 0.22s ease; }
.drop-enter-from   { opacity: 0; transform: translateY(-6px); }
.drop-leave-to     { opacity: 0; transform: translateY(-4px); }

/* ---------- 客服舱 ---------- */
.cabin {
  flex: 1;
  min-height: 0;
  position: relative;
  border-radius: 32px;
  overflow: hidden;
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.9),
    inset 0 0 0 0.5px rgba(255, 180, 120, 0.25),
    0 26px 80px rgba(200, 130, 70, 0.12),
    0 8px 22px rgba(180, 110, 50, 0.06);
}

/* ============================================================
   通用过渡
============================================================ */
.fade-enter-active, .fade-leave-active { transition: opacity 0.35s var(--ease-ios); }
.fade-enter-from, .fade-leave-to { opacity: 0; }

/* ============================================================
   响应式
============================================================ */
@media (max-width: 960px) {
  .shell {
    grid-template-columns: 1fr;
    padding: 12px;
    gap: 12px;
    height: auto;
    min-height: 100vh;
  }
  .rail {
    order: 2;
    max-width: 100%;
  }
  .stage { order: 1; }
  .medal-grid {
    grid-template-columns: repeat(4, minmax(0, 1fr));
    max-height: 240px;
  }
}

/* ============================================================
   合规 Footer · 液态玻璃备案信息
============================================================ */
.site-footer {
  width: 100%;
  margin-top: auto;
  padding: 16px 16px 24px;
  text-align: center;
  position: relative;
  z-index: 20;
}
.footer-pill {
  display: inline-flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 10px 22px;
  border-radius: 18px;
  font-size: 11px;
  font-weight: 500;
  color: #6b7280;          /* tailwind text-gray-500 */
  letter-spacing: 0.02em;
}
.footer-row {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  transition: color 0.25s ease;
}
.footer-row:hover { color: #374151; }
.footer-sep {
  width: 1px;
  height: 12px;
  background: #d1d5db;     /* tailwind bg-gray-300 */
}
.footer-link {
  color: inherit;
  text-decoration: none;
  transition: color 0.25s ease;
}
.footer-link:hover {
  color: #3b82f6;          /* tailwind text-blue-500 */
  text-decoration: underline;
}
.footer-police {
  width: 16px;
  height: 16px;
  object-fit: contain;
  filter: drop-shadow(0 1px 2px rgba(0, 0, 0, 0.18));
}

/* 主内容区：让 main 撑满剩余高度，把 footer 顶到底部 */
.app-main {
  flex: 1 1 auto;
  display: flex;
  flex-direction: column;
  min-height: 0;
  position: relative;
  z-index: 10;
}

/* 液态玻璃通用类：与设计稿原参数一致；已存在则只是同义重声明，无副作用 */
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
</style>
