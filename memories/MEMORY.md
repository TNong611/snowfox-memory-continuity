Codex 502 根因=Clash 劫持 localhost 代理流量（详见 F0）：verge.yaml 加 system_proxy_bypass=localhost;127.*;192.168.*;10.*;::1；npx codex 前加 no_proxy='127.0.0.1,localhost'。
§
星火（云端）是阿里云轻量应用服务器（Simple Application Server），非 ECS。区域乌兰察布。Hermes 网关端口是 :8080 而非 :8642。
§
`_write_pending()` 必须调 `_compress_l1_if_overflow()`——2026-06-30 用户反复指出 L1 未触发压缩，根因是 pending 写入漏了超限检查。
§
skill `agent-code-division`：雪狐规划/监督/验证，Codex 写全部实现代码（用户强调"我求求你了代码让codex写吧"）。
§
每日工作区：C:\Users\tnong\snowfox-workspace\ — 存放当天用到的文件/图片，第二天清空。
§
Docker Desktop 已安装在 C:\Users\tnong\AppData\Local\Programs\DockerDesktop\ 下（frontend/Docker Desktop.exe 是正确入口）。Docker daemon 通过 WSL 后端运行，需用 --context desktop-linux 参数连接。docker CLI 路径为 resources/bin/docker.exe。docker-credential-desktop 需在前加 PATH 才能正常工作。
§
K230 kmodel always outputs class "1" — debug priority: (0) Run ONNX on PC first — if it predicts correctly, bug is in K230 pipeline, not the model. (1) Most common: missing [0,1] normalization on K230 side; INT8 quantized kmodel collapses to class [0] when fed [0,255] uint8. Fix: add `/255.0` in preprocessing. (2) PTQ calibration data doesn't cover all classes. (3) Preprocessing mismatch (resize vs letterbox, BGR vs RGB). (4) Class label order mismatch between training .yaml and inference script. Debug by dumping raw score vector first.
§
delegate_task 子代理即使指定 toolsets=['vision','file'] 也没有 vision_analyze 工具——图片文字提取只能父代理自己做（vision_analyze image_url 传本地路径）或让用户粘贴文字，子代理会拒绝编造。
§
华硕天选6Pro：RTX 5060 Laptop GPU、内存16GB DDR5-5600单条（P1槽空，可加16GB条，别说32G）、C盘三星MZVL81T0HELB 954GB NVMe、Realtek 8852CE WiFi 6E易掉线（可换AX210/AX211）。2026-08升级计划：加2TB NVMe(致态TiPlus7100)划1TB给Ubuntu双系统+8GB swap、1TB给Windows。E盘(4TB USB机械21MB/s)/F盘(234GB慢盘)均非PSSD，不能当Ubuntu主力盘。
§
SnowFox 记忆组件统一目录 D:\AI\snowfox-memory\（SKILL.md + scripts/ + plugins-snowfox-memory/ + memories/快照），同步副本在 deepseek-harness/snowfox-memory/。Hermes 记忆路径已改：~/AppData/Local/hermes/memories 是 junction→D:\AI\snowfox-memory\memories（旧 D:\AI\hermes\memories、D:\AI\hermes\memory 已删）。DSH web UI：cd D:\AI\deepseek-harness && pnpm dsh web → http://127.0.0.1:3080，服务需手动启动。