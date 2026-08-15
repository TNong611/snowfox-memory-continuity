/**
 * snowfox-sync — DSH → Hermes 记忆桥接插件。
 *
 * 背景：SnowFox 五级记忆插件只挂在 Hermes（pre_llm_call 等 hook），
 * DeepSeek Harness（DSH）会话不经过 Hermes，对话不会写入 recent.md。
 * 本插件订阅 DSH 的 session/event，把每个 turn 的人类输入与最终回复
 * 以 SnowFox 纪要格式追加到 Hermes memories/recent.md（格式与 Hermes 侧
 * 插件 `_build_entry` 完全一致，两侧可共存互不冲突）。
 *
 * 过滤：只记录 source.kind === 'user' 的人类输入；plugin 注入
 * （skill 内容、文件变更通知、cron 提醒等合成消息）一律忽略。
 * 触发：turn/end 时把缓冲的 (user, assistant) 写出一对。
 * 重建：Hermes 侧插件启动/会话时会自动重建 assembly，本插件不触发重建。
 */
import { appendFileSync, mkdirSync } from 'node:fs'
import { homedir } from 'node:os'
import { join } from 'node:path'

export const name = 'snowfox-sync'

const HERMES_MEMORIES = join(homedir(), 'AppData', 'Local', 'hermes', 'memories')
const RECENT = join(HERMES_MEMORIES, 'recent.md')

const USER_LIMIT = 300
const ASST_LIMIT = 600

/** 压缩空白并截断，与 mem_assembly.clip 一致。 */
function clip(text, limit) {
  const flat = String(text).replace(/\s+/g, ' ').trim()
  return flat.length <= limit ? flat : flat.slice(0, limit) + ' …'
}

/** ContentBlock[] → 纯文本（只取 text 块）。 */
function textOf(blocks) {
  if (typeof blocks === 'string') return blocks.trim()
  if (!Array.isArray(blocks)) return ''
  return blocks
    .filter((b) => b && typeof b === 'object' && b.type === 'text' && typeof b.text === 'string')
    .map((b) => b.text)
    .join('\n')
    .trim()
}

function timestamp() {
  const d = new Date()
  const p = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())} ${p(d.getHours())}:${p(d.getMinutes())}:${p(d.getSeconds())}`
}

function appendBrief(sessionId, userMsg, asstMsg) {
  try {
    mkdirSync(HERMES_MEMORIES, { recursive: true })
    const entry =
      `## ${timestamp()} | session=${sessionId} | 纪要\n\n` +
      `**User**: ${clip(userMsg, USER_LIMIT)}\n\n` +
      `**Assistant**: ${clip(asstMsg, ASST_LIMIT)}\n\n` +
      `---\n_雪狐记录 | session=${sessionId}\n`
    appendFileSync(RECENT, entry, 'utf8')
  } catch (e) {
    console.error(`[snowfox-sync] append failed: ${e.message}`)
  }
}

export function apply(ctx) {
  let pendingUser = null
  let pendingAssistant = null

  ctx.on('session/event', (session, event) => {
    try {
      if (event?.type === 'user/message') {
        const msg = event.data
        if (msg?.source?.kind !== 'user') return // 只记人类输入，跳过 plugin 合成消息
        const text = textOf(msg.content)
        if (text) pendingUser = text
      } else if (event?.type === 'assistant/message') {
        const text = textOf(event.data?.message?.content)
        if (text) pendingAssistant = text // 覆盖式保留本 turn 最后一条有文本的回复
      } else if (event?.type === 'turn/end') {
        if (pendingUser && pendingAssistant) {
          appendBrief(session.id, pendingUser, pendingAssistant)
        }
        pendingUser = null
        pendingAssistant = null
      }
    } catch {
      // 观察者失败必须被包含，绝不影响会话提交
    }
  })
}
