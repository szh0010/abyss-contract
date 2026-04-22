<template>
  <div class="choice-panel">
    <template v-if="gameStore.isGameOver">
      <div class="ending-box" :class="gameStore.endingType">
        <h2 v-if="gameStore.endingType === 'abyss'">- 深渊结局：万劫不复 -</h2>
        <h2 v-else>- 新生结局：破晓之光 -</h2>
        <button class="restart-btn" @click="restart">重新开始</button>
      </div>
    </template>

    <template v-else-if="gameStore.showResponse">
      <button class="continue-btn" @click="gameStore.continueToNextStage()">
        继续 >>>
      </button>
    </template>

    <template v-else>
      <p class="choice-hint">你的选择将决定命运的走向……</p>
      <div class="choices">
        <button
          class="choice-btn choice-a"
          @click="gameStore.choose('A')"
          :disabled="gameStore.isLoading"
        >
          <span class="choice-label">A</span>
          <span class="choice-text">{{ gameStore.optionA }}</span>
        </button>
        <button
          class="choice-btn choice-b"
          @click="gameStore.choose('B')"
          :disabled="gameStore.isLoading"
        >
          <span class="choice-label">B</span>
          <span class="choice-text">{{ gameStore.optionB }}</span>
        </button>
      </div>
    </template>
  </div>
</template>

<script setup>
import { useRouter } from "vue-router"
import { useGameStore } from "../stores/gameStore.js"

const router = useRouter()
const gameStore = useGameStore()

function restart() {
  router.push("/")
}
</script>

<style scoped>
.choice-panel {
  animation: fadeIn 0.5s ease;
}
.choice-hint {
  text-align: center;
  font-size: 0.85rem;
  color: var(--text-secondary);
  margin-bottom: 1rem;
}
.choices {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}
.choice-btn {
  display: flex;
  align-items: center;
  gap: 1rem;
  width: 100%;
  padding: 1rem 1.5rem;
  background: var(--abyss-dark);
  border: 1px solid var(--abyss-border);
  color: var(--text-primary);
  font-size: 0.95rem;
  font-family: inherit;
  text-align: left;
  cursor: pointer;
  transition: all 0.3s ease;
  border-radius: 2px;
  line-height: 1.6;
}
.choice-btn:hover:not(:disabled) {
  transform: translateX(5px);
}
.choice-a:hover:not(:disabled) {
  border-color: var(--abyss-red);
  box-shadow: 0 0 15px rgba(192, 57, 43, 0.2);
}
.choice-b:hover:not(:disabled) {
  border-color: var(--abyss-green);
  box-shadow: 0 0 15px rgba(39, 174, 96, 0.2);
}
.choice-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.choice-label {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 0.85rem;
  border-radius: 2px;
  flex-shrink: 0;
}
.choice-a .choice-label {
  background: rgba(192, 57, 43, 0.2);
  color: var(--abyss-red-glow);
  border: 1px solid var(--abyss-red);
}
.choice-b .choice-label {
  background: rgba(39, 174, 96, 0.2);
  color: var(--abyss-green);
  border: 1px solid var(--abyss-green);
}
.choice-text {
  flex: 1;
}

/* 继续按钮 */
.continue-btn {
  display: block;
  width: 100%;
  padding: 1rem;
  background: transparent;
  border: 1px solid var(--abyss-border);
  color: var(--text-secondary);
  font-size: 1rem;
  font-family: inherit;
  cursor: pointer;
  transition: all 0.3s;
  letter-spacing: 0.3rem;
  border-radius: 2px;
}
.continue-btn:hover {
  color: var(--text-primary);
  border-color: var(--abyss-gold);
}

/* 结局样式 */
.ending-box {
  text-align: center;
  padding: 2rem;
  border: 1px solid var(--abyss-border);
  border-radius: 2px;
  animation: fadeIn 1s ease;
}
.ending-box.abyss {
  border-color: var(--abyss-red);
  background: rgba(192, 57, 43, 0.05);
}
.ending-box.abyss h2 {
  color: var(--abyss-red);
  text-shadow: 0 0 20px rgba(192, 57, 43, 0.5);
}
.ending-box.rebirth {
  border-color: var(--abyss-green);
  background: rgba(39, 174, 96, 0.05);
}
.ending-box.rebirth h2 {
  color: var(--abyss-green);
  text-shadow: 0 0 20px rgba(39, 174, 96, 0.5);
}
.restart-btn {
  margin-top: 1.5rem;
  padding: 0.8rem 2.5rem;
  background: transparent;
  border: 1px solid var(--text-secondary);
  color: var(--text-secondary);
  font-size: 0.9rem;
  font-family: inherit;
  cursor: pointer;
  transition: all 0.3s;
  border-radius: 2px;
  letter-spacing: 0.3rem;
}
.restart-btn:hover {
  color: var(--text-primary);
  border-color: var(--text-primary);
}
</style>
