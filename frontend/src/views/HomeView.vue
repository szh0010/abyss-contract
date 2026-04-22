<template>
  <div class="home">
    <div class="title-container">
      <h1 class="main-title">深 渊 契 约</h1>
      <p class="subtitle">ABYSS CONTRACT</p>
      <div class="divider"></div>
      <p class="tagline">"你已经没有什么可以失去的了，不是吗？"</p>
    </div>

    <div class="start-section">
      <div class="input-group">
        <label for="playerName">你的名字</label>
        <input
          id="playerName"
          v-model="playerName"
          type="text"
          placeholder="输入你的名字……"
          maxlength="20"
          @keyup.enter="startNewGame"
        />
      </div>
      <button class="start-btn" @click="startNewGame" :disabled="isLoading">
        <span v-if="!isLoading">踏 入 深 渊</span>
        <span v-else>正在连接……</span>
      </button>
      <p class="warning">* 本游戏为反赌博教育作品，所有赌博选项必将导致毁灭结局</p>
    </div>
  </div>
</template>

<script setup>
import { ref } from "vue"
import { useRouter } from "vue-router"
import { useGameStore } from "../stores/gameStore.js"

const router = useRouter()
const gameStore = useGameStore()
const playerName = ref("")
const isLoading = ref(false)

async function startNewGame() {
  isLoading.value = true
  try {
    await gameStore.initGame(playerName.value || "无名者")
    router.push("/game")
  } catch (err) {
    alert("连接服务器失败，请确认后端已启动。")
    console.error(err)
  } finally {
    isLoading.value = false
  }
}
</script>

<style scoped>
.home {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  padding: 2rem;
  animation: fadeIn 1.5s ease;
}

.title-container {
  text-align: center;
  margin-bottom: 3rem;
}

.main-title {
  font-size: 3.5rem;
  font-weight: 700;
  color: var(--abyss-red);
  letter-spacing: 1.5rem;
  text-shadow: 0 0 30px rgba(192, 57, 43, 0.4);
  margin-bottom: 0.5rem;
}

.subtitle {
  font-size: 0.9rem;
  color: var(--text-secondary);
  letter-spacing: 0.8rem;
  font-family: monospace;
}

.divider {
  width: 60px;
  height: 1px;
  background: var(--abyss-red);
  margin: 1.5rem auto;
  box-shadow: 0 0 10px rgba(192, 57, 43, 0.5);
}

.tagline {
  font-size: 1rem;
  color: var(--text-secondary);
  font-style: italic;
  margin-top: 1rem;
}

.start-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1.5rem;
}

.input-group {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
}

.input-group label {
  font-size: 0.85rem;
  color: var(--text-secondary);
}

.input-group input {
  width: 280px;
  padding: 0.8rem 1.2rem;
  background: var(--abyss-dark);
  border: 1px solid var(--abyss-border);
  color: var(--text-primary);
  font-size: 1rem;
  text-align: center;
  font-family: inherit;
  border-radius: 2px;
  outline: none;
  transition: border-color 0.3s;
}

.input-group input:focus {
  border-color: var(--abyss-red);
}

.input-group input::placeholder {
  color: var(--text-secondary);
  opacity: 0.5;
}

.start-btn {
  padding: 1rem 3rem;
  background: transparent;
  border: 1px solid var(--abyss-red);
  color: var(--abyss-red);
  font-size: 1.1rem;
  font-family: inherit;
  letter-spacing: 0.5rem;
  cursor: pointer;
  transition: all 0.3s ease;
  border-radius: 2px;
}

.start-btn:hover:not(:disabled) {
  background: var(--abyss-red);
  color: #fff;
  box-shadow: 0 0 20px rgba(192, 57, 43, 0.4);
}

.start-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.warning {
  font-size: 0.75rem;
  color: var(--text-secondary);
  opacity: 0.6;
  margin-top: 1rem;
}
</style>
