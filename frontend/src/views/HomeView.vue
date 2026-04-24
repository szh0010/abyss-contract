<template>
  <div class="home-page">
    <!-- 序章：电影式过场 -->
    <div v-if="phase === 'intro'" class="intro-screen">
      <div class="intro-content">
        <h1 class="main-title">
          <span class="char" v-for="(ch, i) in titleChars" :key="i" :style="{ animationDelay: i * 0.15 + 's' }">{{ ch }}</span>
        </h1>
        <p class="subtitle" :class="{ visible: showSubtitle }">ABYSS CONTRACT</p>
        <div class="divider" :class="{ visible: showDivider }"></div>
        <p class="lore-line" v-for="(line, i) in loreLines" :key="'l'+i"
           :class="{ visible: visibleLines > i }"
           :style="{ transitionDelay: (i * 0.3) + 's' }">
          <span v-if="line.highlight" class="highlight">{{ line.text }}</span>
          <span v-else>{{ line.text }}</span>
        </p>
        <button class="enter-btn" :class="{ visible: showEnterBtn }" @click="phase = 'name'">
          【 坐 下 】
        </button>
      </div>
      <!-- 底部微光脉搏 -->
      <div class="pulse-line"></div>
    </div>

    <!-- 输入名字 -->
    <div v-else-if="phase === 'name'" class="name-screen">
      <div class="name-card">
        <div class="card-accent"></div>
        <p class="name-prompt">坐下之前，先告诉我——</p>
        <h2 class="name-question">你叫什么名字？</h2>
        <div class="input-wrapper">
          <input
            ref="nameInput"
            v-model="playerName"
            type="text"
            placeholder="输入你的名字"
            maxlength="20"
            @keyup.enter="startGame"
            autofocus
          />
          <div class="input-underline"></div>
        </div>
        <button class="confirm-btn" @click="startGame" :disabled="isLoading">
          <span v-if="!isLoading">确 认</span>
          <span v-else class="loading-text">
            <span>连</span><span>接</span><span>中</span>
            <span class="dot">.</span><span class="dot">.</span><span class="dot">.</span>
          </span>
        </button>
        <p class="skip-hint" @click="playerName = ''; startGame()">跳过，以「无名者」身份进入</p>
      </div>
    </div>

    <!-- 页脚 -->
    <footer class="home-footer">
      <p>本游戏为反赌博 / 反诈骗教育作品 &nbsp;|&nbsp; 报警电话 110 &nbsp;|&nbsp; 法律援助 12348</p>
    </footer>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const phase = ref('intro')
const playerName = ref('')
const isLoading = ref(false)
const nameInput = ref(null)

// 标题逐字动画
const titleChars = ['深', ' ', '渊', ' ', '契', ' ', '约']

// 序章文字
const loreLines = [
  { text: '因为轻信所谓的"内幕消息"……', highlight: false },
  { text: '你背上了 ¥500,000 的高利贷。', highlight: true },
  { text: '催债人没有动粗，只是把你带到了这间没有窗户的地下室。', highlight: false },
  { text: '坐在阴影里的那个男人，已经等候多时。', highlight: false },
]

// 渐入控制
const showSubtitle = ref(false)
const showDivider = ref(false)
const visibleLines = ref(0)
const showEnterBtn = ref(false)

onMounted(() => {
  // 时序编排
  setTimeout(() => { showSubtitle.value = true }, 1200)
  setTimeout(() => { showDivider.value = true }, 1800)
  setTimeout(() => { visibleLines.value = 1 }, 2500)
  setTimeout(() => { visibleLines.value = 2 }, 4000)
  setTimeout(() => { visibleLines.value = 3 }, 5500)
  setTimeout(() => { visibleLines.value = 4 }, 7000)
  setTimeout(() => { showEnterBtn.value = true }, 8500)
})

async function startGame() {
  isLoading.value = true
  try {
    // 存储名字到 sessionStorage，GameView 会读取
    const name = playerName.value.trim() || '无名者'
    sessionStorage.setItem('abyss_player_name', name)
    router.push('/game')
  } catch (err) {
    alert('出错了，请重试')
    console.error(err)
  } finally {
    isLoading.value = false
  }
}
</script>

<style scoped>
.home-page {
  width: 100%;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  position: relative;
  overflow: hidden;
}

/* ======== 序章过场 ======== */
.intro-screen {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  flex: 1;
  width: 100%;
  max-width: 700px;
  padding: 2rem;
  text-align: center;
}

.intro-content {
  position: relative;
  z-index: 2;
}

/* 标题逐字飘入 */
.main-title {
  font-size: 3.5rem;
  font-weight: 700;
  color: #8b0000;
  letter-spacing: 0.8rem;
  margin-bottom: 0.5rem;
  text-shadow: 0 0 40px rgba(139, 0, 0, 0.5), 0 0 80px rgba(139, 0, 0, 0.2);
}

.main-title .char {
  display: inline-block;
  opacity: 0;
  transform: translateY(20px);
  animation: charIn 0.8s ease forwards;
}

@keyframes charIn {
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.subtitle {
  font-size: 0.85rem;
  color: #555;
  letter-spacing: 1rem;
  font-family: 'Courier New', monospace;
  opacity: 0;
  transform: translateY(8px);
  transition: all 1s ease;
}
.subtitle.visible {
  opacity: 1;
  transform: translateY(0);
}

.divider {
  width: 0;
  height: 1px;
  background: linear-gradient(90deg, transparent, #8b0000, transparent);
  margin: 2rem auto;
  transition: width 1.2s ease;
  box-shadow: 0 0 10px rgba(139, 0, 0, 0.4);
}
.divider.visible {
  width: 120px;
}

/* 剧情文字 */
.lore-line {
  font-size: 1.05rem;
  color: #777;
  line-height: 2;
  margin-bottom: 0.8rem;
  opacity: 0;
  transform: translateY(12px);
  filter: blur(4px);
  transition: all 1s ease;
}
.lore-line.visible {
  opacity: 1;
  transform: translateY(0);
  filter: blur(0);
}
.lore-line .highlight {
  color: #ff3333;
  font-weight: 700;
  font-family: 'Courier New', monospace;
  text-shadow: 0 0 12px rgba(255, 51, 51, 0.4);
}

/* 进入按钮 */
.enter-btn {
  margin-top: 2.5rem;
  padding: 14px 60px;
  background: transparent;
  border: 1px solid #4a0000;
  color: #8b0000;
  font-size: 1.4rem;
  font-family: inherit;
  letter-spacing: 0.8rem;
  cursor: pointer;
  transition: all 0.4s ease;
  opacity: 0;
  transform: translateY(10px);
}
.enter-btn.visible {
  opacity: 1;
  transform: translateY(0);
}
.enter-btn:hover {
  background: rgba(139, 0, 0, 0.15);
  color: #ff3333;
  border-color: #8b0000;
  box-shadow: 0 0 25px rgba(139, 0, 0, 0.3), inset 0 0 25px rgba(139, 0, 0, 0.1);
}

/* 底部脉搏光线 */
.pulse-line {
  position: absolute;
  bottom: 60px;
  left: 50%;
  transform: translateX(-50%);
  width: 200px;
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(139, 0, 0, 0.4), transparent);
  animation: pulse 3s ease-in-out infinite;
}
@keyframes pulse {
  0%, 100% { opacity: 0.2; width: 100px; }
  50% { opacity: 0.8; width: 300px; }
}

/* ======== 输入名字 ======== */
.name-screen {
  display: flex;
  align-items: center;
  justify-content: center;
  flex: 1;
  width: 100%;
  padding: 2rem;
  animation: fadeUp 0.8s ease;
}

@keyframes fadeUp {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}

.name-card {
  position: relative;
  width: 100%;
  max-width: 420px;
  padding: 3rem 2.5rem;
  background: rgba(10, 10, 15, 0.9);
  border: 1px solid #1a1a2e;
  text-align: center;
}

.card-accent {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: linear-gradient(90deg, transparent, #8b0000, transparent);
}

.name-prompt {
  font-size: 0.85rem;
  color: #555;
  margin-bottom: 0.5rem;
}

.name-question {
  font-size: 1.4rem;
  color: #ccc;
  font-weight: 400;
  margin-bottom: 2rem;
  letter-spacing: 0.3rem;
}

.input-wrapper {
  position: relative;
  margin-bottom: 2rem;
}

.input-wrapper input {
  width: 100%;
  padding: 12px 0;
  background: transparent;
  border: none;
  border-bottom: 1px solid #333;
  color: #e0e0e0;
  font-size: 1.2rem;
  text-align: center;
  font-family: inherit;
  outline: none;
  transition: border-color 0.3s;
  letter-spacing: 0.2rem;
}

.input-wrapper input:focus {
  border-color: #8b0000;
}

.input-wrapper input::placeholder {
  color: #444;
  font-size: 0.9rem;
  letter-spacing: 0.1rem;
}

.input-underline {
  position: absolute;
  bottom: 0;
  left: 50%;
  width: 0;
  height: 1px;
  background: #8b0000;
  transition: all 0.4s ease;
  transform: translateX(-50%);
  box-shadow: 0 0 8px rgba(139, 0, 0, 0.5);
}

.input-wrapper input:focus ~ .input-underline {
  width: 100%;
}

.confirm-btn {
  width: 100%;
  padding: 14px;
  background: linear-gradient(180deg, rgba(139, 0, 0, 0.8), rgba(74, 0, 0, 0.9));
  border: 1px solid rgba(255, 76, 76, 0.3);
  color: #fff;
  font-size: 1rem;
  font-family: inherit;
  letter-spacing: 0.5rem;
  cursor: pointer;
  transition: all 0.3s;
}

.confirm-btn:hover:not(:disabled) {
  box-shadow: 0 0 20px rgba(139, 0, 0, 0.4);
  border-color: rgba(255, 76, 76, 0.6);
}

.confirm-btn:active:not(:disabled) {
  transform: translateY(1px);
}

.confirm-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.loading-text span {
  animation: blink 1.4s infinite both;
}
.loading-text .dot:nth-child(4) { animation-delay: 0.2s; }
.loading-text .dot:nth-child(5) { animation-delay: 0.4s; }
.loading-text .dot:nth-child(6) { animation-delay: 0.6s; }

@keyframes blink {
  0%, 80%, 100% { opacity: 0.3; }
  40% { opacity: 1; }
}

.skip-hint {
  margin-top: 1.5rem;
  font-size: 0.75rem;
  color: #444;
  cursor: pointer;
  transition: color 0.3s;
}
.skip-hint:hover {
  color: #888;
}

/* ======== 页脚 ======== */
.home-footer {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  text-align: center;
  padding: 12px 0;
  z-index: 10;
}

.home-footer p {
  font-size: 0.7rem;
  color: #ff4c4c;
  opacity: 0.6;
  margin: 0;
  letter-spacing: 0.05rem;
}
</style>