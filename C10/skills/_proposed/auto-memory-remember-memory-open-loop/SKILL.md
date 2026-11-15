# auto-memory-remember-memory-open-loop（自动草案，未上线）

- 支持度：2 次轨迹
- 工具序列：memory.remember → memory.open_loop
- 样例任务：
  - 记住：C10 的写权限边界是项目根，越界一律拒绝；记个待办：给 miner 加一个 min_support=3 的回归
  - 记住：写权限边界是项目根，越界一律拒绝；记个待办：验证遗忘阈值从 0.15 调到 0.2 的影响

## 上线前必须人工完成
1. 确认该序列的语义边界（它到底解决什么问题）；
2. 补齐 triggers 与 inputs 契约；
3. 把 `<从轨迹补全>` 占位替换为真实参数绑定；
4. `python agent.py --promote auto-memory-remember-memory-open-loop`
