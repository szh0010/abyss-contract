/**
 * 全局 Toast：轻量响应式队列 + push()/dismiss()
 * - 不引入任何第三方库，保持极简悬浮岛风格
 * - 由 <GlobalToast /> 组件订阅 toasts 进行渲染
 */
import { reactive } from 'vue'

export const toasts = reactive([])

let _seq = 0

/**
 * 推入一条 toast。
 * @param {string} message 提示文案
 * @param {'info'|'success'|'warning'|'danger'} level 语义级别
 * @param {number} duration 自动消失毫秒数，0 表示不自动消失
 */
export function pushToast(message, level = 'info', duration = 3200) {
  if (!message) return
  const id = ++_seq
  toasts.push({ id, message, level })
  if (duration > 0) {
    setTimeout(() => dismissToast(id), duration)
  }
  return id
}

export function dismissToast(id) {
  const idx = toasts.findIndex((t) => t.id === id)
  if (idx >= 0) toasts.splice(idx, 1)
}

// 语义快捷方法
export const toast = {
  info: (m, d) => pushToast(m, 'info', d),
  success: (m, d) => pushToast(m, 'success', d),
  warning: (m, d) => pushToast(m, 'warning', d),
  danger: (m, d) => pushToast(m, 'danger', d),
}
