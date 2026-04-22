import axios from "axios"

const api = axios.create({
  baseURL: "/api/game",
  timeout: 10000,
  headers: { "Content-Type": "application/json" },
})

export async function startGame(playerName = "无名者") {
  const res = await api.post("/start", { player_name: playerName })
  return res.data
}

export async function makeChoice(sessionId, choice) {
  const res = await api.post("/choose", {
    session_id: sessionId,
    choice: choice,
  })
  return res.data
}

export async function getStatus(sessionId) {
  const res = await api.get("/status/" + sessionId)
  return res.data
}

export async function getCurrentStage(sessionId) {
  const res = await api.get("/stage/" + sessionId)
  return res.data
}

export default api
