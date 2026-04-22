import { defineStore } from "pinia"
import { ref, computed } from "vue"
import { startGame, makeChoice, getCurrentStage } from "../services/api.js"

export const useGameStore = defineStore("game", () => {
  // ===== State =====
  const sessionId = ref(null)
  const stageNumber = ref(0)
  const stageTitle = ref("")
  const kDialogue = ref("")
  const optionA = ref("")
  const optionB = ref("")
  const debt = ref(500000)
  const greed = ref(0)
  const mentalState = ref("清醒")
  const isGameOver = ref(false)
  const endingType = ref(null)
  const isLoading = ref(false)
  const kResponse = ref("")
  const showResponse = ref(false)
  const history = ref([])

  // ===== Computed =====
  const debtFormatted = computed(() => {
    return "" + debt.value.toLocaleString("zh-CN")
  })

  const greedPercent = computed(() => {
    return Math.min(greed.value, 100)
  })

  const mentalColor = computed(() => {
    const colors = {
      "清醒": "#27ae60",
      "动摇": "#f39c12",
      "迷失": "#e67e22",
      "失控": "#e74c3c",
    }
    return colors[mentalState.value] || "#e0e0e0"
  })

  // ===== Actions =====
  async function initGame(playerName) {
    isLoading.value = true
    try {
      const data = await startGame(playerName)
      sessionId.value = data.session_id
      stageNumber.value = data.stage_number
      stageTitle.value = data.stage_title
      kDialogue.value = data.k_dialogue
      optionA.value = data.option_a
      optionB.value = data.option_b
      debt.value = data.player_debt
      greed.value = data.player_greed
      mentalState.value = data.player_mental_state
      isGameOver.value = false
      endingType.value = null
      showResponse.value = false
      history.value = []
    } finally {
      isLoading.value = false
    }
  }

  async function choose(choice) {
    if (!sessionId.value || isGameOver.value) return
    isLoading.value = true
    try {
      const result = await makeChoice(sessionId.value, choice)

      history.value.push({
        stage: stageNumber.value,
        title: stageTitle.value,
        choice: choice,
        choiceText: choice === "A" ? optionA.value : optionB.value,
      })

      kResponse.value = result.k_response
      debt.value = result.new_debt
      greed.value = result.new_greed
      mentalState.value = result.new_mental_state
      isGameOver.value = result.is_game_over
      endingType.value = result.ending_type
      showResponse.value = true

      if (!result.is_game_over && result.next_stage) {
        const stageData = await getCurrentStage(sessionId.value)
        stageNumber.value = stageData.stage_number
        stageTitle.value = stageData.stage_title
        kDialogue.value = stageData.k_dialogue
        optionA.value = stageData.option_a
        optionB.value = stageData.option_b
      }
    } finally {
      isLoading.value = false
    }
  }

  function continueToNextStage() {
    showResponse.value = false
  }

  return {
    sessionId, stageNumber, stageTitle, kDialogue,
    optionA, optionB, debt, greed, mentalState,
    isGameOver, endingType, isLoading, kResponse,
    showResponse, history,
    debtFormatted, greedPercent, mentalColor,
    initGame, choose, continueToNextStage,
  }
})
