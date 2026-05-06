<template>
  <div class="link-check-page">
    <header class="page-header">
      <h1 class="page-title">🔗 可疑链接研判</h1>
      <p class="page-desc">输入可疑 URL，AI 将为你分析其风险等级</p>
    </header>

    <div class="check-card">
      <div class="input-group">
        <input
          v-model="url"
          type="text"
          placeholder="粘贴可疑链接，例如：http://xxx-bank-verify.cn/login"
          class="url-input"
          @keyup.enter="analyzeLink"
        />
        <button class="analyze-btn" @click="analyzeLink" :disabled="!url.trim() || analyzing">
          {{ analyzing ? '分析中...' : '开始研判' }}
        </button>
      </div>

      <!-- 结果展示 -->
      <div v-if="result" class="result-box" :class="'risk-' + result.level">
        <div class="result-header">
          <span class="result-icon">{{ result.level === 'high' ? '🚨' : result.level === 'medium' ? '⚠️' : '✅' }}</span>
          <span class="result-level">{{ result.levelText }}</span>
        </div>
        <div class="result-body">
          <p class="result-reason">{{ result.reason }}</p>
          <p class="result-advice">{{ result.advice }}</p>
        </div>
      </div>
    </div>

    <!-- 常见诈骗链接特征 -->
    <div class="tips-card">
      <h3 class="tips-title">常见诈骗链接特征</h3>
      <ul class="tips-list">
        <li>域名含有 "verify"、"secure"、"login" 等仿冒词汇</li>
        <li>使用非常规顶级域名（.xyz, .top, .cc, .cn 仿冒银行）</li>
        <li>短链接跳转（t.cn/xxx, bit.ly/xxx）隐藏真实地址</li>
        <li>URL 中包含大量随机字符或 IP 地址</li>
      </ul>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const url = ref('')
const analyzing = ref(false)
const result = ref(null)

const HIGH_RISK_PATTERNS = [
  /verify|secure|login|bank.*cn|confirm/i,
  /\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}/,
  /\.(xyz|top|cc|tk|ml|ga|cf)\//i,
]

const MEDIUM_RISK_PATTERNS = [
  /bit\.ly|t\.cn|tinyurl|short/i,
  /free|prize|winner|lucky/i,
]

async function analyzeLink() {
  if (!url.value.trim()) return
  analyzing.value = true
  result.value = null

  await new Promise(r => setTimeout(r, 1200))

  const link = url.value.trim()

  if (HIGH_RISK_PATTERNS.some(p => p.test(link))) {
    result.value = {
      level: 'high',
      levelText: '高风险 · 疑似诈骗',
      reason: '该链接包含仿冒金融机构、钓鱼登录页面等高风险特征。',
      advice: '请勿点击！如已输入个人信息，请立即修改密码并拨打 96110 反诈热线。'
    }
  } else if (MEDIUM_RISK_PATTERNS.some(p => p.test(link))) {
    result.value = {
      level: 'medium',
      levelText: '中风险 · 需要警惕',
      reason: '该链接使用了短链接或包含诱导性词汇，真实目的地不明。',
      advice: '建议不要点击。如需访问，请通过官方渠道验证。'
    }
  } else {
    result.value = {
      level: 'low',
      levelText: '低风险 · 暂未发现异常',
      reason: '未匹配到已知诈骗特征，但仍需保持警惕。',
      advice: '建议通过官方渠道确认链接来源的真实性。'
    }
  }

  analyzing.value = false
}
</script>

<style scoped>
.link-check-page {
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

.check-card {
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 16px;
  padding: 28px;
  margin-bottom: 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}

.input-group {
  display: flex;
  gap: 12px;
}

.url-input {
  flex: 1;
  padding: 14px 18px;
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  font-size: 0.9rem;
  outline: none;
  transition: border-color 0.2s;
  font-family: 'Courier New', monospace;
}

.url-input:focus {
  border-color: #6366f1;
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
}

.analyze-btn {
  padding: 14px 24px;
  background: linear-gradient(135deg, #6366f1, #4f46e5);
  color: #fff;
  border: none;
  border-radius: 10px;
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  white-space: nowrap;
}

.analyze-btn:hover:not(:disabled) {
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.4);
  transform: translateY(-1px);
}

.analyze-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.result-box {
  margin-top: 20px;
  padding: 20px;
  border-radius: 12px;
  border: 2px solid;
  animation: resultIn 0.4s ease;
}

@keyframes resultIn {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}

.risk-high { border-color: #ef4444; background: #fef2f2; }
.risk-medium { border-color: #f59e0b; background: #fffbeb; }
.risk-low { border-color: #10b981; background: #ecfdf5; }

.result-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 12px;
}

.result-icon { font-size: 1.3rem; }

.result-level {
  font-size: 1rem;
  font-weight: 700;
}

.risk-high .result-level { color: #dc2626; }
.risk-medium .result-level { color: #d97706; }
.risk-low .result-level { color: #059669; }

.result-reason {
  font-size: 0.85rem;
  color: #374151;
  margin: 0 0 8px 0;
}

.result-advice {
  font-size: 0.85rem;
  color: #6b7280;
  margin: 0;
  font-style: italic;
}

.tips-card {
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 16px;
  padding: 24px 28px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}

.tips-title {
  font-size: 1rem;
  color: #1f2937;
  margin: 0 0 14px 0;
}

.tips-list {
  padding-left: 20px;
  color: #6b7280;
  font-size: 0.85rem;
  line-height: 2;
}
</style>
