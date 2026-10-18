# 贡献和复盘约定

每次实验提交一个session记录，更新对应主题而不重复复制教程。
1. 记录硬件、OS/L4T/JetPack、解释器与主要依赖版本。
2. 写清输入、命令、预期、实际结果、失败分支和回退。
3. 标记verified/partial/pending/planned；重构版需要独立硬件验收。
4. 性能比较统一输入与精度说明、预热、重复次数；注明功率/温度证据缺口。
5. 模型、视频、日志和engine保存在本地；只提交来源、参数、脱敏摘要和校验值。
6. 提交前运行 python3 -m unittest discover -s tests 和 bash -n scripts/inspect_jetson.sh。
7. 不提交公司IP、账号、访问令牌、短期签名URL、个人图片和未获授权的视频。

新增阶段在 sessions/ 写短复盘，在 docs/ 更新主题，代码进 scripts/ 或 examples/，记录 CHANGELOG。Notion由助手按同一session_id幂等提炼。
