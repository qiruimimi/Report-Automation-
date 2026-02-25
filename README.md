<<<<<<< HEAD
# Coohom周报自动化更新系统

自动更新Confluence周报文档的Python脚本系统，支持流量、激活、活跃、留存、收入五个部分的数据自动生成和更新。

## 🚀 快速开始

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
│   ├── config.yaml                # 主配置 ✅
│   └── sql_replacement_rules.yaml # SQL参数替换规则 ✅
│
├── sql/                           # SQL查询文件 ✅
│   ├── 01_traffic.sql             # 流量/投放数据
│   ├── 02_activation.sql           # 激活/注册漏斗
│   ├── 03_engagement_all_users.sql # 活跃-全用户
│   ├── 03_engagement_new_old_users.sql # 活跃-新老用户
│   ├── 04_retention.sql            # 留存数据
│   └── 05_revenue.sql              # 收入数据
│
├── src/                           # 源代码
│   ├── __init__.py                 ✅
│   ├── date_utils.py              # 日期计算工具 ✅
│   ├── logger.py                  # 日志配置 ✅
│   ├── interactive_prompt.py      # 交互式提示 ✅
│   ├── sql_preprocessor.py        # SQL参数替换 ✅
│   ├── data_fetcher.py            # Metabase数据获取 ✅
│   ├── data_analyzer.py           # 环比计算和分析 ✅
│   ├── report_generator.py        # HTML/MD生成 ✅
│   └── confluence_updater.py      # Confluence更新 ✅
│
├── main.py                        # 主入口（手动触发）✅
├── requirements.txt               # 依赖包 ✅
├── README.md                      # 本文件 ✅
├── QUICKSTART.md                  # 快速启动指南 ✅
├── logs/                          # 日志目录
└── output/                        # 临时输出目录
```

✅ = 已完成  ⏳ = 待完善

## 功能特性

- 🗓️ 支持本周/下周/任意周更新
- 📊 支持收入MD文档或纯SQL数据（分支处理）
- 🔄 自动环比计算和趋势分析
- 🤖 交互式提示 + 定时任务双模式
- 📝 严格保持现有Confluence格式
- 🎨 彩色日志输出，易于追踪

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

### 定时任务

```bash
python run_scheduled.py
```

按配置文件中的时间自动执行（默认：每周三上午10:00）

## 开发进度

### ✅ 第一阶段：基础框架（已完成）
- [x] 项目目录结构
- [x] SQL文件集成
- [x] 配置文件
- [x] 日期计算模块 (`src/date_utils.py`)
- [x] 日志配置模块 (`src/logger.py`)
- [x] 依赖文件 (`requirements.txt`)
- [x] README文档

### ⏳ 第二阶段：核心功能（待实现）
- [ ] 交互式提示模块 (`src/interactive_prompt.py`)
- [ ] SQL参数替换模块 (`src/sql_preprocessor.py`)
- [ ] Metabase数据获取 (`src/data_fetcher.py`)
- [ ] 数据分析模块 (`src/data_analyzer.py`)
- [ ] HTML生成模块 (`src/report_generator.py`)
- [ ] Confluence更新模块 (`src/confluence_updater.py`)
- [ ] 主流程整合 (`main.py`)
- [ ] 定时任务实现 (`run_scheduled.py`)

### ⏳ 第三阶段：优化和测试
- [ ] 错误处理和日志完善
- [ ] 单元测试
- [ ] 端到端测试
- [ ] 性能优化

## 核心模块说明

### date_utils.py - 日期计算

提供灵活的日期计算功能，支持任意周的参数计算。

```python
from src.date_utils import calculate_week_params

# 本周
params = calculate_week_params()

# 下周
params = calculate_week_params(week_offset=1)

# 指定日期
params = calculate_week_params(target_date='20260201')
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

### 测试日期工具

```bash
python src/date_utils.py
```

### 测试日志配置

```bash
python src/logger.py
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

## 贡献指南

本项目正在开发中，欢迎贡献代码和建议！

## 许可证

内部项目 - Coohom Analytics

## 联系方式

如有问题，请联系项目负责人。
=======
# Report Automation



## Getting started

To make it easy for you to get started with GitLab, here's a list of recommended next steps.

Already a pro? Just edit this README.md and make it your own. Want to make it easy? [Use the template at the bottom](#editing-this-readme)!

## Add your files

- [ ] [Create](https://docs.gitlab.com/ee/user/project/repository/web_editor.html#create-a-file) or [upload](https://docs.gitlab.com/ee/user/project/repository/web_editor.html#upload-a-file) files
- [ ] [Add files using the command line](https://docs.gitlab.com/ee/gitlab-basics/add-file.html#add-a-file-using-the-command-line) or push an existing Git repository with the following command:

```
cd existing_repo
git remote add origin https://gitlab.qunhequnhe.com/shuhang/report-automation.git
git branch -M master
git push -uf origin master
```

## Integrate with your tools

- [ ] [Set up project integrations](https://gitlab.qunhequnhe.com/shuhang/report-automation/-/settings/integrations)

## Collaborate with your team

- [ ] [Invite team members and collaborators](https://docs.gitlab.com/ee/user/project/members/)
- [ ] [Create a new merge request](https://docs.gitlab.com/ee/user/project/merge_requests/creating_merge_requests.html)
- [ ] [Automatically close issues from merge requests](https://docs.gitlab.com/ee/user/project/issues/managing_issues.html#closing-issues-automatically)
- [ ] [Enable merge request approvals](https://docs.gitlab.com/ee/user/project/merge_requests/approvals/)
- [ ] [Automatically merge when pipeline succeeds](https://docs.gitlab.com/ee/user/project/merge_requests/merge_when_pipeline_succeeds.html)

## Test and Deploy

Use the built-in continuous integration in GitLab.

- [ ] [Get started with GitLab CI/CD](https://docs.gitlab.com/ee/ci/quick_start/index.html)
- [ ] [Analyze your code for known vulnerabilities with Static Application Security Testing(SAST)](https://docs.gitlab.com/ee/user/application_security/sast/)
- [ ] [Deploy to Kubernetes, Amazon EC2, or Amazon ECS using Auto Deploy](https://docs.gitlab.com/ee/topics/autodevops/requirements.html)
- [ ] [Use pull-based deployments for improved Kubernetes management](https://docs.gitlab.com/ee/user/clusters/agent/)
- [ ] [Set up protected environments](https://docs.gitlab.com/ee/ci/environments/protected_environments.html)

***

# Editing this README

When you're ready to make this README your own, just edit this file and use the handy template below (or feel free to structure it however you want - this is just a starting point!).  Thank you to [makeareadme.com](https://www.makeareadme.com/) for this template.

## Suggestions for a good README
Every project is different, so consider which of these sections apply to yours. The sections used in the template are suggestions for most open source projects. Also keep in mind that while a README can be too long and detailed, too long is better than too short. If you think your README is too long, consider utilizing another form of documentation rather than cutting out information.

## Name
Choose a self-explaining name for your project.

## Description
Let people know what your project can do specifically. Provide context and add a link to any reference visitors might be unfamiliar with. A list of Features or a Background subsection can also be added here. If there are alternatives to your project, this is a good place to list differentiating factors.

## Badges
On some READMEs, you may see small images that convey metadata, such as whether or not all the tests are passing for the project. You can use Shields to add some to your README. Many services also have instructions for adding a badge.

## Visuals
Depending on what you are making, it can be a good idea to include screenshots or even a video (you'll frequently see GIFs rather than actual videos). Tools like ttygif can help, but check out Asciinema for a more sophisticated method.

## Installation
Within a particular ecosystem, there may be a common way of installing things, such as using Yarn, NuGet, or Homebrew. However, consider the possibility that whoever is reading your README is a novice and would like more guidance. Listing specific steps helps remove ambiguity and gets people to using your project as quickly as possible. If it only runs in a specific context like a particular programming language version or operating system or has dependencies that have to be installed manually, also add a Requirements subsection.

## Usage
Use examples liberally, and show the expected output if you can. It's helpful to have inline the smallest example of usage that you can demonstrate, while providing links to more sophisticated examples if they are too long to reasonably include in the README.

## Support
Tell people where they can go to for help. It can be any combination of an issue tracker, a chat room, an email address, etc.

## Roadmap
If you have ideas for releases in the future, it is a good idea to list them in the README.

## Contributing
State if you are open to contributions and what your requirements are for accepting them.

For people who want to make changes to your project, it's helpful to have some documentation on how to get started. Perhaps there is a script that they should run or some environment variables that they need to set. Make these steps explicit. These instructions could also be useful to your future self.

You can also document commands to lint the code or run tests. These steps help to ensure high code quality and reduce the likelihood that the changes inadvertently break something. Having instructions for running tests is especially helpful if it requires external setup, such as starting a Selenium server for testing in a browser.

## Authors and acknowledgment
Show your appreciation to those who have contributed to the project.

## License
For open source projects, say how it is licensed.

## Project status
If you have run out of energy or time for your project, put a note at the top of the README saying that development has slowed down or stopped completely. Someone may choose to fork your project or volunteer to step in as a maintainer or owner, allowing your project to keep going. You can also make an explicit request for maintainers.
>>>>>>> 7d0902d3ec1db35ffa4a10b9d7aa408788e9c33c
