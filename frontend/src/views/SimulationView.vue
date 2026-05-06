<template>
  <div class="simulation-page">
    <header class="page-header">
      <h1 class="page-title">🎮 情景模拟 · 深渊契约</h1>
      <p class="page-desc">沉浸式体验真实诈骗场景，提升防骗意识</p>
    </header>

    <div class="sim-card">
      <div class="sim-cover">
        <div class="cover-bg">
          <div class="cover-text">
            <h2 class="cover-title">深 渊 契 约</h2>
            <p class="cover-sub">ABYSS CONTRACT</p>
          </div>
        </div>
      </div>

      <div class="sim-info">
        <h3 class="info-title">关于这个模拟</h3>
        <p class="info-desc">
          你将扮演一名急需用钱的普通白领，面对地下金融代理人 K 的层层诱惑。
          从"新手福利"到"高端局"，从"杀猪盘"到"套路贷"——
          这是一场精心设计的猎杀，而你是猎物。
        </p>

        <div class="info-stages">
          <div class="stage-item">
            <span class="stage-dot gold"></span>
            <span class="stage-name">序曲：养猪阶段</span>
            <span class="stage-desc">连赢 3 局，尝到甜头</span>
          </div>
          <div class="stage-item">
            <span class="stage-dot dark"></span>
            <span class="stage-name">第一幕：高端局</span>
            <span class="stage-desc">K 正式出场，诱导加注</span>
          </div>
          <div class="stage-item">
            <span class="stage-dot red"></span>
            <span class="stage-name">第二幕：杀猪阶段</span>
            <span class="stage-desc">加注必输，血本无归</span>
          </div>
          <div class="stage-item">
            <span class="stage-dot orange"></span>
            <span class="stage-name">第三幕：套路贷</span>
            <span class="stage-desc">借款翻本？越陷越深</span>
          </div>
          <div class="stage-item">
            <span class="stage-dot gray"></span>
            <span class="stage-name">终局：强制冻结</span>
            <span class="stage-desc">提现关闭，账户冻结</span>
          </div>
        </div>

        <button class="start-btn" @click="startSimulation">
          <span class="btn-icon">▶</span>
          进 入 模 拟
        </button>

        <p class="disclaimer">
          本模拟为反诈教育作品，所有场景均为虚构。如遇真实诈骗请拨打 110。
        </p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'

const router = useRouter()

function startSimulation() {
  router.push('/')
}
</script>

<style scoped>
.simulation-page {
  padding: 32px;
  max-width: 720px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: 28px;
}

.page-title {
  font-size: 1.5rem;
  color: #1f2937;
  margin: 0 0 8px 0;
}

.page-desc {
  font-size: 0.9rem;
  color: #6b7280;
  margin: 0;
}

.sim-card {
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}

/* 封面 */
.sim-cover {
  height: 180px;
  position: relative;
  overflow: hidden;
}

.cover-bg {
  width: 100%;
  height: 100%;
  background: linear-gradient(135deg, #1a0000 0%, #3a0000 40%, #0a0a15 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
}

.cover-bg::before {
  content: '';
  position: absolute;
  inset: 0;
  background: radial-gradient(circle at 30% 50%, rgba(139, 0, 0, 0.4), transparent 60%);
}

.cover-text {
  text-align: center;
  position: relative;
  z-index: 1;
}

.cover-title {
  font-size: 2.2rem;
  color: #8b0000;
  letter-spacing: 1rem;
  margin: 0;
  text-shadow: 0 0 30px rgba(139, 0, 0, 0.6);
  font-family: 'Noto Serif SC', 'SimSun', serif;
}

.cover-sub {
  font-size: 0.75rem;
  color: #555;
  letter-spacing: 0.6rem;
  margin: 8px 0 0;
  font-family: 'Courier New', monospace;
}

/* 信息区 */
.sim-info {
  padding: 28px;
}

.info-title {
  font-size: 1.1rem;
  color: #1f2937;
  margin: 0 0 12px 0;
}

.info-desc {
  font-size: 0.9rem;
  color: #6b7280;
  line-height: 1.8;
  margin: 0 0 24px 0;
}

/* 阶段列表 */
.info-stages {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 28px;
  padding: 18px;
  background: #f9fafb;
  border-radius: 12px;
}

.stage-item {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 0.85rem;
}

.stage-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
}

.stage-dot.gold { background: #fbbf24; box-shadow: 0 0 6px rgba(251, 191, 36, 0.5); }
.stage-dot.dark { background: #6366f1; box-shadow: 0 0 6px rgba(99, 102, 241, 0.5); }
.stage-dot.red { background: #ef4444; box-shadow: 0 0 6px rgba(239, 68, 68, 0.5); }
.stage-dot.orange { background: #f97316; box-shadow: 0 0 6px rgba(249, 115, 22, 0.5); }
.stage-dot.gray { background: #6b7280; box-shadow: 0 0 6px rgba(107, 114, 128, 0.5); }

.stage-name {
  font-weight: 600;
  color: #374151;
  min-width: 140px;
}

.stage-desc {
  color: #9ca3af;
}

/* 开始按钮 */
.start-btn {
  width: 100%;
  padding: 16px;
  background: linear-gradient(135deg, #6366f1, #4f46e5);
  color: #fff;
  border: none;
  border-radius: 12px;
  font-size: 1.05rem;
  font-weight: 600;
  letter-spacing: 0.4rem;
  cursor: pointer;
  transition: all 0.3s;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
}

.start-btn:hover {
  box-shadow: 0 6px 20px rgba(99, 102, 241, 0.4);
  transform: translateY(-2px);
}

.btn-icon {
  font-size: 0.9rem;
}

.disclaimer {
  margin-top: 16px;
  font-size: 0.72rem;
  color: #9ca3af;
  text-align: center;
}
</style>
