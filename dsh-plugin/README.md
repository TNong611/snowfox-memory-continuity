# dsh-plugin — DSH → Hermes 记忆桥接

`snowfox-sync.mjs` 订阅 DSH `session/event`，把每个 turn 的人类输入与最终回复
以 SnowFox 纪要格式追加到 Hermes `memories/recent.md`（与 Hermes 侧插件 `_build_entry` 格式一致）。

部署：复制到 `~/.dsh/profiles/web/` 并在 `cordis.patch.yml` 中 `insert` 引用
（相对路径 `./snowfox-sync.mjs`，从 profile 目录解析）。
