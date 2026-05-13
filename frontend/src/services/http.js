/**
 * 全局 axios 实例：
 *   - 自动带 Bearer Token
 *   - 401 自动登出 + 跳登录页
 *   - 401 / 409 / 500 等异常自动 Toast 提示
 *   - 登录/注册后同时持久化 token、用户对象与裸用户名（username），
 *     便于主界面直接读取展示（DiceBear 头像等）
 *   - 若 localStorage 里只剩 token，也能解析 JWT 的 sub 字段回落显示
 */
import axios from 'axios'
import router from '../router'
import { toast } from './toast'

const TOKEN_KEY = 'abyss_token'
const USER_KEY = 'abyss_user'
const USERNAME_KEY = 'abyss_username'

export function getToken() {
  return localStorage.getItem(TOKEN_KEY) || ''
}
export function setToken(t) {
  localStorage.setItem(TOKEN_KEY, t)
}
export function getUser() {
  try {
    return JSON.parse(localStorage.getItem(USER_KEY) || 'null')
  } catch {
    return null
  }
}
export function setUser(u) {
  localStorage.setItem(USER_KEY, JSON.stringify(u))
  if (u && typeof u.username === 'string') {
    localStorage.setItem(USERNAME_KEY, u.username)
  }
}

/**
 * 读取当前用户名：
 *   1) 优先 abyss_username（登录成功时写入）
 *   2) 回落 abyss_user.username
 *   3) 再回落解析 JWT 的 sub 字段
 *   4) 都没有则返回空字符串
 */
export function getUsername() {
  const direct = localStorage.getItem(USERNAME_KEY)
  if (direct) return direct
  const u = getUser()
  if (u?.username) return u.username
  const sub = decodeJwtSub(getToken())
  return sub || ''
}

export function setUsername(name) {
  if (name) localStorage.setItem(USERNAME_KEY, name)
}

/** 解析 JWT 的 sub 字段（不校验签名，纯前端展示用）。 */
export function decodeJwtSub(token) {
  if (!token || typeof token !== 'string') return ''
  const parts = token.split('.')
  if (parts.length < 2) return ''
  try {
    const payload = parts[1].replace(/-/g, '+').replace(/_/g, '/')
    const padded = payload + '==='.slice((payload.length + 3) % 4)
    const json = decodeURIComponent(
      atob(padded)
        .split('')
        .map((c) => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
        .join('')
    )
    return JSON.parse(json)?.sub || ''
  } catch {
    return ''
  }
}

export function clearAuth() {
  localStorage.removeItem(TOKEN_KEY)
  localStorage.removeItem(USER_KEY)
  localStorage.removeItem(USERNAME_KEY)
}

const http = axios.create({
  baseURL: '/api',
  timeout: 20000,
})

// 请求拦截：注入 Authorization
http.interceptors.request.use((config) => {
  const token = getToken()
  if (token) {
    config.headers = config.headers || {}
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// 静默路径：这些接口自己处理错误提示，不要全局 toast
const SILENT_PATHS = ['/auth/login', '/auth/register']
function isSilent(config) {
  if (!config?.url) return false
  return SILENT_PATHS.some((p) => config.url.includes(p))
}

// 响应拦截：状态码统一 toast + 401 跳登录
http.interceptors.response.use(
  (res) => res,
  (err) => {
    const status = err?.response?.status
    const detail = err?.response?.data?.detail
    const silent = isSilent(err?.config)

    if (status === 401) {
      clearAuth()
      const current = router.currentRoute.value
      if (current.name !== 'Login') {
        if (!silent) toast.danger('密码错误或账号不存在')
        router.replace({
          name: 'Login',
          query: { redirect: current.fullPath },
        })
      } else if (!silent) {
        toast.danger('密码错误或账号不存在')
      }
    } else if (status === 409) {
      if (!silent) toast.warning(detail || '用户名已被占用')
    } else if (status === 403) {
      if (!silent) toast.warning(detail || '没有访问权限')
    } else if (status === 404) {
      if (!silent) toast.warning(detail || '资源不存在')
    } else if (status && status >= 500) {
      if (!silent) toast.danger('服务器异常，请稍后重试')
    } else if (!status && err?.message) {
      // 网络层错误（超时 / 断网 / CORS）
      if (!silent) toast.danger('网络异常，请检查连接')
    }

    return Promise.reject(err)
  }
)

export default http
