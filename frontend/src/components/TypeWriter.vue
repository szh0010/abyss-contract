<template>
  <div class="typewriter">
    <span>{{ displayedText }}</span>
    <span v-if="isTyping" class="cursor">|</span>
  </div>
</template>

<script setup>
import { ref, watch, onUnmounted } from "vue"

const props = defineProps({
  text: { type: String, required: true },
  speed: { type: Number, default: 40 },
})

const emit = defineEmits(["done"])
const displayedText = ref("")
const isTyping = ref(false)
let timer = null

function startTyping() {
  displayedText.value = ""
  isTyping.value = true
  let index = 0

  if (timer) clearInterval(timer)

  timer = setInterval(() => {
    if (index < props.text.length) {
      displayedText.value += props.text[index]
      index++
    } else {
      clearInterval(timer)
      isTyping.value = false
      emit("done")
    }
  }, props.speed)
}

watch(() => props.text, () => {
  startTyping()
}, { immediate: true })

onUnmounted(() => {
  if (timer) clearInterval(timer)
})
</script>

<style scoped>
.typewriter {
  white-space: pre-wrap;
  word-break: break-word;
}
.cursor {
  color: var(--abyss-red);
  animation: blink 1s step-end infinite;
}
@keyframes blink {
  50% { opacity: 0; }
}
</style>
