# Coohom平台整体数据周报

**报告日期**: {{ report_date }}
**数据周**: {{ data_week }} (截止{{ data_end_date }})

---

## 1.流量

### 整体表现

- 总新访客: **{{ total_visitors }}人**
- 总注册数: **{{ total_registrations }}人**
- 整体转化率: **{{ conversion_rate }}%**

### 环比上周变化

- 新访客: **{{ visitors_change_str }}**
- 注册数: **{{ registrations_change_str }}**
- 注册转化率: **{{ conversion_change_str }}**

### 注意项

{% if attention_items %}
{% for item in attention_items %}
- {{ item }}
{% endfor %}
{% else %}

暂无特别注意事项。
{% endif %}

---

## 2.激活

### 完整数据对比（{{ previous_week_label }} vs {{ current_week_label }}）

| 步骤            | 上上周 ({{ previous_week_label }}) | 上周 ({{ current_week_label }}) | 变化         |
| --------------- | --------------------------------- | -------------------------- | ------------ |
{% for step in funnel_steps %}
| {{ step.name }}     | {{ step.previous_rate }}%         | {{ step.current_rate }}%   | {{ step.change_str }} |
{% endfor %}
| **总转化率**    | {{ overall_previous_rate }}%         | {{ overall_current_rate }}%   | {{ overall_change_str }} |

{% if is_current_week_incomplete %}
### ⚠️ 本周数据（{{ current_week_label }}）- 转化期未结束，仅供参考

| 指标             | 本周 ({{ current_week_label }}) | 说明                       |
| ---------------- | ----------------------------- | -------------------------- |
{% for metric in current_week_metrics %}
| {{ metric.name }} | {{ metric.value }}     | {{ metric.note }}           |
{% endfor %}
{% endif %}

### 历史趋势

{% if historical_trends %}
{% for trend in historical_trends %}
- {{ trend }}
{% endfor %}
{% endif %}

---

## 3.活跃

- 当周WAU达到 **{{ wau }}人**，环比上周{{ wau_change_str }}，主要是{{ wau_contribution }}
- 新用户WAU: {{ new_user_wau }}人（环比{{ new_user_wau_change_str }}）
- 老用户WAU: {{ old_user_wau }}人（环比{{ old_user_wau_change_str }}）

### 历史趋势

- {{ historical_weeks }}周历史平均WAU: **{{ historical_avg_wau }}人**

{% if attention_items %}
### 注意项
{% for item in attention_items %}
- {{ item }}
{% endfor %}
{% endif %}

---

## 4.留存

### 新用户留存率：**{{ new_user_retention_rate }}%**

- 新用户留存率从{{ new_user_retention_previous }}%提升至{{ new_user_retention_current }}%，从{{ new_user_retention_min }}%下降至{{ new_user_retention_max }}%，处于近12周{{ new_user_retention_level }}水平

### 老用户留存率：**{{ old_user_retention_rate }}%**

- 老用户留存率从{{ old_user_retention_previous }}%提升至{{ old_user_retention_current }}%，从{{ old_user_retention_min }}%下降至{{ old_user_retention_max }}%，{{ old_user_trend_note }}

### 历史趋势（近12周）

- 新用户次周留存平均值: **{{ historical_new_user_avg }}%**
- 老用户次周留存平均值: **{{ historical_old_user_avg }}%**

{% if insights %}
### 留存率分化洞察
{% for insight in insights %}
- {{ insight }}
{% endfor %}
{% endif %}

---

## 5.收入

当周收入 **{{ total_revenue }} 美元**，较上周{{ previous_revenue }} 美元{{ revenue_change_str }}，增长率 {{ revenue_growth_rate }}%。

其中，续约收入{{ renewal_revenue }} 美元（增长率 {{ renewal_growth_rate }}%），新签收入{{ new_signing_revenue }} 美元（增长率 {{ new_signing_growth_rate }}%）。

### AI 总结

{{ ai_summary }}

### 正常收入({{ total_revenue }} 美元) 分析

- 收入类型：{{ revenue_type }}
- 用户数：{{ user_count }}
- 客单价：{{ average_order_value }}

{% if historical_trends %}
### 历史趋势

- {{ historical_weeks }}周平均收入: **{{ historical_avg_revenue }} 美元**
{% for trend in historical_trends %}
- {{ trend }}
{% endfor %}
{% endif %}

---

## 6.核心洞察与建议

### 正向趋势

{% for insight in positive_insights %}
- {{ insight }}
{% endfor %}

{% if negative_insights %}
### 需要关注的问题

{% for insight in negative_insights %}
- {{ insight }}
{% endfor %}
{% endif %}

### 行动建议

#### 短期建议（1-2周）

{% for suggestion in short_term_suggestions %}
- {{ suggestion }}
{% endfor %}

#### 中期建议（1-2月）

{% for suggestion in medium_term_suggestions %}
- {{ suggestion }}
{% endfor %}

#### 长期建议（3-6月）

{% for suggestion in long_term_suggestions %}
- {{ suggestion }}
{% endfor %}

---

**数据来源**: Metabase (database_id: {{ database_id }})
**报告生成器**: Coohom周报自动化系统 v2.0
**执行时间**: {{ execution_time }}
