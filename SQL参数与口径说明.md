# Coohom周报SQL查询参数与口径说明

**更新日期**: 2026-02-09
**数据源**: Metabase (database_id: 2)
**周报周期**: 每周一生成上周数据

---

## 通用参数说明

### 日期参数命名规则

- **当前周标签**: 使用周一日期作为周标签（YYYYMMDD格式）

  - 例如：`20260202` 表示 2026年2月2日（周一）开始的周
  - 实际数据范围：2026-02-02 至 2026-02-08（周日）
- **历史数据范围**: 固定为12-13周

  - 起始ds：一般为n周前的周一，根据当前周动态调整
  - 结束ds：一般为昨日或者为上周周日，根据当前周动态调整
- **快照日期(ds)**: 数据快照的日期

  - **s表快照（用户表,扩展表快照，收入invoice表）**: 使用 t+1 最新的一天（昨日）作为快照
    - 例如：`20260208` 表示2026年2月9日 t+1 最新的快照
  - **i表快照（各种日志表）**: 历史数据范围
    - 例如：20251229 ~ 20260208这段时间所有的增量数据   ->  ds >= '20251229' and ds <= '20260208'

### 用户类型定义

- **新用户**: 当周注册的用户
  - 判断标准：`user_created_week = created_week`
- **老用户**: 当周之前已注册的用户
  - 判断标准：`user_created_week < created_week`

---

## 1. 流量查询 (01_traffic_weekly.sql)

### 查询目的

统计各渠道的新访客数、注册数和转化率

### 关键参数

| 参数名称           | 当前值                                                                                                                                                 | 说明                    |
| ------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------ | ----------------------- |
| **数据范围** | `20251110` 至 `20260208`                                                                                                                           | 13周完整数据            |
| **时间维度** | `周`                                                                                                                                                 | 按周聚合（可改为日/月） |
| **渠道列表** | `'paid ads','organic search','referral','ai search','social media','email','affiliate & kol','operations','desktop app','mobile app search','other'` | 11个渠道                |

### 核心口径定义

#### 新访客数 (new_effective_guest_cnt)

```sql
-- 定义：首次访问且首次注册在当天的用户
count(distinct case
    when (
        (fst_registered_time is null)  -- 无首次注册时间
        or (date_format(fst_registered_time, '%Y%m%d') = created_day)  -- 或首次注册在当天
    )
    and (coalesce(date_format(fst_visit_coohom_time, '%Y%m%d'), created_day) = created_day)  -- 且首次访问在当天
    then qhdi
end)
```

**关键逻辑**：

- 排除历史注册用户在当天首次访问的情况
- 只统计当天新注册且有访问行为的用户

#### 新访客注册数 (new_effective_register_cnt)

```sql
-- 定义：新访客中当天完成注册的用户
count(distinct case
    when (
        (fst_registered_time is null)
        or (date_format(fst_registered_time, '%Y%m%d') = created_day)
    )
    and (coalesce(date_format(fst_visit_coohom_time, '%Y%m%d'), created_day) = created_day)
    then register_user_id
end)
```

#### 新访客注册转化率

```sql
-- 计算：新访客注册数 / 新访客数
new_effective_register_cnt / new_effective_guest_cnt
```

### 数据源表

- `hive_prod.exabrain.dwb_coohom_user_visit_register_i_d`
- 字段：`qhdi`, `visit_user_id`, `register_user_id`, `fst_registered_time`, `fst_visit_coohom_time`, `ads_channel_classify`

### 注意事项

- 渠道分类基于 `ads_channel_classify` 字段
- 转化率计算时，分母为0时返回NULL
- 时间维度可配置为日/周/月

---

## 2. 激活查询 (02_activation_ready.sql)

### 查询目的

统计新注册用户在工具中的激活转化漏斗

### 关键参数

| 参数名称                 | 当前值                                        | 说明                                            |
| ------------------------ | --------------------------------------------- | ----------------------------------------------- |
| **用户表快照**     | `ds = '20260209'`                           | ✅ 用户表快照：昨日（t+1前提下的最新的一天)     |
| **locale表快照**   | `ds = '20260209'`                           | ✅ locale表快照：昨日（t+1前提下的最新的一天)   |
| **设计表快照**     | `ds = '20260209'`                           | ✅ 设计表快照：昨日（t+1前提下的最新的一天)     |
| **qhdi扩展表快照** | `ds = '20260209'`                           | ✅ qhdi扩展表快照：昨日（t+1前提下的最新的一天) |
| **tag标签表快照**  | `ds = '20260209'`                           | ✅ tag标签表快照：昨日（t+1前提下的最新的一天)  |
| **注册日期范围**   | `20251110` 至 `20260208`                  | 13周数据，从第一周的周一到最后一周的周日        |
| **行为数据范围**   | `20251110` 至 `DATE_ADD('20260208', 6天)` | 延长6天观察转化                                 |
| **用户类型过滤**   | `['个人用户']`                              | 只统计个人用户                                  |
| **注册平台**       | `['PC Apps','WEB']`                         | PC和Web端注册                                   |
| **排除测试用户**   | `international_user_id <> 3099059`          | 排除特定测试账号                                |
| **删除状态**       | `deleted = false`                           | 只统计未删除用户                                |

### 核心口径定义

#### 转化漏斗步骤

1. **注册 → 进工具** (注册到进工具转化率)

   ```sql
   count(distinct user_with_pv) / count(distinct registered_users)
   ```

   - **定义**: 7天滚动窗口内PV > 6的用户
   - **计算**: 滚动7天总PV超过6次才算"进工具"
2. **进工具 → 画户型** (进工具到有效画户型转化率)

   ```sql
   count(distinct users_with_floorplan) / count(distinct users_entered_tool)
   ```

   - **定义**: 使用户型功能创建项目的用户
3. **画户型 → 拖模型** (有效画户型到有效拖模型转化率)

   ```sql
   count(distinct users_with_model_drag) / count(distinct users_with_floorplan)
   ```

   - **定义**: 拖拽模型到场景的用户
4. **拖模型 → 渲染** (有效拖模型到渲染转化率)

   ```sql
   count(distinct users_with_render) / count(distinct users_with_model_drag)
   ```

   - **定义**: 完成渲染操作的用户

#### 7天滚动窗口定义

```sql
-- 对于每个用户和日期，计算过去6天+当天的总PV
SUM(b.pv) AS total_pv
FROM user_daily_pv a
LEFT JOIN user_daily_pv b ON a.userid = b.userid
AND b.ds BETWEEN DATE_FORMAT(DATE_ADD(a.ds, INTERVAL -6 DAY), '%Y%m%d')
AND a.ds
HAVING SUM(b.pv) > 6  -- 7天总PV > 6
```

**关键逻辑**：

- 用户首次连续7天PV > 6的那一天记为"进工具"
- 这是用户真正开始使用工具的标志

### 数据源表

- **用户表**: `hive_prod.exabrain.dwb_usr_coohom_user_s_d`
- **行为表**: `hive_prod.kdw_log.dwd_log_yuntuModelAfterDrag`
- **扩展表**: `hive_prod.exabrain.dwb_usr_coohom_qhdi_extended_s_d`

### 注意事项

- **转化期未结束**: 最近一周的数据可能不完整，需要7天观察期
- **用户快照**: 使用周二快照确保数据完整性
- **PV阈值**: 7天PV > 6 是用户激活的经验阈值

---

## 3. 活跃查询 (03_engagement_new_old_users.sql)

### 查询目的

统计工具WAU（周活跃用户）及新老用户分解

### 关键参数

| 参数名称                 | 当前值               | 说明                 |
| ------------------------ | -------------------- | -------------------- |
| **上周数据结束日** | `ds <= '20260208'` | 上周最后一天周日之前 |
| **数据起始日**     | `ds >= '20251110'` | 固定起始周（周一)    |
| **用户类型**       | `'个人用户'`       | 只统计个人用户       |

### 核心口径定义

#### 工具WAU (Weekly Active Users)

```sql
count(DISTINCT user_id)  -- 去重用户ID
```

**定义**: 当周在工具有过任何操作的用户

#### 新老用户判断

```sql
if(user_created_week = created_week, '新注册', '老用户')
```

- **新注册**: 当周注册的用户
- **老用户**: 当周之前已注册的用户

#### 周定义

```sql
date_trunc('WEEK', str_to_date('20260208', '%Y%m%d'))  -- 周一
```

**定义**: 以周一作为周的开始

### 数据源表

- `hive_prod.exabrain.dw_flw_wt_coohomtool_i_d`
- 关键字段：`user_id`, `created_week`, `user_created_week`, `cohom_user_type`, `tool_name`, `active_country_sc`, `coohom_register_country_sc`

### 注意事项

- **周标签**: 使用周一日期代表整周
- **用户去重**: 同一用户在同一周只计数一次
- **数据完整性**: 上周数据使用 `<` 本周二，本周数据使用 `<=` 本周二

---

## 4. 留存查询 (04_retention.sql)

### 查询目的

统计工具用户的次周留存率（新老用户分别统计）

### 关键参数

| 参数名称               | 当前值                                       | 说明                         |
| ---------------------- | -------------------------------------------- | ---------------------------- |
| **上周数据范围** | `ds >= '20251110'` AND `ds < 上周周日`   | 从起始周周一到上周周日       |
| **本周数据范围** | `ds >= '20251110'` AND `ds <= yesterday` | 从起始周周一到 `yesterday` |
| **用户类型**     | `'个人用户'`                               | 只统计个人用户               |

### 核心口径定义

#### 工具次周留存率

```sql
count(DISTINCT thisweek.user_id) / count(DISTINCT lastweek.user_id)
```

**定义**: 上周活跃的用户在本周继续活跃的比例

#### 留存计算逻辑

```sql
-- 上周活跃
SELECT user_id, created_week
FROM dw_flw_wt_coohomtool_i_d
WHERE ds < '本周二'  -- 上周快照

-- 本周活跃 (LEFT JOIN)
SELECT user_id, last_created_week
FROM dw_flw_wt_coohomtool_i_d
WHERE ds <= '本周二'  -- 本周快照

-- 匹配条件
ON lastweek.user_id = thisweek.user_id
AND lastweek.created_week = thisweek.last_created_week  -- 同一周的用户
AND lastweek.active_user_type = thisweek.active_user_type  -- 同一类型
```

#### 新老用户留存分别计算

- **新用户留存**: 上周新注册用户在本周的留存率
- **老用户留存**: 上周老用户在本周的留存率

### 数据源表

- `hive_prod.exabrain.dw_flw_wt_coohomtool_i_d`
- 同活跃查询，但增加了本周匹配逻辑

### 注意事项

- **本周数据缺失**: 最新的周（如20260202）本周留存率为0%，因为下周数据尚未生成
- **历史周数据**: 显示历史周（如20260126）的留存率才有意义
- **用户类型匹配**: 必须保持用户类型一致（新→新，老→老）

---

## 5. 收入查询 (05_revenue.sql)

### 查询目的

统计订阅收入（总/新签/续约）、付费用户数、客单价

### 关键参数

| 参数名称                         | 当前值                                                     | 说明                                            |
| -------------------------------- | ---------------------------------------------------------- | ----------------------------------------------- |
| **用户表快照（exabrain）** | `ds = '20260209'`                                        | ✅ 用户表快照：昨日（t+1前提下的最新的一天)     |
| **用户表快照（kdw_dw）**   | `ds = '20260209'`                                        | ✅ 用户表快照：昨日（t+1前提下的最新的一天)     |
| **qhdi扩展表快照**         | `ds = '20260209'`                                        | ✅ qhdi扩展表快照：昨日（t+1前提下的最新的一天) |
| **交易表快照**             | `ds = '20260209'`                                        | ✅ 交易表快照：昨日（t+1前提下的最新的一天)     |
| **支付日期范围**           | `pay_success_day BETWEEN '20251110' AND '20260208'`      | 13周支付数据，从起始周周一到上周周日            |
| **订单类型**               | `'normal_subscription_mode', 'single_subscription_mode'` | 正常订阅+单品会员                               |
| **金额过滤**               | `coalesce(amt_usd, 0) > 0`                               | 只统计支付成功的订单                            |

### 核心口径定义

#### 总收入 (Total_Amt)

```sql
round(sum(coalesce(amt_usd, 0)), 1)  -- 美元，保留1位小数
```

**定义**: 所有支付成功的订单金额总和（美元）

#### 新签收入 (NewSubscribe_Amt)

```sql
round(sum(if(order_type_user = 'NewSubscribe', coalesce(amt_usd, 0), 0)), 1)
```

**定义**: 首次订阅用户的订单金额（新签）

#### 续约收入 (Renewal_Amt)

```sql
round(sum(if(order_type_user = 'Renewal', coalesce(amt_usd, 0), 0)), 1)
```

**定义**: 续费用户的订单金额（续约）

#### 订单类型判断 (order_type_user)

```sql
-- 根据用户历史订单判断
-- NewSubscribe: 用户首次订阅
-- Renewal: 用户非首次订阅
```

#### 付费用户数

```sql
count(DISTINCT if(sub_mode_type IN ('normal_subscription_mode', 'single_subscription_mode'), user_id, NULL))
```

**定义**: 支付成功的去重用户数（排除单品渲染券）

#### 客单价

```sql
总收入 / 付费用户数  -- 美元/人
```

### 数据源表

- **用户表**: `hive_prod.exabrain.dwb_usr_coohom_user_s_d`
- **交易表**: `hive_prod.kdw_dw.dws_coohom_trd_daily_toc_invoice_s_d`
- **渠道表**: `hive_prod.exabrain.dwb_usr_coohom_qhdi_extended_s_d`

### 用户过滤逻辑 (CTE usr)

```sql
-- 多表JOIN过滤符合条件的基础用户
1. dwb_usr_coohom_user_s_d (exabrain)  -- 注册信息
2. dwb_usr_coohom_user_s_d (kdw_dw)    -- locale信息
3. dwb_usr_coohom_qhdi_extended_s_d    -- 渠道信息
```

### 注意事项

- **快照日期**: 必须使用已生成的快照（周二），不能用未来日期
- **金额单位**: 统一使用美元（USD）
- **订单模式**: 排除 `single_coupon_mode`（单品买券）
- **收入完整性**: 本周数据可能不完整，因为订单有延迟到账

---

## 更新新周数据的步骤

### 1. 确定周标签

```bash
# 示例：生成2026年2月8日（周日）结束的周报
今日日期：20260210
最新快照日期(t+1也就是昨日):   20260209  (2月9日周二)
目标周标签（周一): 20260202  (2月2日周一，代表20260202~20260208这周)
目标周（周日): 20260208
上周标签（周一):   20260126  (1月26日周一， 代表20260126~20260201这周)
前12周的第一周标签（周一)：20251110  (开始周的周一)
```

### 2. 更新SQL文件中的日期参数

#### 01_traffic_weekly.sql

```sql
-- 第77行
(`ds` between '20251110' and '20260208')  -- 更新结束日期
```

#### 02_activation_ready.sql

```sql
-- 第69行：用户表快照（exabrain）
WHERE ds = '20260209'  

-- 第70行：注册日期范围
and created_day between '20251110' and '20260208'

-- 第84行：tag标签表快照
WHERE ds = '20260209'  

-- 第94行：locale表快照
where ds = '20260209'  

-- 第99行：qhdi扩展表快照
WHERE ds = '20260209'  

-- 第10行：行为数据范围
ds BETWEEN '20251110' AND DATE_FORMAT(DATE_ADD('20260208', INTERVAL 6 DAY), '%Y%m%d')  

-- 第120行：行为数据范围
ds between '20251110' and DATE_FORMAT(DATE_ADD('20260208', INTERVAL 6 DAY), '%Y%m%d')

-- 第147行：行为数据范围
ds between '20251110' and DATE_FORMAT(DATE_ADD('20260208', INTERVAL 6 DAY), '%Y%m%d')

-- 第132行：设计表快照
where ds = '20260209'  

```

#### 03_engagement_new_old_users.sql

```sql
-- 第6.7行
WHERE ds >= '20251110'
		AND ds <= '20260208'
```

#### 04_retention.sql

```sql
-- 第9行
AND ds < date_format(date_trunc('WEEK', str_to_date('20260208', '%Y%m%d')), '%Y%m%d')

-- 第24行
AND ds <= '20260208'
```

#### 05_revenue.sql

```sql
-- 第11行：用户表快照（exabrain）
WHERE ds = '20260209'

-- 第20行：用户表快照（kdw_dw）
WHERE ds = '20260209'

-- 第25行：qhdi扩展表快照
WHERE ds = '20260209'

-- 第61行：交易表快照
WHERE ds = '20260209'

-- 第62行：支付日期范围
AND pay_success_day BETWEEN '20251110' AND '20260208'
```

### 3. 执行数据提取

```bash
# 使用Metabase MCP工具逐个执行SQL
mcp__metabase__execute_sql_query(database_id=2, query=...)
```

### 4. 保存JSON数据

```bash
# 保存到output目录
traffic_weekly_20260202.json
activation_weekly_20260202.json
engagement_weekly_20260202.json
retention_weekly_20260202.json
revenue_weekly_20260202.json
```

### 5. 生成周报

```bash
python generate_weekly_report.py --week 20260202 --prev-week 20260126
```

---

## 常见问题排查

### 问题1: 收入查询返回0行

**可能原因**:

- 快照日期 `ds = '20260208'` 或 `ds = '20260209'` 不存在
- 用户过滤CTE过于严格

**解决方案**:

- 检查可用的快照日期:
  ```sql
  -- 用户表快照
  SELECT ds FROM hive_prod.exabrain.dwb_usr_coohom_user_s_d
  WHERE ds >= '20260202' GROUP BY ds ORDER BY ds DESC LIMIT 10

  -- 交易表快照
  SELECT ds FROM hive_prod.kdw_dw.dws_coohom_trd_daily_toc_invoice_s_d
  WHERE ds >= '20260202' GROUP BY ds ORDER BY ds DESC LIMIT 10
  ```
- 使用已存在的快照日期（通常用周日的快照 `ds = '20260208'`）

### 问题2: 留存率显示0%

**可能原因**:

- 本周（20260202）的留存率确实为0%，因为下周数据未生成
- 周报显示的是本周的留存率，而非上周

**解决方案**:

- 更新retention JSON的 `latest_week` 为上周标签
- 或在报告中标注"留存数据以上周为准"

### 问题3: 激活转化率异常

**可能原因**:

- 转化期未结束（需要7天观察）
- 数据快照时间过早

**解决方案**:

- 在报告中添加警告："⚠️ 本周数据 - 转化期未结束，仅供参考"
- 使用上上周数据进行完整对比

---

## 附录：数据表说明

### 用户相关表

| 表名                                   | 说明             | 关键字段                                                                                 |
| -------------------------------------- | ---------------- | ---------------------------------------------------------------------------------------- |
| `dwb_usr_coohom_user_s_d`            | 用户基础信息快照 | `kujiale_user_id`, `created_day`, `created_week`, `deleted`, `cohom_user_type` |
| `dwb_usr_coohom_qhdi_extended_s_d`   | 渠道扩展信息     | `qhdi`, `ads_channel_classify`                                                       |
| `dwb_coohom_user_visit_register_i_d` | 访问注册行为     | `qhdi`, `fst_visit_coohom_time`, `fst_registered_time`                             |

### 行为相关表

| 表名                            | 说明             | 关键字段                                                            |
| ------------------------------- | ---------------- | ------------------------------------------------------------------- |
| `dw_flw_wt_coohomtool_i_d`    | 工具活跃流水     | `user_id`, `created_week`, `user_created_week`, `tool_name` |
| `dwd_log_yuntuModelAfterDrag` | 云图模型操作日志 | `userid`, `ds`, PV计数                                          |

### 交易相关表

| 表名                                     | 说明         | 关键字段                                                                              |
| ---------------------------------------- | ------------ | ------------------------------------------------------------------------------------- |
| `dws_coohom_trd_daily_toc_invoice_s_d` | 交易订单快照 | `user_id`, `pay_success_day`, `amt_usd`, `order_type_user`, `sub_mode_type` |

---

**文档维护**: 每次更新周报参数时同步更新本文档
**责任人**: 数据分析团队
