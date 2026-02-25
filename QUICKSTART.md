# 快速启动指南

## 快速开始

### 1. 安装依赖

```bash
cd weekly_report_automation
pip install -r requirements.txt
```

### 2. 测试模块

测试各个基础模块：

```bash
# 测试日期计算
python src/date_utils.py

# 测试SQL预处理
python src/sql_preprocessor.py

# 测试数据分析
python src/data_analyzer.py

# 测试数据质量
python src/data_quality.py
```

### 3. 运行主程序

```bash
python main.py
```

系统会提示：
1. 选择目标周（本周/下周/指定日期）
2. 是否提供收入MD文档（可选）
3. 确认执行参数

### 4. 一键生成（快速模式）

```bash
python generate_weekly_report.py
```

使用默认参数快速生成本周周报。

### 5. 执行流程

系统会自动执行：
1. ✅ 计算日期参数
2. ✅ 预处理SQL文件（替换日期参数）
3. ✅ 从Metabase获取本周数据
4. ✅ 从Metabase获取上周数据（或从归档加载）
5. ✅ 计算环比变化
6. ✅ 数据质量验证和异常检测
7. ✅ 生成HTML报告
8. ✅ 更新Confluence页面
9. ✅ 归档数据和报告到output目录

## 当前状态

### ✅ 已实现并测试

- ✅ **date_utils.py** - 日期计算（支持本周/下周/任意周）
- ✅ **sql_preprocessor.py** - SQL参数替换
- ✅ **data_analyzer.py** - 环比计算和基础分析
- ✅ **logger.py** - 日志配置
- ✅ **interactive_prompt.py** - 命令行交互
- ✅ **data_quality.py** - 数据验证和质量分析
- ✅ **data_loader.py** - 统一数据加载接口
- ✅ **report_generator.py** - HTML生成
- ✅ **confluence_updater.py** - Confluence更新
- ✅ **main.py** - 主流程整合
- ✅ **generate_weekly_report.py** - 一键生成脚本

### ⏳ 待完善的功能

- **完整报告生成** - 实现所有5个部分的完整HTML生成
- **MD文档深度集成** - 收入MD的解析和应用
- **指标模块拆分** - 将metrics_extractor拆分为独立模块
- **性能优化** - 并行查询、缓存机制
- **定时任务** - 实现run_scheduled.py用于自动执行

## 使用示例

### 场景1：本周更新（无收入MD）

```bash
$ python main.py

📊 Coohom周报自动化更新系统
============================================================

请选择目标周：
  1. 本周（默认）
  2. 下一周
  3. 上一周
  4. 手动指定日期

请输入选项 (1-4, 默认1): 1

------------------------------------------------------------
💰 收入部分配置
------------------------------------------------------------

本周是否有收入周总结MD文档？ (y/n, 默认n): n

[执行...]
✅ 周报更新完成！
```

### 场景2：指定日期更新

```bash
请输入选项 (1-4, 默认1): 4
请输入日期 (格式: YYYYMMDD, 如: 20260126): 20260205

[系统会自动计算该日期所在周的参数...]
```

### 场景3：一键生成

```bash
$ python generate_weekly_report.py

[系统使用默认参数自动执行...]
✅ 周报生成完成！
```

## 注意事项

1. **MCP工具调用** - 当前通过subprocess调用MCP工具，需要确保MCP环境配置正确
2. **Metabase连接** - 需要确保能够访问Metabase
3. **Confluence权限** - 需要robot-mobot账号有更新页面81397518314的权限
4. **SQL文件** - SQL文件已在项目中，参数替换规则已配置
5. **输出目录** - 系统会自动按月归档输出文件到 `output/archive/` 目录

## 数据归档

系统会自动将生成的文件归档到按月组织的目录：

```
output/
├── archive/
│   └── 2026-02/
│       ├── json/          # JSON数据文件
│       └── reports/       # 生成的报告
├── cache/               # 查询缓存
└── sql_queries/         # SQL查询历史
```

文件命名格式：
- JSON数据: `{section}_{week_label}.json` (如 `traffic_2026w08.json`)
- 报告文件: `{report_name}_{week_label}.{ext}` (如 `weekly_report_2026w08.html`)

## 下一步优化

1. **完善报告生成** - 实现所有5个部分的完整HTML生成
2. **MD文档解析** - 深度解析收入MD并智能应用
3. **错误处理** - 添加更详细的错误信息和恢复机制
4. **定时任务** - 实现run_scheduled.py用于自动执行
5. **单元测试** - 为每个模块添加单元测试
6. **指标模块化** - 将metrics_extractor拆分为独立模块到metrics/目录

## 故障排查

### 问题1：ModuleNotFoundError

确保在项目根目录执行，并且使用了正确的Python路径：

```bash
cd weekly_report_automation
python main.py  # 而不是 python src/main.py
```

### 问题2：MCP工具调用失败

检查MCP工具是否可用：

```bash
mcp list  # 查看可用的MCP工具
```

### 问题3：Metabase查询失败

- 检查database_id配置（config.yaml中）
- 验证SQL文件路径正确
- 检查日期参数是否正确替换

### 问题4：数据加载失败

- 检查 `output/archive/` 目录结构是否正确
- 确认文件命名格式为 `{section}_{week_label}.json`

## 技术支持

如有问题，请查看日志文件：

```bash
cat logs/weekly_report.log
```

## 相关文档

- [README.md](README.md) - 项目总览
- [SQL参数与口径说明.md](SQL参数与口径说明.md) - SQL口径详细说明
- [docs/OPTIMIZATION_HISTORY.md](docs/OPTIMIZATION_HISTORY.md) - 优化历史记录
- [docs/OPTIMIZATION_GUIDE.md](docs/OPTIMIZATION_GUIDE.md) - 优化指南
