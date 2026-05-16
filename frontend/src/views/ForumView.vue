<template>
  <div class="forum-root">
    <!-- ====== 顶部 ====== -->
    <header class="forum-head">
      <div class="head-icon liquid-glass">🌳</div>
      <div class="head-meta">
        <h1 class="head-title">深渊树洞</h1>
        <p class="head-sub">防骗经验交流区 · 你说的每一句都会被永久记住</p>
      </div>
      <button class="refresh-btn liquid-glass spring-bounce" @click="refresh" :disabled="loading">
        <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M21 12a9 9 0 1 1-3-6.7L21 8"/>
          <path d="M21 3v5h-5"/>
        </svg>
        <span>刷新</span>
      </button>
    </header>

    <!-- ====== 发帖卡片 ====== -->
    <section class="composer liquid-glass">
      <textarea
        v-model="newPostContent"
        class="composer-input"
        placeholder="分享你的防骗经历… 经验越具体，越能帮到别人"
        maxlength="2000"
        :disabled="submitting"
      ></textarea>

      <!-- 已选附图预览 -->
      <transition name="fade">
        <div v-if="newImagePath" class="composer-preview">
          <img :src="newImagePath" class="preview-img" alt="预览" />
          <button type="button" class="preview-remove" @click="clearAttachment" title="移除图片">×</button>
        </div>
      </transition>

      <!-- 隐藏的 file input -->
      <input
        ref="fileInputEl"
        type="file"
        accept="image/png,image/jpeg,image/jpg,image/gif,image/webp"
        class="hidden-file"
        @change="onFileSelected"
      />

      <div class="composer-foot">
        <button
          class="composer-attach"
          type="button"
          :disabled="uploading || submitting"
          @click="openFilePicker"
          :title="uploading ? '上传中…' : '附上截图（5MB 内）'"
        >
          <span aria-hidden="true">📷</span>
          <span>{{ uploading ? '上传中…' : (newImagePath ? '更换截图' : '附上截图') }}</span>
        </button>
        <div class="composer-meta">
          <span class="char-count" :class="{ warn: newPostContent.length > 1800 }">
            {{ newPostContent.length }} / 2000
          </span>
          <button
            class="composer-submit spring-bounce"
            :disabled="!canSubmit"
            @click="submitPost"
          >
            <span v-if="!submitting">发布分享</span>
            <span v-else class="dots"><i></i><i></i><i></i></span>
          </button>
        </div>
      </div>
    </section>

    <!-- ====== 帖子列表 ====== -->
    <section class="feed">
      <transition-group name="post" tag="div" class="feed-list">
        <article v-for="post in posts" :key="post.id" class="post-card liquid-glass">
          <header class="post-head">
            <div class="post-author">
              <img :src="post.avatar" class="post-avatar" :alt="`${post.author} 头像`" />
              <div class="post-meta">
                <div class="post-name">
                  {{ post.author }}
                  <span v-if="post.is_bot" class="bot-tag">官方</span>
                </div>
                <div class="post-time">{{ post.time }}</div>
              </div>
            </div>
            <button
              v-if="post.is_mine"
              class="post-del"
              @click="deletePost(post.id)"
              title="删除我的发布"
            >删除</button>
          </header>
          <p class="post-content">{{ post.content }}</p>

          <!-- 配图（如果有） -->
          <div v-if="post.image_path" class="post-image-wrap">
            <img :src="post.image_path" class="post-image" alt="附图" loading="lazy" />
          </div>

          <!-- 互动条：点赞 + 评论 -->
          <footer class="post-actions">
            <button
              class="action-btn spring-bounce"
              :class="{ liked: post.liked_by_me }"
              @click="toggleLike(post)"
              :title="post.liked_by_me ? '取消点赞' : '点赞'"
            >
              <span class="action-icon" aria-hidden="true">{{ post.liked_by_me ? '❤️' : '🤍' }}</span>
              <span class="action-count">{{ post.likes }}</span>
            </button>
            <button
              class="action-btn"
              @click="toggleComments(post)"
              :title="post.show_comments ? '收起评论' : '展开评论'"
            >
              <span class="action-icon" aria-hidden="true">💬</span>
              <span class="action-count">{{ post.comment_count }}</span>
            </button>
          </footer>

          <!-- 评论区 -->
          <transition name="fade-down">
            <section v-if="post.show_comments" class="comments">
              <div v-if="post.comments_loading" class="comments-empty">加载中…</div>
              <ul v-else-if="post.comments && post.comments.length" class="comments-list">
                <li v-for="c in post.comments" :key="c.id" class="comment-item">
                  <img :src="c.avatar" class="comment-avatar" alt="" />
                  <div class="comment-body">
                    <div class="comment-head">
                      <span class="comment-name">{{ c.author }}</span>
                      <span class="comment-time">{{ c.time }}</span>
                    </div>
                    <p class="comment-text">{{ c.content }}</p>
                  </div>
                </li>
              </ul>
              <div v-else class="comments-empty">还没有评论 · 来一条吧</div>

              <div class="comment-composer">
                <input
                  v-model="post.draft"
                  class="comment-input"
                  type="text"
                  maxlength="500"
                  placeholder="写下你的看法…"
                  @keyup.enter="submitComment(post)"
                />
                <button
                  class="comment-submit spring-bounce"
                  :disabled="!post.draft || !post.draft.trim() || post.posting_comment"
                  @click="submitComment(post)"
                >
                  发送
                </button>
              </div>
            </section>
          </transition>
        </article>
      </transition-group>

      <p v-if="!loading && posts.length === 0" class="empty">
        还没有人发声 · 做第一个分享经验的人吧
      </p>
      <p v-if="loading" class="empty">加载中…</p>
    </section>
  </div>
</template>

<!-- script -->
<script setup>
import { ref, computed, onMounted } from 'vue'
import http from '../services/http'
import { toast } from '../services/toast'

const posts = ref([])
const newPostContent = ref('')
const newImagePath = ref('')      // 上传成功后的 /uploads/forum/xxx.png
const loading = ref(false)
const submitting = ref(false)
const uploading = ref(false)
const fileInputEl = ref(null)

const canSubmit = computed(
  () => !submitting.value
    && !uploading.value
    && newPostContent.value.trim().length > 0
)

/* 把后端 PostOut 注水成前端可状态化的对象（带评论草稿等本地态） */
function decorate(raw) {
  return {
    ...raw,
    show_comments: false,
    comments: null,
    comments_loading: false,
    posting_comment: false,
    draft: '',
  }
}

async function refresh() {
  loading.value = true
  try {
    const { data } = await http.get('/forum/posts', { params: { limit: 80 } })
    posts.value = (Array.isArray(data) ? data : []).map(decorate)
  } catch (e) {
    if (e?.response?.status !== 401) toast.danger('帖子加载失败')
  } finally {
    loading.value = false
  }
}

/* ===== 图片上传 ===== */
function openFilePicker() {
  if (uploading.value || submitting.value) return
  fileInputEl.value?.click()
}

function clearAttachment() {
  newImagePath.value = ''
  if (fileInputEl.value) fileInputEl.value.value = ''
}

async function onFileSelected(e) {
  const file = e.target.files?.[0]
  if (!file) return
  if (file.size > 5 * 1024 * 1024) {
    toast.warning('图片大小不得超过 5MB')
    e.target.value = ''
    return
  }
  uploading.value = true
  try {
    const form = new FormData()
    form.append('file', file)
    const { data } = await http.post('/forum/upload', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    newImagePath.value = data?.image_path || ''
    toast.success('图片已附上')
  } catch (err) {
    if (err?.response?.status !== 401) {
      toast.danger(err?.response?.data?.detail || '图片上传失败')
    }
  } finally {
    uploading.value = false
    e.target.value = ''
  }
}

/* ===== 发帖 / 删除 ===== */
async function submitPost() {
  if (!canSubmit.value) return
  const content = newPostContent.value.trim()
  submitting.value = true
  try {
    const { data } = await http.post('/forum/posts', {
      content,
      image_path: newImagePath.value || null,
    })
    posts.value = [decorate(data), ...posts.value]
    newPostContent.value = ''
    clearAttachment()
    toast.success('已发布到深渊树洞')
  } catch (e) {
    if (e?.response?.status === 401) return
    toast.danger(e?.response?.data?.detail || '发布失败，请重试')
  } finally {
    submitting.value = false
  }
}

async function deletePost(id) {
  if (!confirm('确定删除这条发布？删除后不可恢复。')) return
  try {
    await http.delete(`/forum/posts/${id}`)
    posts.value = posts.value.filter((p) => p.id !== id)
    toast.success('已删除')
  } catch (e) {
    if (e?.response?.status === 401) return
    if (e?.response?.status === 403) {
      toast.warning('只能删除自己的发布')
      return
    }
    toast.danger(e?.response?.data?.detail || '删除失败')
  }
}

/* ===== 点赞 ===== */
async function toggleLike(post) {
  try {
    const { data } = await http.post(`/forum/posts/${post.id}/like`)
    post.liked_by_me = !!data.liked
    post.likes = data.likes
  } catch (e) {
    if (e?.response?.status === 401) return
    toast.danger('点赞失败')
  }
}

/* ===== 评论 ===== */
async function toggleComments(post) {
  if (post.show_comments) {
    post.show_comments = false
    return
  }
  post.show_comments = true
  if (post.comments) return     // 已加载过则不重拉
  post.comments_loading = true
  try {
    const { data } = await http.get(`/forum/posts/${post.id}/comments`)
    post.comments = Array.isArray(data) ? data : []
  } catch (e) {
    if (e?.response?.status !== 401) toast.danger('评论加载失败')
  } finally {
    post.comments_loading = false
  }
}

async function submitComment(post) {
  const text = (post.draft || '').trim()
  if (!text || post.posting_comment) return
  post.posting_comment = true
  try {
    const { data } = await http.post(`/forum/posts/${post.id}/comments`, {
      content: text,
    })
    post.comments = [...(post.comments || []), data]
    post.comment_count = (post.comment_count || 0) + 1
    post.draft = ''
  } catch (e) {
    if (e?.response?.status === 401) return
    toast.danger(e?.response?.data?.detail || '评论失败')
  } finally {
    post.posting_comment = false
  }
}

onMounted(refresh)
</script>
<!-- style -->
<style scoped>
/* ============================================================
   深渊树洞 · 液态玻璃 + 弹簧动效
============================================================ */
.forum-root {
  width: min(680px, 100%);
  margin: 0 auto;
  padding: 20px 16px 40px;
  display: flex;
  flex-direction: column;
  gap: 22px;
  height: 100%;
  overflow-y: auto;
  /* 隐藏丑陋的原生滚动条 */
  scrollbar-width: none;
  -ms-overflow-style: none;
  font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display',
               'PingFang SC', 'Helvetica Neue', sans-serif;
  color: #1f2937;
}
.forum-root::-webkit-scrollbar { width: 0; height: 0; display: none; }

/* 通用液态玻璃（Demo 原参数） */
.liquid-glass {
  background: rgba(255, 255, 255, 0.5);
  backdrop-filter: blur(24px);
  -webkit-backdrop-filter: blur(24px);
  border: 1px solid rgba(255, 255, 255, 0.7);
  box-shadow:
    inset 0 2px 4px rgba(255, 255, 255, 0.9),
    inset 0 -2px 6px rgba(0, 0, 0, 0.05),
    0 8px 32px rgba(0, 0, 0, 0.06);
}

.spring-bounce { transition: all 0.5s cubic-bezier(0.25, 1.5, 0.5, 1); }
.spring-bounce:active:not(:disabled) { transform: scale(0.92) translateY(2px); }

/* ============ 头部 ============ */
.forum-head {
  display: flex;
  align-items: center;
  gap: 14px;
}
.head-icon {
  width: 44px; height: 44px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.4rem;
  flex-shrink: 0;
}
.head-meta { flex: 1; min-width: 0; }
.head-title {
  font-size: 1.4rem;
  font-weight: 800;
  letter-spacing: 0.06em;
  color: #2d2416;
}
.head-sub {
  font-size: 0.74rem;
  color: #7e6a4f;
  margin-top: 4px;
  letter-spacing: 0.02em;
}
.refresh-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  border: none;
  border-radius: 14px;
  cursor: pointer;
  font: inherit;
  font-size: 0.82rem;
  color: #6b4f24;
}
.refresh-btn:disabled { opacity: 0.6; cursor: not-allowed; }

/* ============ 发帖卡片 ============ */
.composer {
  border-radius: 26px;
  padding: 18px 20px 14px;
}
.composer-input {
  width: 100%;
  min-height: 92px;
  resize: vertical;
  border: none;
  outline: none;
  background: transparent;
  font: inherit;
  font-size: 0.95rem;
  line-height: 1.6;
  color: #1f2937;
  letter-spacing: 0.005em;
}
.composer-input::placeholder {
  color: #9ca3af;
  font-weight: 300;
}
.composer-foot {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 10px;
  padding-top: 12px;
  border-top: 1px solid rgba(0, 0, 0, 0.06);
}
.composer-attach {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border: none;
  background: transparent;
  font: inherit;
  font-size: 0.82rem;
  color: #f97316;
  cursor: pointer;
  opacity: 0.7;
}
.composer-attach[disabled] { cursor: not-allowed; }
.composer-meta {
  display: flex;
  align-items: center;
  gap: 12px;
}
.char-count {
  font-family: 'SF Mono', ui-monospace, monospace;
  font-size: 0.72rem;
  color: #9ca3af;
}
.char-count.warn { color: #ea580c; }
.composer-submit {
  padding: 8px 22px;
  border: none;
  border-radius: 999px;
  cursor: pointer;
  font: inherit;
  font-size: 0.86rem;
  font-weight: 700;
  letter-spacing: 0.04em;
  color: #fff;
  background: linear-gradient(90deg, #fb923c 0%, #ef4444 100%);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.5),
    0 8px 22px rgba(239, 68, 68, 0.32);
}
.composer-submit:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.dots { display: inline-flex; gap: 5px; }
.dots i {
  width: 5px; height: 5px; border-radius: 50%; background: #fff;
  animation: blink 1.2s infinite ease-in-out;
}
.dots i:nth-child(2) { animation-delay: 0.15s; }
.dots i:nth-child(3) { animation-delay: 0.30s; }
@keyframes blink {
  0%, 80%, 100% { opacity: 0.3; transform: scale(0.85); }
  40%           { opacity: 1;   transform: scale(1); }
}

/* ============ 帖子列表 ============ */
.feed { display: flex; flex-direction: column; gap: 18px; }
.feed-list { display: flex; flex-direction: column; gap: 18px; }

.post-card {
  border-radius: 32px;
  padding: 22px 24px;
}
.post-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}
.post-author {
  display: flex;
  align-items: center;
  gap: 12px;
}
.post-avatar {
  width: 44px; height: 44px;
  border-radius: 50%;
  border: 2px solid rgba(255, 255, 255, 0.7);
  background: rgba(255, 255, 255, 0.6);
  object-fit: cover;
}
.post-name {
  font-size: 0.88rem;
  font-weight: 700;
  color: #2d2416;
  display: inline-flex;
  align-items: center;
  gap: 6px;
}
.bot-tag {
  font-family: 'SF Mono', ui-monospace, monospace;
  font-size: 0.62rem;
  letter-spacing: 0.14em;
  padding: 1px 6px;
  border-radius: 6px;
  color: #d97706;
  background: rgba(245, 158, 11, 0.12);
}
.post-time {
  margin-top: 2px;
  font-size: 0.7rem;
  color: #9ca3af;
}
.post-del {
  border: none;
  background: transparent;
  font: inherit;
  font-size: 0.78rem;
  color: #9ca3af;
  cursor: pointer;
  transition: color 0.2s ease;
}
.post-del:hover { color: #ef4444; text-decoration: underline; }
.post-content {
  font-size: 0.92rem;
  line-height: 1.75;
  color: #374151;
  white-space: pre-wrap;
  word-break: break-word;
}

/* ============ 空 / 加载 ============ */
.empty {
  text-align: center;
  font-size: 0.82rem;
  color: #9ca3af;
  padding: 32px 0;
}

/* ============ 列表过渡 ============ */
.post-enter-active,
.post-leave-active {
  transition: all 0.5s cubic-bezier(0.25, 1.5, 0.5, 1);
}
.post-enter-from { opacity: 0; transform: translateY(12px) scale(0.96); }
.post-leave-to   { opacity: 0; transform: translateY(-6px) scale(0.96); }
.post-move       { transition: transform 0.45s cubic-bezier(0.22, 1, 0.36, 1); }

/* ============ 上传 / 配图 ============ */
.hidden-file { display: none; }
.composer-preview {
  position: relative;
  margin-top: 12px;
  width: fit-content;
  max-width: 100%;
}
.preview-img {
  display: block;
  max-width: 240px;
  max-height: 200px;
  border-radius: 14px;
  object-fit: cover;
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.12);
}
.preview-remove {
  position: absolute;
  top: -8px; right: -8px;
  width: 24px; height: 24px;
  border-radius: 50%;
  border: none;
  background: rgba(0, 0, 0, 0.6);
  color: #fff;
  font-size: 14px;
  line-height: 1;
  cursor: pointer;
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.18);
}
.fade-enter-active, .fade-leave-active { transition: all 0.3s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; transform: scale(0.96); }

/* ============ 帖子配图 ============ */
.post-image-wrap {
  margin-top: 8px;
  border-radius: 18px;
  overflow: hidden;
  background: rgba(0, 0, 0, 0.04);
}
.post-image {
  display: block;
  width: 100%;
  max-height: 420px;
  object-fit: cover;
}

/* ============ 互动条 ============ */
.post-actions {
  display: flex;
  gap: 22px;
  margin-top: 14px;
  padding-top: 12px;
  border-top: 1px solid rgba(0, 0, 0, 0.06);
}
.action-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border: none;
  border-radius: 999px;
  background: transparent;
  font: inherit;
  font-size: 0.84rem;
  color: #6b7280;
  cursor: pointer;
  transition: background 0.25s ease, color 0.25s ease;
}
.action-btn:hover { background: rgba(255, 255, 255, 0.55); color: #111827; }
.action-btn.liked { color: #e11d48; }
.action-icon { font-size: 1rem; line-height: 1; }
.action-count { font-family: 'SF Mono', ui-monospace, monospace; font-size: 0.78rem; }

/* ============ 评论区 ============ */
.fade-down-enter-active, .fade-down-leave-active {
  transition: all 0.35s cubic-bezier(0.22, 1, 0.36, 1);
}
.fade-down-enter-from, .fade-down-leave-to {
  opacity: 0; transform: translateY(-6px);
}

.comments {
  margin-top: 12px;
  padding: 12px 14px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.45);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.85);
}
.comments-empty {
  padding: 8px 4px;
  font-size: 0.78rem;
  color: #9ca3af;
  text-align: center;
}
.comments-list { list-style: none; display: flex; flex-direction: column; gap: 10px; }
.comment-item {
  display: flex;
  gap: 10px;
  padding: 6px 0;
}
.comment-avatar {
  width: 30px; height: 30px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.6);
  border: 1px solid rgba(255, 255, 255, 0.7);
  flex-shrink: 0;
  object-fit: cover;
}
.comment-body { flex: 1; min-width: 0; }
.comment-head {
  display: flex;
  align-items: baseline;
  gap: 8px;
}
.comment-name { font-size: 0.82rem; font-weight: 600; color: #1f2937; }
.comment-time { font-size: 0.7rem; color: #9ca3af; }
.comment-text {
  margin-top: 2px;
  font-size: 0.84rem;
  line-height: 1.6;
  color: #374151;
  white-space: pre-wrap;
  word-break: break-word;
}

.comment-composer {
  margin-top: 12px;
  display: flex;
  gap: 8px;
}
.comment-input {
  flex: 1;
  min-width: 0;
  border: 1px solid rgba(0, 0, 0, 0.06);
  background: rgba(255, 255, 255, 0.7);
  border-radius: 999px;
  padding: 8px 14px;
  font: inherit;
  font-size: 0.84rem;
  color: #1f2937;
  outline: none;
  transition: border 0.2s ease, box-shadow 0.2s ease;
}
.comment-input:focus {
  border-color: rgba(251, 146, 60, 0.5);
  box-shadow: 0 0 0 3px rgba(251, 146, 60, 0.18);
}
.comment-submit {
  padding: 8px 18px;
  border: none;
  border-radius: 999px;
  font: inherit;
  font-size: 0.82rem;
  font-weight: 700;
  color: #fff;
  background: linear-gradient(90deg, #fb923c 0%, #ef4444 100%);
  box-shadow: 0 6px 16px rgba(239, 68, 68, 0.3);
  cursor: pointer;
}
.comment-submit:disabled { opacity: 0.5; cursor: not-allowed; }
</style>

