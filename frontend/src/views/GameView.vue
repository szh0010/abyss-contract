<template>
  <div class="game-page">
    <header class="game-header">
      <h1 class="game-logo">深渊契约</h1>
      <span class="player-name">{{ gameStore.sessionId ? "进行中" : "未开始" }}</span>
    </header>

    <main class="game-main">
      <!-- 玩家状态栏 -->
      <PlayerStatus />

      <!-- AI 对话框 -->
      <GameDialogue @typing-done="onTypingDone" />

      <!-- 选项面板 -->
      <ChoicePanel v-if="showChoices" />

      <!-- 加载中 -->
      <div v-if="gameStore.isLoading" class="loading">
        <span class="loading-dot">.</span>
        <span class="loading-dot">.</span>
        <span class="loading-dot">.</span>
      </div>
    </main>

    <footer class="game-footer">
      <p>本游戏为反赌博教育作品 | 如遇金融诈骗请拨打 110 | 法律援助热线 12348</p>
    </footer>
  </div>
</template>

<script setup>
import { ref, computed } from "vue"
import { useGameStore } from "../stores/gameStore.js"
import PlayerStatus from "../components/PlayerStatus.vue"
import GameDialogue from "../components/GameDialogue.vue"
import ChoicePanel from "../components/ChoicePanel.vue"

const gameStore = useGameStore()
const typingFinished = ref(false)

const showChoices = computed(() => {
  return !gameStore.isLoading && typingFinished.value
})

function onTypingDone() {
  typingFinished.value = true
}
</script>

<style scoped>
.game-page {
  width: 100%;
  max-width: 800px;
  min-height: 100vh;
  margin: 0 auto;
  padding: 1rem 2rem;
  display: flex;
  flex-direction: column;
}

.game-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 0;
  border-bottom: 1px solid var(--abyss-border);
  margin-bottom: 1.5rem;
}

.game-logo {
  font-size: 1.3rem;
  color: var(--abyss-red);
  letter-spacing: 0.5rem;
  font-weight: 700;
}

.player-name {
  font-size: 0.8rem;
  color: var(--text-secondary);
}

.game-main {
  flex: 1;
  animation: fadeIn 0.8s ease;
}

/* 加载动画 */
.loading {
  text-align: center;
  padding: 2rem;
  font-size: 2rem;
  color: var(--text-secondary);
}

.loading-dot {
  animation: blink 1.4s infinite;
  animation-fill-mode: both;
}

.loading-dot:nth-child(2) {
  animation-delay: 0.2s;
}

.loading-dot:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes blink {
  0%, 80%, 100% { opacity: 0; }
  40% { opacity: 1; }
}

.game-footer {
  text-align: center;
  padding: 1.5rem 0;
  border-top: 1px solid var(--abyss-border);
  margin-top: 2rem;
}

.game-footer p {
  font-size: 0.75rem;
  color: var(--text-secondary);
  opacity: 0.5;
}
</style>
