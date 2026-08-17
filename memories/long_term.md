# L3 Long-term — 长期记忆

## 系统还原后模型被删，重新拉取超时；用户要求识别三个SolidWorks残肢应用（3DEXPERIENCE Exchang 【重复×3】
系统还原后模型被删，重新拉取超时；用户要求识别三个SolidWorks残肢应用（3DEXPERIENCE Exchange、CEF、Login Manager），决定卸载并清注册表；DISM修复系统至67.5%，QQ和图吧工具箱损坏；模型配置在deepseek-v4-flash和v4-pro间反复切换，最终通过配置文件固定为flash，别名显示为V4.Med；会话锁定需/new或/model命令切换模型。
## 系统还原后SolidWorks残肢卸载、DISM修复、模型配置切换为deepseek-v4-flash，会话需/new或 【重复×2】

系统还原后SolidWorks残肢卸载、DISM修复、模型配置切换为deepseek-v4-flash，会话需/new或/model切换。
## 用户要求先将当前文本加载到 recent，再处理平台自动注入的会话历史。 【重复×2】
用户要求先将当前文本加载到 recent，再处理平台自动注入的会话历史。
用户指令：当前文本未加载到recent，要求先加载再处理平台自动注入的会话历史。
## 用户提示：达到工具调用最大次数，要求总结已发现和完成的内容，不再调用工具。 【重复×2】
用户提示：达到工具调用最大次数，要求总结已发现和完成的内容，不再调用工具。
用户消息：达到工具调用次数上限，要求总结发现与成果，不再调用工具。
## 系统提示达到工具调用上限，要求给出最终总结。 【重复×2】
系统提示达到工具调用上限，要求给出最终总结。
用户提示达到工具调用上限，要求给出最终总结，不再调用工具。
## 工具调用达到最大迭代次数，要求提供最终总结，不再调用工具。 【重复×2】
工具调用达到最大迭代次数，要求提供最终总结，不再调用工具。
达到工具调用上限，要求提供最终总结，不再调用工具。
## Assistant
重写插件__init__.py：_on_pre_llm_call从history提取上一轮对话写入recent/；_on_session_end仅日志；_save_turn写入recent/文件并调用_rebuild_assembly；_extract_prev_turn逆向遍历跳过tool消息找最后
assistant→user对

## Assistant
2026-06-29 20:33:42，助手确认bug已修复并写入recent。根因是memory_tool.py的_path_for()硬编码路径，已改为SnowFox标准路径：user→user/profile.md，memory→long_term/memory.md。运行版和开发版均已打补丁。

## 修复总结
修复register()签名不兼容和钩子名不匹配bug；修改plugins/snowfox-memory/__init__.py；需重启Hermes并检查memories/recent/、_assembled_context.md、agent.log；提醒同步plugin.yaml的hooks配置。

## consolidated
Windows 11环境，TIA Portal SQL Server崩溃已修复；用户刘悦宁，SolidWorks 2026不稳定欲降级；星火服务器SSH密钥丢失，密码认证；五级禁用；Ollama强制GPU；CLTRN理论提出记忆系统部署；SnowFox fork修改。

## consolidated
系统还原后SolidWorks残件(3DEXPERIENCE Exchange、CEF、Login Manager)需卸载；DISM修复系统至67%；模型配置从deepseek-v4-pro切回flash，建议直接改配置文件避免界面覆盖。

## User
用户指出post_llm_call钩子不可靠，agent.log无snowfox-memory插件日志，确认插件从未加载或register()未调用，决定放弃post_llm_call，改用pre_llm_call+on_session_end方案。

## consolidated
2026-06-27 02:43:32，用户要求写入test.txt，内容"SnowFox agent is running"，工具write_file执行成功，写入24字节至C:\Users\tnong\test.txt。

## User
用户质疑实时性不足，建议通过发送和生成中断直接写入recent。

# consolidated
架构已有post_llm_call钩子，问题为插件未加载+assembly未实时重建，插件内添加_rebuild_assembly()。

## User
2026-06-29 20:27:19，用户报告C:\Users\tnong\AppData\Local\hermes\memories下MEMORY和USER文件不断生成的bug，要求修复并将会话加入recent。

## consolidated
用户询问recent文件夹无聊天记录，解释五级记忆数据流：F0固定→L1近期→L2中期→L3长期→L4，user/fixed不压缩，修复config.yaml中plugins.enabled类型错误。

## Assistant
分析post_llm_call触发条件，确认插件snowfox-memory虽在plugins.enabled中但钩子未注册，运行时pm._hooks显示post_llm_call为0 callback。

## Assistant
修复平台历史注入问题：turn_context.py 新增 _snowfox_ch 保存完整历史给钩子，conversation_loop.py 跳过历史轮次只发当前轮次给 LLM，DB 持久化不受影响

## User
任务列表：修_on_session_end兜底写入(in_progress)；运行memory_maintenance(pending)；验证recent/和assembly包含当前会话(pending)

## Assistant
4/4测试通过：api_messages只含当前轮次，_snowfox_ch保留历史给钩子，修改turn_context.py和conversation_loop.py，DB持久化不受影响

## consolidated
L1已包含最近对话（测试→钩子迁移→Codex修复），询问用户“没同步”具体指当前会话历史、更早会话还是其他内容，可写入recent/和_assembled_context.md。

## consolidated
确认 _assembled_context.md 含旧数据(06-27)，手动运行 memory_maintenance.py 重建 assembly，并补写当前会话文件。

## Assistant
助手说明_assembled_context.md已有248行，包含最近对话（测试、钩子迁移、Codex修复），询问用户“未同步”的具体范围（当前会话历史/更早会话/其他）。

## consolidated
Hermes Agent系统提示：定义助手角色（Nous Research），强调工具执行、真实结果、避免虚构输出；提供文档链接和技能加载指导；要求并行工具调用。

## Assistant
修复：SOUL.md第13行“近期流”改为“完整近期对话”；删除孤立USER.md；同步两个memory_maintenance.py版本（加USER段、全量L3）

## User
用户提出新方案：不用不可靠的post_llm_call钩子，改用pre_llm_call钩子（下次LLM调用前触发）+on_session_end钩子兜底，确保每轮都能保存。

## consolidated
用户提供Codex.exe路径(C:\Program Files\WindowsApps\...)，助手确认是Windows Store安装版本并准备使用。

## 输入架构
定义了Hermes平台的输入架构：系统提示层（身份/工具/Skills）+ 组装记忆层（F0/L3/用户画像/L2/L1）+ 当前消息层；会话框仅显示，不作为输入。

## Assistant
手动补写缺失轮次到recent/，修改turn_context.py去掉conversation_history注入，只保留当前用户消息

## Assistant
4/4 测试通过：api_messages 只含当前轮次、后续 API 调用跳过历史、_snowfox_ch 保留完整历史、文件修改确认

## 输入架构
输入架构说明：系统提示层（Hermes固定注入）、组装记忆层（含F0/L3/用户画像/L2/L1）、当前消息层；强调会话框仅用于显示，非输入来源。
## consolidated
用户通过中继向雪狐发送了2条消息：CLTRN中文版(2346字)和英文版(6459字)，并提供了curl拉取命令及token。

## Assistant
mem_compress.py按字节大小(st_size)触发：.md文件总字节>50KB时，按mtime从旧到新移出文件至~5KB

## Assistant
解释插件未加载、cron周期、assembly快照延迟链，手动运行memory_maintenance.py重建assembly。

## Assistant
助手检查recent/状态和插件代码，记录session=20260628_132543_5d1bf4_。

## Assistant
汇编重建成功(10514B)，验证雪狐记录 session=20260628_132543_5d1bf4_

## Assistant
手动修复代码，Codex三条路（代理502、OpenAI 403、Anthropic未内置）均不可用。

## User
助手记录会话标识：_雪狐记录 | session=20260628_144421_25d3b2_。

## User
用户询问新会话不知当前会话，解释三次链路延迟并手动重跑assembly。

## consolidated
用户要求同步之前会话框内容，助手检查记忆状态和会话框。

## consolidated
雪狐从L3（长期记忆）退休，不再参与跨会话知识管理。

## session=20260628
记录了会话ID为20260628的会话。

## Assistant
因插件需/new加载，本轮未触发自动写入，手动补写。

## consolidated
L2（中期摘要）被合并/压缩，旧会话知识浓缩。

## Assistant
助手回复“你好！有什么可以帮你的？”，无其他内容。

## User
用户反馈当前会话未加载recent，建议让codex帮忙写。

## User
用户询问超限触发基于文件占用大小还是字节大小

## User
用户反馈recent仍看不到当前聊天记录。

## 雪狐
雪狐：确认，重置会话框，加载组装上下文。
## 排查Codex→ccswitch→DeepSeek链路，定位`requires_openai_auth=true`导致代
排查Codex→ccswitch→DeepSeek链路，定位`requires_openai_auth=true`导致代理验证OpenAI失败502，改为false

## 确认`base_url=15721`、`requires_openai_auth=false`，建议试`npx code
确认`base_url=15721`、`requires_openai_auth=false`，建议试`npx codex exec --yolo 'ok?'`

## 分析Clash代理导致127.0.0.1:15721报502：本地回环被劫持、HTTP代理协议不兼容；解决方案：Clas
分析Clash代理导致127.0.0.1:15721报502：本地回环被劫持、HTTP代理协议不兼容；解决方案：Clash配置绕过本地回环

## 诊断结论：ccswitch能正确处理Responses API；502因config.toml中base_url被改为死
诊断结论：ccswitch能正确处理Responses API；502因config.toml中base_url被改为死端口15726；requires_openai_auth已恢复false；已恢复config指向http://127.0.0.1:15721/v1

## Codex连不上因Rust reqwest自动走Clash代理导致502，修复：设置no_proxy="127.0.0.
Codex连不上因Rust reqwest自动走Clash代理导致502，修复：设置no_proxy="127.0.0.1,localhost"，已写入~/.bashrc的codex()函数

## Codex连接问题根因：Rust reqwest自动走Clash代理导致502，修复方案已写入~/.bashrc，测试验
Codex连接问题根因：Rust reqwest自动走Clash代理导致502，修复方案已写入~/.bashrc，测试验证通过

## 修复ccswitch弹窗：Rust/Tauri应用silentStartup:false→true，下次启动直接最小化到
修复ccswitch弹窗：Rust/Tauri应用silentStartup:false→true，下次启动直接最小化到托盘

## SSH暂时连不上，但核心部署已完成，部署memory-continuity v4.0.0到星火云端Hermes
SSH暂时连不上，但核心部署已完成，部署memory-continuity v4.0.0到星火云端Hermes

## 部署完成：memory-continuity v2→v4.0.0，MD5校验通过；遗留references/目录待SSH
部署完成：memory-continuity v2→v4.0.0，MD5校验通过；遗留references/目录待SSH恢复后清理

## 修复SnowFox记忆插件bug：删除__init__.py中未初始化变量_last_turn的引用，pre_llm_c
修复SnowFox记忆插件bug：删除__init__.py中未初始化变量_last_turn的引用，pre_llm_call钩子恢复正常，需重启Gateway生效

## 飞书连接已恢复：22:58:13重连成功，原网关PID 31972的WebSocket实际已断开（Lark SDK报re
飞书连接已恢复：22:58:13重连成功，原网关PID 31972的WebSocket实际已断开（Lark SDK报receive message loop exit），重启后修复

## 修复SnowFox插件bug：`__init__.py`第36行未定义变量`_last_turn`已删除；需重启Gate
修复SnowFox插件bug：`__init__.py`第36行未定义变量`_last_turn`已删除；需重启Gateway生效；F0有4个固定记忆，L1有3条记录，L2/L3/L4为空

## 超限压缩策略改为L1留45KB其余压缩至L2，修复`_last_turn`未定义bug，需重启Gateway
超限压缩策略改为L1留45KB其余压缩至L2，修复`_last_turn`未定义bug，需重启Gateway

## 本地三脚本验证通过：L1从98KB压缩至40.9KB；SSH超时无法同步星火，建议改用独立脚本cron部署
本地三脚本验证通过：L1从98KB压缩至40.9KB；SSH超时无法同步星火，建议改用独立脚本cron部署

## 用户质疑L2/L3保留容量计算依据，要求修改技能并同步GitHub，但对话无有效技能更新点
用户质疑L2/L3保留容量计算依据，要求修改技能并同步GitHub，但对话无有效技能更新点

## L3长期记忆模块，上限50KB，存储跨会话知识
L3长期记忆模块，上限50KB，存储跨会话知识

## 输入架构：系统提示层+组装记忆层（F0/L3/USER/L2/L1）+当前消息层；会话框仅显示，非输入源
输入架构：系统提示层+组装记忆层（F0/L3/USER/L2/L1）+当前消息层；会话框仅显示，非输入源

## 用户询问Hermes更新失败，助手诊断原因为Windows锁定hermes.exe进程(PID 29016)，提供方案A
用户询问Hermes更新失败，助手诊断原因为Windows锁定hermes.exe进程(PID 29016)，提供方案A(关闭GUI后手动更新)和方案B(使用--force强制更新)

## 用户询问输入架构，助手详细解释了五级记忆组装式输入架构（F0固定记忆、L4归档、L3长期、L2中期摘要、L1近期对话）及
用户询问输入架构，助手详细解释了五级记忆组装式输入架构（F0固定记忆、L4归档、L3长期、L2中期摘要、L1近期对话）及压缩策略

