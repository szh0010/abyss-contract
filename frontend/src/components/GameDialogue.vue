<template>
  <div class="dialogue-container">
    <div class="dialogue-header">
      <span class="speaker-icon">K</span>
      <span class="speaker-name">代理人 K</span>
      <span class="stage-badge">{{ gameStore.stageTitle }}</span>
    </div>
    <div class="dialogue-body">
      <TypeWriter
        :text="dialogueText"
        :speed="35"
        @done="onTypingDone"
      />
    </div>
  </div>
</template>

<script setup>
import { computed } from "vue"
import { useGameStore } from "../stores/gameStore.js"
import TypeWriter from "./TypeWriter.vue"

const gameStore = useGameStore()
const emit = defineEmits(["typingDone"])

const dialogueText = computed(() => {
  if (gameStore.showResponse) {
    return gameStore.kResponse
  }
  return gameStore.kDialogue
})

function onTypingDone() {
  emit("typingDone")
}
</script>

<style scoped>
.dialogue-container {
  background: var(--abyss-dark);
  border: 1px solid var(--abyss-border);
  border-left: 3px solid var(--abyss-red);
  border-radius: 2px;
  margin-bottom: 1.5rem;
  animation: fadeIn 0.6s ease;
}
.dialogue-header {
  display: flex;
  align-items: center;
  gap: 0.8rem;
  padding: 0.8rem 1.2rem;
  border-bottom: 1px solid var(--abyss-border);
}
.speaker-icon {
  width: 32px;
  height: 32px;
  background: var(--abyss-red);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 0.9rem;
  border-radius: 2px;
}
.speaker-name {
  font-size: 0.95rem;
  color: var(--text-primary);
  font-weight: 700;
}
.stage-badge {
  margin-left: auto;
  font-size: 0.75rem;
  color: var(--text-secondary);
  border: 1px solid var(--abyss-border);
  padding: 0.2rem 0.6rem;
  border-radius: 2px;
}
.dialogue-body {
  padding: 1.5rem;
  font-size: 1rem;
  line-height: 2;
  min-height: 200px;
  max-height: 450px;
  overflow-y: auto;
}
</style>
