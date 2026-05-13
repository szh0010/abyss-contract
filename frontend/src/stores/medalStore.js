/**
 * 全局勋章状态：Pinia + localStorage 持久化
 *
 * - 关键诉求：主大厅的勋章墙必须实时反映游戏内的解锁
 * - 多用户隔离：按 abyss_username 分表存储，不同账号互不干扰
 * - 数据形态对齐 App.vue 已有的 medal 渲染逻辑：
 *     { id, name, icon, tier, unlocked }
 *   icon 字段保留两种约定：
 *     1) 单字符（emoji 或字母）→ 直接当 emoji 渲染（覆盖 SVG）
 *     2) 已知 SVG 关键词（shield/star/eye/bolt）→ 走旧的 SVG 路径
 *   两种约定在 App.vue 里会一起兼容。
 */
import { defineStore } from 'pinia'
import { ref, computed, watch } from 'vue'
import { getUsername } from '../services/http'

const KEY_PREFIX = 'abyss_medals::'

function storageKey(username) {
  return KEY_PREFIX + (username || '__guest__')
}

function load(username) {
  try {
    const raw = localStorage.getItem(storageKey(username))
    if (!raw) return []
    const parsed = JSON.parse(raw)
    return Array.isArray(parsed) ? parsed : []
  } catch {
    return []
  }
}

function save(username, list) {
  try {
    localStorage.setItem(storageKey(username), JSON.stringify(list))
  } catch {
    /* quota exceeded etc. — 静默 */
  }
}

export const useMedalStore = defineStore('medals', () => {
  const currentUser = ref(getUsername())
  const medals = ref(load(currentUser.value))

  const unlockedMedals = computed(() => medals.value.filter((m) => m.unlocked))
  const unlockedCount = computed(() => unlockedMedals.value.length)

  // 写入即持久化
  watch(
    medals,
    (v) => save(currentUser.value, v),
    { deep: true }
  )

  /** 切换登录用户时重新加载，避免 A 用户的勋章渗到 B 账号。 */
  function syncWithCurrentUser() {
    const next = getUsername()
    if (next !== currentUser.value) {
      currentUser.value = next
      medals.value = load(next)
    }
  }

  /**
   * 解锁一枚勋章；已存在则只把 unlocked 置 true（幂等）。
   * @returns {boolean} true=新增解锁；false=已经解锁过
   */
  function unlock(medal) {
    if (!medal?.id) return false
    const existing = medals.value.find((m) => m.id === medal.id)
    if (existing) {
      if (existing.unlocked) return false
      existing.unlocked = true
      existing.acquired_at = new Date().toISOString()
      return true
    }
    medals.value.push({
      tier: 'gold',
      unlocked: true,
      acquired_at: new Date().toISOString(),
      ...medal,
    })
    return true
  }

  /** 仅供调试 / 重置使用。 */
  function clearAll() {
    medals.value = []
  }

  return {
    medals,
    unlockedMedals,
    unlockedCount,
    unlock,
    clearAll,
    syncWithCurrentUser,
  }
})
