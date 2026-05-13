<template>
  <div class="login-page">
    <transition name="card-swap" mode="out-in">
      <div class="auth-card" :key="mode">
        <div class="brand">
          <div class="brand-mark">
            <span class="mark-dot"></span>
          </div>
          <div class="brand-name">反诈先锋</div>
          <div class="brand-sub">
            {{ mode === 'login' ? 'Welcome back · 守护每一个正直的你' : '创建账户 · 加入守护者行列' }}
          </div>
        </div>

        <form class="form" @submit.prevent="submit">
          <div class="field">
            <label class="field-label">用户名</label>
            <input
              v-model="username"
              type="text"
              autocomplete="username"
              maxlength="50"
              :placeholder="mode === 'login' ? '输入用户名' : '至少 2 个字符'"
              class="field-input"
            />
            <span class="field-glow"></span>
          </div>

          <div class="field">
            <label class="field-label">密码</label>
            <input
              v-model="password"
              type="password"
              :autocomplete="mode === 'login' ? 'current-password' : 'new-password'"
              maxlength="128"
              :placeholder="mode === 'login' ? '输入密码' : '至少 6 位'"
              class="field-input"
              @keyup.enter="submit"
            />
            <span class="field-glow"></span>
          </div>

          <transition name="err">
            <p v-if="errorMsg" class="err-msg">{{ errorMsg }}</p>
          </transition>

          <button class="submit-btn" :disabled="busy" type="submit">
            <transition name="btn-swap" mode="out-in">
              <span v-if="!busy" :key="mode" class="submit-label">
                {{ mode === 'login' ? '登 录' : '创建账户' }}
              </span>
              <span v-else key="busy" class="dots"><i></i><i></i><i></i></span>
            </transition>
          </button>
        </form>

        <div class="switch-row">
          <span class="switch-text">
            {{ mode === 'login' ? '还没有账号？' : '已有账号？' }}
          </span>
          <button class="switch-btn" type="button" @click="toggleMode">
            {{ mode === 'login' ? '立即注册' : '返回登录' }}
          </button>
        </div>
      </div>
    </transition>

    <p class="tiny-tip">JWT 会话 · 7 天内免登录</p>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import http, { setToken, setUser, setUsername } from '../services/http'
import { toast } from '../services/toast'

const router = useRouter()
const route = useRoute()

const mode = ref('login')
const username = ref('')
const password = ref('')
const busy = ref(false)
const errorMsg = ref('')

function toggleMode() {
  mode.value = mode.value === 'login' ? 'register' : 'login'
  errorMsg.value = ''
}

async function submit() {
  errorMsg.value = ''
  const u = username.value.trim()
  const p = password.value
  if (u.length < 2) return (errorMsg.value = '用户名至少 2 位')
  if (p.length < 6) return (errorMsg.value = '密码至少 6 位')

  busy.value = true
  try {
    const path = mode.value === 'login' ? '/auth/login' : '/auth/register'
    const { data } = await http.post(path, { username: u, password: p })
    setToken(data.access_token)
    setUser(data.user)
    setUsername(data.user?.username || u)
    toast.success(mode.value === 'login' ? `欢迎回来，${data.user?.username || u}` : '账号创建成功')
    const redirect = route.query.redirect || '/chat'
    router.replace(redirect)
  } catch (e) {
    const status = e?.response?.status
    const detail = e?.response?.data?.detail
    if (status === 401) {
      errorMsg.value = '密码错误或账号不存在'
    } else if (status === 409) {
      errorMsg.value = '用户名已被占用'
    } else if (status && status >= 500) {
      errorMsg.value = '服务器异常，请稍后重试'
    } else {
      errorMsg.value = detail || '网络异常，请稍后重试'
    }
    toast.danger(errorMsg.value)
  } finally {
    busy.value = false
  }
}
</script>

<style scoped>
/* ============================================================
   登录页（aurora 继承自 App.vue 全站层）
============================================================ */
.login-page {
  position: relative;
  z-index: 1;
  min-height: 100vh;
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 24px;
  font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'SF Pro Text',
               'Inter', 'PingFang SC', 'Helvetica Neue', sans-serif;
}

/* 液态玻璃卡片 */
.auth-card {
  position: relative;
  width: min(420px, 92%);
  padding: 44px 40px 32px;
  border-radius: 32px;
  background: rgba(255, 253, 248, 0.62);
  backdrop-filter: blur(28px) saturate(180%);
  -webkit-backdrop-filter: blur(28px) saturate(180%);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.95),
    inset 0 -0.5px 0 rgba(255, 255, 255, 0.4),
    inset 0 0 0 0.5px rgba(255, 185, 120, 0.22),
    0 34px 80px rgba(200, 130, 70, 0.18),
    0 6px 18px rgba(180, 110, 50, 0.08);
}

/* iOS 丝滑切换 login ↔ register */
.card-swap-enter-active,
.card-swap-leave-active {
  transition: opacity 0.42s cubic-bezier(0.22, 1, 0.36, 1),
              transform 0.42s cubic-bezier(0.22, 1, 0.36, 1),
              filter 0.42s ease;
}
.card-swap-enter-from {
  opacity: 0;
  transform: translateY(8px) scale(0.985);
  filter: blur(6px);
}
.card-swap-leave-to {
  opacity: 0;
  transform: translateY(-6px) scale(0.995);
  filter: blur(3px);
}

/* ============================================================
   品牌
============================================================ */
.brand {
  text-align: center;
  margin-bottom: 36px;
}
.brand-mark {
  width: 44px;
  height: 44px;
  margin: 0 auto 18px;
  border-radius: 14px;
  background: linear-gradient(135deg, #ffb578 0%, #ff7a50 100%);
  box-shadow:
    0 12px 30px rgba(255, 122, 80, 0.35),
    inset 0 1px 0 rgba(255, 255, 255, 0.45);
  display: flex;
  align-items: center;
  justify-content: center;
}
.mark-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.92);
  box-shadow: 0 0 12px rgba(255, 255, 255, 0.7);
}
.brand-name {
  font-size: 1.28rem;
  font-weight: 500;
  letter-spacing: 0.25em;
  color: #2d2416;
  margin-bottom: 8px;
}
.brand-sub {
  font-size: 0.8rem;
  font-weight: 400;
  letter-spacing: 0.04em;
  color: #7e6a4f;
}

/* ============================================================
   表单
============================================================ */
.form {
  display: flex;
  flex-direction: column;
  gap: 22px;
}

.field {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.field-label {
  font-size: 0.7rem;
  font-weight: 500;
  letter-spacing: 0.16em;
  color: #7e6a4f;
  padding-left: 2px;
  text-transform: uppercase;
}
.field-input {
  width: 100%;
  padding: 10px 2px;
  border: none;
  outline: none;
  background: transparent;
  color: #2d2416;
  font-family: inherit;
  font-size: 0.98rem;
  font-weight: 400;
  letter-spacing: 0.01em;
  border-bottom: 1px solid rgba(180, 130, 80, 0.22);
  transition: border-color 0.3s ease;
}
.field-input::placeholder {
  color: #b8a583;
  font-weight: 300;
}
.field-input:focus {
  border-bottom-color: rgba(255, 122, 80, 0.6);
}
.field-glow {
  position: absolute;
  bottom: 0; left: 0; right: 0;
  height: 1.5px;
  background: linear-gradient(90deg, transparent, #ff7a50, transparent);
  opacity: 0;
  transform: scaleX(0.4);
  transition: opacity 0.35s ease, transform 0.35s ease;
  pointer-events: none;
}
.field:focus-within .field-glow {
  opacity: 1;
  transform: scaleX(1);
}

/* 错误 */
.err-msg {
  margin: -4px 0;
  padding: 10px 14px;
  font-size: 0.78rem;
  color: #a8334a;
  background: rgba(217, 74, 103, 0.1);
  border-radius: 12px;
  font-weight: 400;
  box-shadow: inset 0 0 0 0.5px rgba(217, 74, 103, 0.2);
}
.err-enter-active, .err-leave-active { transition: all 0.3s cubic-bezier(0.22, 1, 0.36, 1); }
.err-enter-from, .err-leave-to { opacity: 0; transform: translateY(-4px); }

/* ============================================================
   提交按钮 · 液态玻璃 + 弹簧阻力
============================================================ */
.submit-btn {
  margin-top: 10px;
  position: relative;
  width: 100%;
  height: 48px;
  border: none;
  border-radius: 16px;
  color: #fff;
  font-size: 0.92rem;
  font-weight: 500;
  letter-spacing: 0.3em;
  font-family: inherit;
  cursor: pointer;
  overflow: hidden;
  background: linear-gradient(135deg, #ffb578 0%, #ff7a50 100%);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.48),
    inset 0 0 0 0.5px rgba(255, 200, 160, 0.6),
    0 16px 38px rgba(255, 122, 80, 0.42),
    0 4px 10px rgba(200, 100, 60, 0.12);
  transition: transform 0.4s cubic-bezier(0.25, 1.5, 0.5, 1),
              box-shadow 0.3s cubic-bezier(0.4, 0, 0.2, 1),
              opacity 0.2s;
}
.submit-btn:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.55),
    0 22px 52px rgba(255, 122, 80, 0.55),
    0 6px 14px rgba(200, 100, 60, 0.18);
}
.submit-btn:active:not(:disabled) {
  transform: scale(0.92);
  transition: all 0.4s cubic-bezier(0.25, 1.5, 0.5, 1);
}
.submit-btn:disabled { opacity: 0.6; cursor: not-allowed; }

.submit-label { display: inline-block; }
.btn-swap-enter-active, .btn-swap-leave-active {
  transition: opacity 0.25s ease, transform 0.25s cubic-bezier(0.22, 1, 0.36, 1);
}
.btn-swap-enter-from { opacity: 0; transform: translateY(6px); }
.btn-swap-leave-to   { opacity: 0; transform: translateY(-6px); }

.dots { display: inline-flex; gap: 6px; }
.dots i {
  width: 6px; height: 6px; border-radius: 50%; background: #fff;
  animation: blink 1.2s infinite ease-in-out;
}
.dots i:nth-child(2) { animation-delay: 0.15s; }
.dots i:nth-child(3) { animation-delay: 0.3s; }
@keyframes blink {
  0%, 80%, 100% { opacity: 0.3; transform: scale(0.85); }
  40%           { opacity: 1;   transform: scale(1); }
}

/* ============================================================
   切换 / 底部提示
============================================================ */
.switch-row {
  margin-top: 22px;
  text-align: center;
  font-size: 0.82rem;
  font-weight: 400;
}
.switch-text { color: #7e6a4f; }
.switch-btn {
  background: none;
  border: none;
  color: #ff7a50;
  font-size: inherit;
  font-family: inherit;
  font-weight: 600;
  padding: 0 4px;
  cursor: pointer;
  letter-spacing: 0.04em;
  transition: color 0.25s;
}
.switch-btn:hover { color: #e05930; }

.tiny-tip {
  position: relative;
  margin-top: 26px;
  font-size: 0.7rem;
  letter-spacing: 0.18em;
  font-weight: 400;
  color: #b8a583;
  z-index: 2;
}
</style>
