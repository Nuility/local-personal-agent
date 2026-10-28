# Local Personal Agent

本地私人 Agent 原型：主对话读取共享记忆，研究、编程、规划三个专业 Agent 通过独立任务队列运行各自工作流，并将关键文本产出汇入共享记忆。任务可以直接提交给专业 Agent，无需主对话先分派。

默认接入 Ollama 的 `deepseek-r1:8b`。这是 DeepSeek-R1-0528-Qwen3-8B 蒸馏模型，基于 Qwen3-8B，不是完整版 DeepSeek。仓库不包含模型权重、个人记忆或实际对话。

## 环境与安装

- Linux x86_64，或 Windows + WSL2 Ubuntu-24.04。
- Python 3.12、curl、tar、apt、dpkg-deb；Python 部分仅使用标准库。
- NVIDIA GPU 与可用驱动。显存占用随模型和上下文变化；用 `nvidia-smi` 和 `python3 agent.py status` 检查实际 GPU 加载。
- 安装需要联网下载官方 Ollama Linux 运行时及模型，预留至少 15 GB 磁盘空间；运行时与权重存放在忽略目录 `.runtime/`。

在项目目录执行：

```bash
bash setup.sh
bash start.sh
```

Windows 用户可双击 `Setup.cmd`，然后 `Start.cmd`。这些入口使用名为 `Ubuntu-24.04` 的 WSL 发行版；如果发行版名称不同，修改 `.cmd` 文件中的 `-d` 参数。

服务绑定本机 `127.0.0.1:11435`，设置 `OLLAMA_NO_CLOUD=1`。启动脚本会复用该端口已有的 Ollama 服务，因此运行前应确认它是你打算使用的本机服务。模型下载需要网络；推理请求发往本机。

退出聊天后 worker 继续处理队列。停止本项目启动的服务：

```bash
python3 stop.py
```

或双击 `Stop.cmd`。停止脚本校验进程身份，不停止其他项目的服务。不要在活动任务运行过程中停止服务；中断的任务会在 worker 再次启动时恢复排队。

## 本地个性化

未创建本地配置时，程序读取仓库中的 `*.example.*` 模板。要定制，先复制：

```bash
cp config.example.json config.json
cp persona.example.md persona.md
cp core_principles.example.md core_principles.md
```

`config.json` 设置模型、上下文和专业工作流；`persona.md` 设置主对话风格；`core_principles.md` 在每一次模型调用中优先加载。以上本地文件被 Git 忽略，不会随正常提交上传。修改后重启 worker 以加载新配置。原则属于提示词约束，不能保证模型永远不偏离。

初始记忆库为空，不预设任何人的资料。明确偏好由用户主动添加；Agent 的任务摘要标记为未经事实核验的产出，不自动变成用户人格结论。

## 使用

聊天窗口支持 `/help`、`/remember 内容`、`/memories`、`/correct ID 新内容`、`/forget ID`、`/task planning 任务内容`、`/jobs`、`/result ID`、`/exit`。

也可直接使用命令行：

```bash
python3 agent.py remember "回答时先给结论，再给理由"
python3 agent.py ingest ./private/notes.md
python3 agent.py submit research "分析已导入资料的主要论点"
python3 agent.py jobs
python3 agent.py chat "根据已确认的目标，整理下一步计划" --session demo
```

`ingest` 只支持不超过 2 MB 的 UTF-8 `.txt` / `.md`。请先自行创建 `private/` 并放入资料。手动运行后台处理器可用 `python3 agent.py worker`；正常使用 `start.sh` 时它已启动，同一数据目录只允许一个 worker。

## 工作方式与当前边界

- SQLite 保存记忆、会话、任务、步骤检查点与记忆修改记录。独立工作流共享同一模型服务；当前 worker 串行处理专业任务，不表示每个 Agent 都独占 GPU。
- 检索使用中英文词片段匹配，尚无向量嵌入、自动知识图谱或大规模检索。
- 专业 Agent 当前生成分析、计划和代码草稿，没有浏览器、外部应用或执行代码的工具。任务完成表示文本生成完成，不代表计划已经实施。
- `forget` 从可检索共享记忆中移除内容，但原始会话、任务记录以及 SQLite 历史页可能仍保留相关内容；它不是完整数据擦除功能。
- 当前版本没有微调训练流程、自动定时任务或网页界面。记忆检索有助于个性化，不等于模型拥有人的理解或永久准确记忆。
- `data/` 包含未加密的个人数据，应按本地私人文件管理。`PERSONAL_AGENT_DATA` 可改变数据目录；配套启动/停止脚本按默认 `data/` 管理进程，使用自定义目录时需自行管理 worker。

## 检查

```bash
python3 -m unittest -v
bash -n setup.sh start.sh
```

离线测试使用模拟模型响应和临时数据库，覆盖空白初始化、记忆纠正与删除、独立工作流共享产出、失败续跑，以及固定原则注入。测试不证明模型输出质量或任意硬件的 GPU 兼容性。

## 上传边界

仓库仅包含代码、通用配置模板和此说明。个人配置、聊天记录、数据库、导入文档、验收对话、日志、缓存、运行时、模型权重与凭据均未纳入。`.gitignore` 只是默认保护；提交前仍应检查 `git diff --cached`，不要强制添加个人文件。模型与运行时从各自官方渠道获取，遵循各自许可。
