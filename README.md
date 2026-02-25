# Coohom周报自动化更新系统

自动更新Confluence周报文档的Python脚本系统，支持流量、激活、活跃、留存、收入五个部分的数据自动生成和更新。

## 快速开始

详细的快速启动指南请查看 [QUICKSTART.md](QUICKSTART.md)

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 运行程序
python main.py
```

## 项目结构

```
weekly_report_automation/
├── config/                        # 配置文件
│   ├── config.yaml                # 主配置
│   └── sql_replacement_rules.yaml # SQL参数替换规则
│
├── sql/                           # SQL查询文件
│   ├── 01_traffic.sql             # 流量/投放数据
│   ├── 02_activation.sql           # 激活/注册漏斗
│   ├── 03_engagement_all_users.sql # 活跃-全用户
│   ├── 03_engagement_new_old_users.sql # 活跃-新老用户
│   ├── 04_retention.sql            # 留存数据
│   └── 05_revenue.sql              # 收入数据
│
├── src/                           # 源代码
│   ├── __init__.py
│   ├── date_utils.py              # 日期计算工具
│   ├── logger.py                  # 日志配置
│   ├── interactive_prompt.py      # 交互式提示
│   ├── sql_preprocessor.py        # SQL参数替换
│   ├── data_fetcher.py            # Metabase数据获取
│   ├── data_analyzer.py           # 环比计算和分析
│   ├── data_quality.py           # 数据验证和质量分析
│   ├── data_loader.py           # 统一数据加载接口
│   ├── metrics_extractor.py      # 指标提取器
│   ├── report_generator.py        # HTML/MD生成
│   └── confluence_updater.py      # Confluence更新
│
├── metrics/                       # 指标提取模块（待实现）
│   └── __init__.py
│
├── docs/                          # 文档
│   ├── OPTIMIZATION_HISTORY.md   # 优化历史
│   └── OPTIMIZATION_GUIDE.md    # 优化指南
│
├── main.py                        # 主入口（手动触发）
├── generate_weekly_report.py      # 简化版一键生成
├── requirements.txt               # 依赖包
├── README.md                     # 本文件
├── QUICKSTART.md                 # 快速启动指南
├── SQL参数与口径说明.md          # SQL口径文档
├── logs/                         # 日志目录
└── output/                       # 输出目录
    ├── archive/                  # 历史归档（按月）
    ├── cache/                   # 查询缓存
    └── sql_queries/             # SQL查询历史
```

## 功能特性

- 🗓️ 支持本周/下周/任意周更新
- 📊 支持收入MD文档或纯SQL数据（分支处理）
- 🔄 自动环比计算和趋势分析
- 🤖 交互式提示 + 定时任务双模式
- 📝 严格保持现有Confluence格式
- 🎨 彩色日志输出，易于追踪
- ✅ 数据质量验证和异常检测

## 安装步骤

### 1. 环境要求

- Python 3.8+
- pip

### 2. 安装依赖

```bash
cd weekly_report_automation
pip install -r requirements.txt
```

### 3. 配置文件

主要配置文件位于 `config/config.yaml`，已包含默认配置。

如需修改，请编辑以下内容：
- Metabase数据库ID
- Confluence页面ID
- SQL文件路径
- 日志配置等

## 使用方法

### 手动触发（推荐）

```bash
python main.py
```

系统会提示：
1. 选择目标周（本周/下周/指定日期）
2. 是否提供收入MD文档（可选）
3. 确认执行参数

### 一键生成

```bash
python generate_weekly_report.py
```

使用默认参数快速生成周报。

## 开发进度

### ✅ 第一阶段：基础框架（已完成）
- [x] 项目目录结构
- [x] SQL文件集成
- [x] 配置文件
- [x] 日期计算模块 (`src/date_utils.py`)
- [x] 日志配置模块 (`src/logger.py`)
- [x] 依赖文件 (`requirements.txt`)
- [x] README文档

### ✅ 第二阶段：核心功能（已完成）
- [x] 交互式提示模块 (`src/interactive_prompt.py`)
- [x] SQL参数替换模块 (`src/sql_preprocessor.py`)
- [x] Metabase数据获取 (`src/data_fetcher.py`)
- [x] 数据分析模块 (`src/data_analyzer.py`)
- [x] 数据质量验证 (`src/data_quality.py`)
- [x] 统一数据加载 (`src/data_loader.py`)
- [x] HTML生成模块 (`src/report_generator.py`)
- [x] Confluence更新模块 (`src/confluence_updater.py`)
- [x] 主流程整合 (`main.py`)
- [x] 一键生成脚本 (`generate_weekly_report.py`)

### ⏳ 第三阶段：优化和测试
- [x] 错误处理和日志完善
- [x] 数据质量分析
- [x] 单元测试
- [x] 端到端测试
- [x] 项目文件清理和重组
- [ ] 性能优化
- [ ] 指标提取模块拆分 (`metrics/` 目录)

## 核心模块说明

### date_utils.py - 日期计算

提供灵活的日期计算功能，支持任意周的参数计算。

```python
from src.date_utils import calculate_week_params, calculate_previous_week, calculate_week_end_date

# 本周
params = calculate_week_params()

# 下周
params = calculate_week_params(week_offset=1)

# 指定日期
params = calculate_week_params(target_date='20260201')

# 计算上周标签
previous_week = calculate_previous_week('2026w05')  # 返回 '2026w04'

# 计算周结束日期
end_date = calculate_week_end_date('2026w05')  # 返回 '20260201'
```

### data_loader.py - 数据加载

统一的数据加载接口，支持从归档目录加载历史数据。

```python
from src.data_loader import DataLoader

loader = DataLoader()

# 加载单个部分数据
data = loader.load_section_data(
    base_dir=Path('output/archive/2026-01/json'),
    section='traffic',
    week_label='2026w04'
)

# 加载所有部分数据
all_data = loader.load_all_sections(
    base_dir=Path('output/archive/2026-01/json'),
    week_label='2026w04',
    previous_week_label='2026w03'
)
```

### data_quality.py - 数据质量

数据验证和质量分析功能。

```python
from src.data_quality import DataValidator, DataQualityAnalyzer

validator = DataValidator()
analyzer = DataQualityAnalyzer()

# 数据完整性验证
is_valid, issues = validator.validate_data_completeness('traffic', data)

# 异常检测
anomalies = validator.check_anomalies('traffic', current_data, previous_data, 'new_visitors')

# 生成质量报告
report = analyzer.generate_quality_report(all_sections_data, all_sections_analysis)
```

### logger.py - 日志配置

统一的彩色日志系统，支持控制台和文件输出。

```python
from src.logger import setup_logging

logger = setup_logging(
    name='weekly_report',
    level='INFO',
    log_file='logs/weekly_report.log'
)
```

## SQL文件说明

所有SQL文件支持动态参数替换，支持的关键参数包括：

- `{partition_start}` / `{partition_end}`: 数据分区日期范围
- `{week_sunday}` / `{week_saturday}`: 周结束日期
- `{snapshot_date}`: 快照日期
- `{history_start_date}`: 历史数据起始日期（2个月前）
- `{pay_start_date}` / `{pay_end_date}`: 支付日期范围

## 测试

### 运行单元测试

```bash
pytest tests/
```

### 测试各模块

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

## 输出目录结构

系统会按月归档输出文件：

```
output/
├── archive/
│   └── 2026-01/
│       ├── json/          # JSON数据文件
│       └── reports/       # 生成的报告
├── cache/               # 查询缓存
└── sql_queries/         # SQL查询历史
```

## 故障排查

### 常见问题

1. **ImportError: No module named 'colorlog'**
   ```bash
   pip install colorlog
   ```

2. **SQL参数未替换**
   - 检查 `config/sql_replacement_rules.yaml` 中的pattern是否与SQL文件中的实际内容匹配

3. **Confluence版本冲突**
   - 系统会自动递增版本号，如仍有问题，检查 `confluence_updater.py` 中的版本管理逻辑

4. **数据加载失败**
   - 检查 `output/archive/` 目录结构是否正确
   - 确认文件命名格式为 `{section}_{week_label}.json`

## 贡献指南

本项目正在开发中，欢迎贡献代码和建议！

### 开发规范

1. 遵循现有代码风格
2. 添加适当的单元测试
3. 更新相关文档
4. 提交前运行 `pytest` 确保测试通过

## 许可证

内部项目 - Coohom Analytics

## 联系方式

如有问题，请联系项目负责人。

## 相关文档

- [QUICKSTART.md](QUICKSTART.md) - 快速启动指南
- [SQL参数与口径说明.md](SQL参数与口径说明.md) - SQL口径详细说明
- [docs/OPTIMIZATION_HISTORY.md](docs/OPTIMIZATION_HISTORY.md) - 优化历史记录
- [docs/OPTIMIZATION_GUIDE.md](docs/OPTIMIZATION_GUIDE.md) - 优化指南
