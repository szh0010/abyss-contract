<template>
  <div id="abyss-app" :class="{ 'game-mode': isGameMode }">
    <!-- ========== 游戏全屏模式（序章/牌局） ========== -->
    <template v-if="isGameMode">
      <div class="noise-overlay"></div>
      <router-view v-slot="{ Component }">
        <transition name="page-fade" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </template>

    <!-- ========== 平台模式（侧边栏 + 主区域） ========== -->
    <template v-else>
      <!-- 侧边栏 -->
      <aside class="sidebar">
        <div class="sidebar-top">
          <!-- Logo -->
          <div class="logo-area">
            <div class="logo-icon">
              <svg viewBox="0 0 32 32" width="28" height="28">
                <circle cx="16" cy="16" r="14" fill="none" stroke="currentColor" stroke-width="2"/>
                <path d="M10 20 L16 10 L22 20 Z" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round"/>
              </svg>
            </div>
            <div class="logo-text">
              <span class="logo-title">反诈先锋</span>
              <span class="logo-sub">Anti-Fraud Guardian</span>
            </div>
          </div>

          <!-- 导航菜单 -->
          <nav class="nav-menu">
            <router-link to="/chat" class="nav-item" active-class="nav-active">
              <span class="nav-icon">💬</span>
              <span class="nav-label">智能对话</span>
            </router-link>
            <router-link to="/link-check" class="nav-item" active-class="nav-active">
              <span class="nav-icon">🔗</span>
              <span class="nav-label">链接研判</span>
            </router-link>
            <router-link to="/simulation" class="nav-item" active-class="nav-active">
              <span class="nav-icon">🎮</span>
              <span class="nav-label">情景模拟</span>
              <span class="nav-badge">深渊契约</span>
            </router-link>
          </nav>
        </div>

        <!-- 底部：用户积分/勋章 -->
        <div class="sidebar-bottom">
          <div class="user-stats">
            <div class="stat-row">
              <span class="stat-icon">⭐</span>
              <span class="stat-name">防诈积分</span>
              <span class="stat-val">{{ userScore }}</span>
            </div>
            <div class="stat-row">
              <span class="stat-icon">🛡️</span>
              <span class="stat-name">勋章</span>
              <span class="stat-val badge-val" v-if="hasBadge">防诈先锋</span>
              <span class="stat-val badge-none" v-else>未获得</span>
            </div>
          </div>
          <div class="sidebar-footer">
            <span class="footer-text">反诈热线 96110</span>
          </div>
        </div>
      </aside>

      <!-- 主内容区 -->
      <main class="main-content">
        <router-view v-slot="{ Component }">
          <transition name="content-fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </main>
    </template>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()

const userScore = ref(120)
const hasBadge = ref(false)

const isGameMode = computed(() => {
  const gamePaths = ['/', '/game']
  return gamePaths.includes(route.path)
})
</script>

<style>
/* ======== 全局重置 ======== */
* { margin:0; padding:0; box-sizing:border-box; }

#abyss-app {
  position: relative;
  min-height: 100vh;
  display: flex;
  background: #f8f9fc;
}

#abyss-app.game-mode {
  display: block;
  background: #000;
}

/* ======== 游戏模式噪点 ======== */
.noise-overlay {
  position: fixed;
  inset: 0;
  background-image: url('data:image/svg+xml,%3Csvg viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg"%3E%3Cfilter id="noiseFilter"%3E%3CfeTurbulence type="fractalNoise" baseFrequency="0.65" numOctaves="3" stitchTiles="stitch"/%3E%3C/filter%3E%3Crect width="100%25" height="100%25" filter="url(%23noiseFilter)"/%3E%3C/svg%3E');
  opacity: 0.03;
  pointer-events: none;
  z-index: 0;
}

/* ======== 侧边栏 ======== */
.sidebar {
  width: 260px;
  height: 100vh;
  position: fixed;
  left: 0;
  top: 0;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  background: linear-gradient(180deg, #1a1f36 0%, #0f1225 100%);
  border-right: 1px solid rgba(99, 115, 255, 0.15);
  padding: 24px 16px;
  z-index: 100;
  overflow-y: auto;
}

.sidebar-top {
  flex: 1;
}

/* Logo */
.logo-area {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 12px;
  margin-bottom: 32px;
}

.logo-icon {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #6366f1, #4f46e5);
  border-radius: 10px;
  color: #fff;
  box-shadow: 0 4px 15px rgba(99, 102, 241, 0.4);
}

.logo-text {
  display: flex;
  flex-direction: column;
}

.logo-title {
  font-size: 1.1rem;
  font-weight: 700;
  color: #e8eaff;
  letter-spacing: 0.15rem;
}

.logo-sub {
  font-size: 0.6rem;
  color: #6b7280;
  letter-spacing: 0.05rem;
  font-family: 'Courier New', monospace;
}

/* 导航菜单 */
.nav-menu {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  border-radius: 10px;
  color: #9ca3af;
  text-decoration: none;
  font-size: 0.9rem;
  transition: all 0.25s ease;
  position: relative;
}

.nav-item:hover {
  background: rgba(99, 102, 241, 0.1);
  color: #c7caff;
}

.nav-item.nav-active {
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.2), rgba(79, 70, 229, 0.15));
  color: #a5b4fc;
  font-weight: 600;
  box-shadow: inset 0 0 0 1px rgba(99, 102, 241, 0.3);
}

.nav-item.nav-active::before {
  content: '';
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 3px;
  height: 60%;
  background: #6366f1;
  border-radius: 0 3px 3px 0;
}

.nav-icon {
  font-size: 1.1rem;
  width: 24px;
  text-align: center;
}

.nav-label {
  flex: 1;
}

.nav-badge {
  font-size: 0.6rem;
  padding: 2px 8px;
  background: linear-gradient(135deg, #ef4444, #dc2626);
  color: #fff;
  border-radius: 10px;
  letter-spacing: 0.05rem;
  font-weight: 600;
}

/* 底部用户信息 */
.sidebar-bottom {
  border-top: 1px solid rgba(99, 115, 255, 0.1);
  padding-top: 16px;
}

.user-stats {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 12px;
  background: rgba(99, 102, 241, 0.06);
  border-radius: 10px;
  margin-bottom: 12px;
}

.stat-row {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.82rem;
}

.stat-icon {
  font-size: 0.9rem;
  width: 20px;
  text-align: center;
}

.stat-name {
  flex: 1;
  color: #9ca3af;
}

.stat-val {
  color: #e8eaff;
  font-weight: 700;
  font-family: 'Courier New', monospace;
}

.badge-val {
  color: #fbbf24;
  font-size: 0.75rem;
  padding: 1px 8px;
  background: rgba(251, 191, 36, 0.15);
  border-radius: 8px;
  font-family: inherit;
}

.badge-none {
  color: #6b7280;
  font-weight: 400;
  font-size: 0.75rem;
}

.sidebar-footer {
  text-align: center;
  padding: 8px 0;
}

.footer-text {
  font-size: 0.7rem;
  color: #4b5563;
  letter-spacing: 0.1rem;
}

/* ======== 主内容区 ======== */
.main-content {
  margin-left: 260px;
  flex: 1;
  min-height: 100vh;
  position: relative;
}

/* ======== 过渡动画 ======== */
.page-fade-enter-active,
.page-fade-leave-active {
  transition: opacity 0.6s ease;
}
.page-fade-enter-from,
.page-fade-leave-to {
  opacity: 0;
}

.content-fade-enter-active,
.content-fade-leave-active {
  transition: opacity 0.3s ease, transform 0.3s ease;
}
.content-fade-enter-from {
  opacity: 0;
  transform: translateY(8px);
}
.content-fade-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}
</style>