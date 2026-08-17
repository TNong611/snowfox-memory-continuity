/**
 * snowfox-inject — Hermes 五级记忆 → DSH 系统提示注入插件。
 *
 * 背景：SnowFox 五级记忆的组装产物 _assembled_context.md 由 Hermes 侧插件
 * 周期性重建（USER/F0/L3/L2/L1 预算制组装，36KB）。DSH 会话不经过 Hermes，
 * 此前只有 snowfox-sync 把对话单向写入 recent.md，记忆从未作为输入进入
 * DSH 的模型请求。本插件在每次 prompt assembly 时读取最新组装产物，
 * 以 prompt section 形式注入系统提示，实现「记忆文件作为输入，
 * 会话框只负责显示」的架构意图。
 *
 * 降级：文件不存在 / 读取失败 / 超限时返回空 section，绝不影响会话提交。
 * 容量：组装产物本身受 36KB 预算约束；本插件再设 64KB 硬上限防异常膨胀。
 */

import { readFileSync } from 'node:fs'
import { join } from 'node:path'

export const name = 'snowfox-inject'

/** 使用 ctx.systemPrompt 服务必须声明 inject 依赖（cordis 约定）。 */
export const inject = ['systemPrompt']

/** 记忆真源目录（junction 目标，与 hermes 运行时同目录）。 */
const MEMORIES_DIR = 'D:\\AI\\snowfox-memory\\memories'
const ASSEMBLY = join(MEMORIES_DIR, '_assembled_context.md')

/** 硬上限：超过即丢弃，避免异常组装产物挤爆上下文。 */
const MAX_BYTES = 64 * 1024

/**
 * 会话级快照缓存：同一会话内只读一次组装文件并固定快照，prompt 前缀
 * 保持稳定 → DeepSeek 前缀缓存可命中（命中率从 53% 回到 90%+）。
 *
 * 剥离首行 `<!-- SnowFox Memory Assembly | built: ... -->` 时间戳注释：
 * 该行每次组装重建都会变化，若保留会破坏 system prompt 前缀稳定性。
 *
 * 刷新时机：`session/created` 事件（新会话）清空缓存，下次 assembly 重读
 * 最新组装。会话中途 Hermes 重建组装不影响已固定的前缀。
 *
 * 失败不缓存：读失败/超限返回空，下次调用重试（观察者失败必须被包含）。
 */
let cachedText = null

function loadAssembly() {
  if (cachedText !== null) return cachedText
  try {
    const raw = readFileSync(ASSEMBLY, 'utf8')
    // 去掉 UTF-8 BOM、剥离首行 built 时间戳注释、裁剪超限内容
    const text = raw
      .replace(/^\uFEFF/, '')
      .replace(/^<!-- SnowFox Memory Assembly \| built: [^\n]* -->\r?\n/, '')
      .trim()
    if (!text) return ''
    if (Buffer.byteLength(text, 'utf8') > MAX_BYTES) return ''
    cachedText = text
    return text
  } catch {
    return ''
  }
}

export function apply(ctx) {
  // 新会话创建时清缓存，下次 prompt assembly 读最新组装记忆。
  ctx.on('session/created', () => {
    cachedText = null
  })
  ctx.systemPrompt.section({
    name: 'snowfox:memory',
    // harness identity 为 -100、persona 为 0；-50 使记忆排在 persona 之前。
    order: -50,
    text: () => loadAssembly(),
  })
}
