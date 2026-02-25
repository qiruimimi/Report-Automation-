# Coohom平台整体数据周报

**报告日期**: {{report_date}}
**数据周**: {{week_label}} (截止{{week_end_date}})

---

## 1.流量

**整体表现**

- 总新访客: **{{traffic_total_guests|format_number}}人**
- 总注册数: **{{traffic_total_registers|format_number}}人**
- 整体转化率: **{{traffic_conversion_rate}}%**

**环比上周变化**

- 新访客: **{{traffic_guests_wow}}** {{traffic_guests_trend}}
- 注册数: **{{traffic_registers_wow}}** {{traffic_registers_trend}}
- 注册转化率: **{{traffic_conversion_wow}}** {{traffic_conversion_trend}}

**注意项**

{% for note in traffic_notes %}
- **{{note.channel}}:** {{note.description}}
{% endfor %}

---

## 2.激活

**完整数据对比（{{last_last_week_label}} vs {{last_week_label}}）**

| 步骤            | 上上周 ({{last_last_week_label}}) | 上周 ({{last_week_label}}) | 变化         |
| --------------- | --------------------------------- | -------------------------- | ------------ |
| 注册→进工具     | {{activation_step1_llw}}%         | {{activation_step1_lw}}%   | {{activation_step1_change}} |
| 进工具→画户型   | {{activation_step2_llw}}%         | {{activation_step2_lw}}%   | {{activation_step2_change}} |
| 画户型→拖模型   | {{activation_step3_llw}}%         | {{activation_step3_lw}}%   | {{activation_step3_change}} |
| 拖模型→渲染     | {{activation_step4_llw}}%         | {{activation_step4_lw}}%   | {{activation_step4_change}} |
| **总转化率**    | {{activation_total_llw}}%         | {{activation_total_lw}}%   | {{activation_total_change}} |

{% if incomplete_data %}
**⚠️ 本周数据（{{current_week_label}}）- 转化期未结束，仅供参考**

| 指标             | 本周 ({{current_week_label}}) | 说明                       |
| ---------------- | ----------------------------- | -------------------------- |
| 新注册用户数     | {{activation_new_users}}      | 与流量数据一致             |
| 注册→进工具      | {{activation_step1_curr}}%    | 转化率正常                 |
| 进工具→画户型    | {{activation_step2_curr}}%    | ⚠️ 数据不完整，仍在转化期   |
| 画户型→拖模型    | {{activation_step3_curr}}%    | ⚠️ 数据不完整              |
| 拖模型→渲染      | {{activation_step4_curr}}%    | ⚠️ 数据不完整              |
{% endif %}

---

## 3.活跃

- 当周WAU达到 **{{engagement_total_wau|format_number}}人**，环比上周{{engagement_wow}}%，主要是{{engagement_driver}}贡献
- 新用户WAU: {{engagement_new_wau|format_number}}人（环比{{engagement_new_wow}}%）
- 老用户WAU: {{engagement_old_wau|format_number}}人（环比{{engagement_old_wow}}%）

**历史趋势**

- 25周历史平均WAU: **{{engagement_historical_avg|format_number}}**人

---

## 4.留存

**新用户留存率：** **{{retention_new_rate}}%**

- 新用户留存率从{{retention_new_last}}%提升至{{retention_new_rate}}%，{{retention_new_trend}}

**老用户留存率：** **{{retention_old_rate}}%**

- 老用户留存率从{{retention_old_last}}%提升至{{retention_old_rate}}%，{{retention_old_trend}}

**历史趋势（近12周）**

- 新用户次周留存平均值: **{{retention_new_12w_avg}}%**
- 老用户次周留存平均值: **{{retention_old_12w_avg}}%**

---

## 5.收入

**当周收入 {{revenue_total|format_number}} 美元**，较上周{{revenue_change_abs|format_number}} 美元{{revenue_trend}}，增长率 {{revenue_change_rate}}%。

其中，续约收入{{revenue_renewal_change}} 美元（增长率 {{revenue_renewal_rate}}%），新签收入{{revenue_new_change}} 美元（增长率 {{revenue_new_rate}}%）。

**1、AI 总结**

{{revenue_ai_summary}}

**2、正常收入({{revenue_normal_change}} 美元) 分析**

- 收入类型：{{revenue_type_analysis}}
- 用户数：{{revenue_users_analysis}}
- 客单价：{{revenue_arpu_analysis}}

{% if revenue_sku_analysis %}
**3、SKU维度分析**

{{revenue_sku_analysis}}
{% endif %}

{% if revenue_country_analysis %}
**4、国家维度分析**

{{revenue_country_analysis}}
{% endif %}

{% if revenue_tier_analysis %}
**5、账单分层分析**

{{revenue_tier_analysis}}
{% endif %}

---

**数据来源**: Metabase (database_id: {{database_id}})
**报告生成器**: Coohom周报自动化系统 v2.0
**执行时间**: {{execution_time}}
