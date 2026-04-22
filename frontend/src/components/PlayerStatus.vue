<template>
  <div class="status-bar">
    <div class="status-item">
      <span class="label">债务</span>
      <span class="value debt">{{ gameStore.debtFormatted }}</span>
    </div>
    <div class="status-item">
      <span class="label">贪婪值</span>
      <div class="greed-bar">
        <div
          class="greed-fill"
          :style="{ width: gameStore.greedPercent + '%' }"
        ></div>
      </div>
      <span class="value greed">{{ gameStore.greed }}/100</span>
    </div>
    <div class="status-item">
      <span class="label">精神状态</span>
      <span class="value" :style="{ color: gameStore.mentalColor }">
        {{ gameStore.mentalState }}
      </span>
    </div>
    <div class="status-item">
      <span class="label">阶段</span>
      <span class="value">{{ gameStore.stageNumber }} / 5</span>
    </div>
  </div>
</template>

<script setup>
import { useGameStore } from "../stores/gameStore.js"
const gameStore = useGameStore()
</script>

<style scoped>
.status-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 1.5rem;
  background: var(--abyss-dark);
  border: 1px solid var(--abyss-border);
  border-radius: 2px;
  margin-bottom: 1.5rem;
  gap: 1.5rem;
  flex-wrap: wrap;
}
.status-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}
.label {
  font-size: 0.8rem;
  color: var(--text-secondary);
}
.value {
  font-size: 0.95rem;
  font-weight: 700;
}
.debt {
  color: var(--abyss-red-glow);
}
.greed {
  font-size: 0.8rem;
  color: var(--text-warning);
}
.greed-bar {
  width: 80px;
  height: 6px;
  background: var(--abyss-gray);
  border-radius: 3px;
  overflow: hidden;
}
.greed-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--abyss-gold-dim), var(--abyss-red));
  border-radius: 3px;
  transition: width 0.8s ease;
}
</style>
