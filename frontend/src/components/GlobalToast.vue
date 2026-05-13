<template>
  <teleport to="body">
    <div class="toast-stack" aria-live="polite">
      <transition-group name="toast">
        <div
          v-for="t in toasts"
          :key="t.id"
          class="toast liquid-surface"
          :class="`toast-${t.level}`"
          @click="dismissToast(t.id)"
        >
          <span class="toast-dot"></span>
          <span class="toast-msg">{{ t.message }}</span>
        </div>
      </transition-group>
    </div>
  </teleport>
</template>

<script setup>
import { toasts, dismissToast } from '../services/toast'
</script>

<style scoped>
.toast-stack {
  position: fixed;
  top: 24px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 9999;
  display: flex;
  flex-direction: column;
  gap: 10px;
  pointer-events: none;
}

.toast {
  pointer-events: auto;
  display: inline-flex;
  align-items: center;
  gap: 12px;
  min-width: 220px;
  max-width: 420px;
  padding: 12px 18px;
  border-radius: 18px;
  cursor: pointer;
  font-family: inherit;
  font-size: 0.88rem;
  font-weight: 500;
  letter-spacing: 0.02em;
  color: #2d2416;
  background: rgba(255, 253, 248, 0.78);
  backdrop-filter: blur(22px) saturate(180%);
  -webkit-backdrop-filter: blur(22px) saturate(180%);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.95),
    inset 0 0 0 0.5px rgba(255, 185, 120, 0.28),
    0 22px 60px rgba(200, 130, 60, 0.16),
    0 6px 16px rgba(180, 110, 50, 0.08);
}

.toast-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}
.toast-msg { line-height: 1.5; }

.toast-info    .toast-dot { background: #6ea8ff; box-shadow: 0 0 10px rgba(110, 168, 255, 0.5); }
.toast-success .toast-dot { background: #5fbf8a; box-shadow: 0 0 10px rgba(95, 191, 138, 0.5); }
.toast-warning .toast-dot { background: #f5a524; box-shadow: 0 0 10px rgba(245, 165, 36, 0.5); }
.toast-danger  .toast-dot { background: #d94a67; box-shadow: 0 0 10px rgba(217, 74, 103, 0.55); }

.toast-danger  { color: #8a2b3f; }
.toast-warning { color: #8a5d12; }
.toast-success { color: #2f6b4c; }

/* 弹簧进出 */
.toast-enter-active,
.toast-leave-active {
  transition:
    opacity 0.5s cubic-bezier(0.25, 1.5, 0.5, 1),
    transform 0.5s cubic-bezier(0.25, 1.5, 0.5, 1);
}
.toast-enter-from { opacity: 0; transform: translateY(-12px) scale(0.92); }
.toast-leave-to   { opacity: 0; transform: translateY(-6px) scale(0.96); }
.toast-move       { transition: transform 0.4s cubic-bezier(0.22, 1, 0.36, 1); }
</style>
