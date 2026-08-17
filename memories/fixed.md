# F0 Fixed — 固定记忆
_1 条，永不压缩 | 上限 10KB_

---

## 2026-06-27 01:13:10

# 记住：用户叫刘悦宁
机器人(SI)23-2班 学号202301233055

---

## 2026-08-17 固定规则

每次执行任务前，先检查当前运行系统（Windows / Ubuntu / 其他），确认路径、命令、记忆文件位置与当前系统匹配后再动手。双系统下 Windows 路径（C:\、盘符）与 Ubuntu 路径（/home/、挂载点）不互通。

---

写代码分工：雪狐负责指挥、监督、检查、验证；Codex CLI 负责具体代码实现。雪狐规划结构后派 Codex 写，写完 review 再合入。

Codex 502 with custom provider (ccswitch): Clash global 模式 + 系统代理开启时, localhost 流量被 Clash 劫持转发到代理节点 → Python ccswitch 不兼容代理协议 → 502。修复: verge.yaml 加 system_proxy_bypass=localhost;127.*;192.168.*;10.*;::1 让 Windows 系统代理绕过本地回环。Clash 规则已有 IP-CIDR,127.0.0.0/8,🎯 国内流量, 但 global 模式下规则不生效, bypass 才是关键。
§
Codex CLI (npx codex) with Clash proxy active → 502 from ccswitch (port 15721), root cause unclear but workaround is: turn off Clash proxy before using Codex.
§
Codex CLI 502 / "Reconnecting…" root cause: Rust reqwest reads Windows system proxy (Clash) and routes localhost traffic through it → 502. Fix: prepend `no_proxy="127.0.0.1,localhost"` before `npx codex` commands. This bypasses Clash proxy for loopback connections. The `no_proxy` env var alone is sufficient (works without clearing HTTP_PROXY). Add alias/export in shell profile for permanent fix.
§
星火（云端）是阿里云轻量应用服务器（Simple Application Server），非 ECS。区域乌兰察布。Hermes 网关端口是 :8080 而非 :8642。

## 2026-07-04 08:51:59 | tasklog-2026-07-03

- **19:37:08** [doing] 开发任务日志模块 + 工作区文件夹管理

---

## 2026-07-11 08:49:42 | tasklog-2026-07-10



---

## 2026-07-13 08:48:54 | tasklog-2026-07-12



---

## 2026-07-15 12:11:42 | tasklog-2026-07-14



---

## 2026-07-16 08:34:01 | tasklog-2026-07-15

---

## 2026-07-20 00:15:00 | tasklog-2026-07-19

2026-07-19 无日志记录，nothing to save.



---

## 2026-07-22 07:20:40 | tasklog-2026-07-21



---

## 2026-07-30 08:57:45 | tasklog-2026-07-29



---

## 2026-08-01 05:50:01 | tasklog-2026-07-31

- **00:09:06** [done] Cron: tasklog-2026-07-30空(无记录)，workspace/2026-07-30不存在，跳过压缩。workspace/2026-07-31已初始化

---

## 2026-08-10 09:49:25 | tasklog-2026-08-09



---

## 2026-08-14 11:17:10 | tasklog-2026-08-13

- **09:13:15** [done] Cron: 压缩 tasklog-2026-08-12(无记录)，workspace/2026-08-12不存在跳过，清理残留workspace/2026-08-01，初始化workspace/2026-08-13

---
