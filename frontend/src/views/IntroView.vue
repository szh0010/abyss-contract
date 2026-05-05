<template>
  <div class="intro-page" :class="{ 'white-flash': whiteFlash }">
    <!-- ========== 第一幕：地铁背景 ========== -->
    <transition name="scene-fade">
      <div v-if="scene === 1" class="scene scene-subway">
        <img :src="bgSubway" class="scene-bg" alt="地铁" />
        <div class="scene-overlay"></div>
        <div class="narration-box">
          <p class="narration-text" :class="{ visible: textVisible }">
            又是一个加班到末班车的夜晚。
          </p>
          <p class="narration-text sub" :class="{ visible: subTextVisible }">
            城市的灯光从车窗外划过，像是永远抓不住的机会。
          </p>
        </div>
        <button class="next-btn" :class="{ visible: showNextBtn }" @click="goToScene(2)">
          继 续
        </button>
      </div>
    </transition>

    <!-- ========== 第二幕：疲惫白领 ========== -->
    <transition name="scene-fade">
      <div v-if="scene === 2" class="scene scene-tired">
        <img :src="charTired" class="scene-bg" alt="疲惫白领" />
        <div class="scene-overlay"></div>
        <div class="narration-box narration-bottom">
          <p class="narration-text" :class="{ visible: textVisible }">
            他是林晓。
          </p>
          <p class="narration-text sub" :class="{ visible: subTextVisible }">
            月薪六千的普通白领，信用卡透支了三张，
          </p>
          <p class="narration-text sub" :class="{ visible: subText2Visible }">
            母亲住院的通知单还压在床头——医药费还差 <span class="highlight">¥50,000</span>。
          </p>
          <p class="narration-text sub urgent" :class="{ visible: subText3Visible }">
            银行贷款被拒了。亲戚借遍了。离发工资还有二十三天。
          </p>
          <p class="narration-text sub urgent" :class="{ visible: subText4Visible }">
            他需要一笔钱。<span class="highlight">现在就要。</span>
          </p>
        </div>
        <button class="next-btn" :class="{ visible: showNextBtn }" @click="goToScene(3)">
          继 续
        </button>
      </div>
    </transition>

    <!-- ========== 第三幕：短信陷阱 ========== -->
    <transition name="scene-fade">
      <div v-if="scene === 3" class="scene scene-message">
        <img :src="messageImg" class="scene-bg" alt="短信" />
        <div class="scene-overlay light"></div>
        <div class="narration-box narration-top">
          <p class="narration-text" :class="{ visible: textVisible }">
            就在这时，一条陌生短信弹了出来——
          </p>
          <p class="narration-text sub tempt" :class="{ visible: subTextVisible }">
            "无抵押、秒到账、利息极低……点击链接即可申请。"
          </p>
        </div>

        <!-- 点击提示 -->
        <div class="click-hint" :class="{ visible: showHint }">
          <span class="hint-arrow">▼</span>
          <span class="hint-text">点 击 链 接</span>
        </div>

        <!-- 隐形点击热区：需要用 F12 对准手机图片中链接的位置 -->
        <div
          class="link-hitbox"
          :class="{ 'debug-hitbox': debugMode }"
          @click="triggerTransition"
          title="点击链接"
        ></div>
      </div>
    </transition>

    <!-- 白光转场层 -->
    <div class="flash-layer" :class="{ active: whiteFlash }"></div>

    <!-- 跳过按钮 -->
    <button class="skip-btn" @click="skipIntro" v-if="!whiteFlash">跳过序章 →</button>

    <!-- 场景指示器 -->
    <div class="scene-indicator" v-if="!whiteFlash">
      <span v-for="n in 3" :key="n" class="dot" :class="{ active: scene === n }"></span>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import bgSubway from '../assets/images/bg_subway.png'
import charTired from '../assets/images/char_tired.png'
import messageImg from '../assets/images/message.png'

const router = useRouter()

const scene = ref(1)
const textVisible = ref(false)
const subTextVisible = ref(false)
const subText2Visible = ref(false)
const subText3Visible = ref(false)
const subText4Visible = ref(false)
const showNextBtn = ref(false)
const showHint = ref(false)
const whiteFlash = ref(false)

// ===== F12 调试模式：设为 true 可看到红框热区 =====
const debugMode = ref(false)

function resetAnimations() {
  textVisible.value = false
  subTextVisible.value = false
  subText2Visible.value = false
  subText3Visible.value = false
  subText4Visible.value = false
  showNextBtn.value = false
  showHint.value = false
}

function playScene(n) {
  resetAnimations()

  if (n === 1) {
    setTimeout(() => { textVisible.value = true }, 800)
    setTimeout(() => { subTextVisible.value = true }, 2200)
    setTimeout(() => { showNextBtn.value = true }, 4000)
  } else if (n === 2) {
    setTimeout(() => { textVisible.value = true }, 600)
    setTimeout(() => { subTextVisible.value = true }, 1800)
    setTimeout(() => { subText2Visible.value = true }, 3200)
    setTimeout(() => { subText3Visible.value = true }, 4800)
    setTimeout(() => { subText4Visible.value = true }, 6400)
    setTimeout(() => { showNextBtn.value = true }, 8000)
  } else if (n === 3) {
    setTimeout(() => { textVisible.value = true }, 600)
    setTimeout(() => { subTextVisible.value = true }, 2000)
    setTimeout(() => { showHint.value = true }, 3500)
  }
}

function goToScene(n) {
  scene.value = n
}

function triggerTransition() {
  whiteFlash.value = true
  setTimeout(() => {
    router.push('/game')
  }, 1200)
}

function skipIntro() {
  router.push('/game')
}

watch(scene, (newVal) => {
  playScene(newVal)
})

onMounted(() => {
  playScene(1)
})
</script>

<style scoped>
.intro-page {
  width: 100vw;
  height: 100vh;
  position: relative;
  overflow: hidden;
  background: #000;
  font-family: 'Noto Serif SC', 'SimSun', serif;
}

/* ======== 场景容器 ======== */
.scene {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
}

.scene-bg {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
  filter: brightness(0.7);
}

.scene-overlay {
  position: absolute;
  inset: 0;
  background: linear-gradient(180deg, rgba(0,0,0,0.4) 0%, rgba(0,0,0,0.6) 50%, rgba(0,0,0,0.85) 100%);
}

.scene-overlay.light {
  background: linear-gradient(180deg, rgba(0,0,0,0.3), rgba(0,0,0,0.4));
}

/* ======== 场景切换动画 ======== */
.scene-fade-enter-active,
.scene-fade-leave-active {
  transition: opacity 1.2s ease;
}
.scene-fade-enter-from,
.scene-fade-leave-to {
  opacity: 0;
}

/* ======== 旁白文字 ======== */
.narration-box {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 85%;
  max-width: 720px;
  text-align: center;
  z-index: 5;
}

.narration-box.narration-bottom {
  top: auto;
  bottom: 12%;
  transform: translate(-50%, 0);
}

.narration-box.narration-top {
  top: 10%;
  transform: translate(-50%, 0);
}

.narration-text {
  font-size: 1.4rem;
  color: #e8e8e8;
  line-height: 2;
  letter-spacing: 0.15rem;
  margin-bottom: 0.8rem;
  opacity: 0;
  transform: translateY(12px);
  filter: blur(4px);
  transition: all 1.2s ease;
  text-shadow: 0 2px 20px rgba(0,0,0,0.9), 0 0 40px rgba(0,0,0,0.8);
}

.narration-text.sub {
  font-size: 1.05rem;
  color: #bbb;
}

.narration-text.urgent {
  color: #e0b0b0;
}

.narration-text.tempt {
  color: #d4af37;
  font-style: italic;
}

.narration-text.visible {
  opacity: 1;
  transform: translateY(0);
  filter: blur(0);
}

.narration-text .highlight {
  color: #ff3333;
  font-weight: 700;
  font-family: 'Courier New', monospace;
  text-shadow: 0 0 20px rgba(255, 51, 51, 0.6);
}

/* ======== 继续按钮 ======== */
.next-btn {
  position: absolute;
  bottom: 4%;
  left: 50%;
  transform: translateX(-50%) translateY(10px);
  padding: 12px 50px;
  background: transparent;
  border: 1px solid rgba(139, 0, 0, 0.6);
  color: #ccc;
  font-size: 1rem;
  font-family: inherit;
  letter-spacing: 0.6rem;
  cursor: pointer;
  transition: all 0.5s ease;
  opacity: 0;
  z-index: 10;
}

.next-btn.visible {
  opacity: 1;
  transform: translateX(-50%) translateY(0);
}

.next-btn:hover {
  background: rgba(139, 0, 0, 0.2);
  border-color: #ff3333;
  color: #ff3333;
  box-shadow: 0 0 25px rgba(139, 0, 0, 0.4);
}

/* ======== 第三幕：点击提示 ======== */
.click-hint {
  position: absolute;
  bottom: 15%;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  opacity: 0;
  transition: opacity 1s ease;
  z-index: 8;
}

.click-hint.visible {
  opacity: 1;
  animation: hintPulse 1.8s ease-in-out infinite;
}

@keyframes hintPulse {
  0%, 100% { opacity: 0.5; transform: translateX(-50%) translateY(0); }
  50% { opacity: 1; transform: translateX(-50%) translateY(-6px); }
}

.hint-arrow {
  color: #d4af37;
  font-size: 1.4rem;
  text-shadow: 0 0 15px rgba(212, 175, 55, 0.8);
}

.hint-text {
  color: #d4af37;
  font-size: 0.85rem;
  letter-spacing: 0.4rem;
  text-shadow: 0 0 10px rgba(212, 175, 55, 0.6);
}

/* ========================================================
   ★★★ 关键：点击热区 ★★★
   默认整张图都可点击（简单粗暴但有效）
   如果需要精准对准手机链接位置，改下面的 top/left/width/height
   ======================================================== */
.link-hitbox {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  cursor: pointer;
  z-index: 20;
  background: transparent;
}

/* F12 调试模式：显示红框，定位完毕后把 debugMode 设为 false */
.link-hitbox.debug-hitbox {
  background: rgba(255, 0, 0, 0.3);
  border: 2px solid #ff0000;
  box-shadow: 0 0 15px rgba(255, 0, 0, 0.6);
}

/* ======== 白光转场 ======== */
.flash-layer {
  position: absolute;
  inset: 0;
  background: #fff;
  opacity: 0;
  pointer-events: none;
  z-index: 100;
  transition: opacity 0.8s ease;
}

.flash-layer.active {
  opacity: 1;
  animation: flashOut 1.2s ease forwards;
}

@keyframes flashOut {
  0% { opacity: 0; }
  30% { opacity: 1; }
  100% { opacity: 1; }
}

/* ======== 跳过按钮 ======== */
.skip-btn {
  position: absolute;
  top: 20px;
  right: 20px;
  padding: 6px 14px;
  background: rgba(0, 0, 0, 0.4);
  border: 1px solid rgba(255, 255, 255, 0.15);
  color: #888;
  font-size: 0.75rem;
  font-family: inherit;
  letter-spacing: 0.2rem;
  cursor: pointer;
  z-index: 50;
  transition: all 0.3s;
}

.skip-btn:hover {
  color: #ccc;
  border-color: rgba(255, 255, 255, 0.3);
  background: rgba(0, 0, 0, 0.6);
}

/* ======== 场景指示器 ======== */
.scene-indicator {
  position: absolute;
  bottom: 20px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  gap: 10px;
  z-index: 50;
}

.scene-indicator .dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.2);
  transition: all 0.4s;
}

.scene-indicator .dot.active {
  background: #ff3333;
  box-shadow: 0 0 10px rgba(255, 51, 51, 0.8);
  width: 24px;
  border-radius: 3px;
}
</style>
