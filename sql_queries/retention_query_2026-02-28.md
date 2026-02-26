# RETENTION SQL Query - 2026-02-28

## 数据参数

- **target_date**: `2026-02-28`

## SQL文件
04_retention.sql

## 完整SQL语句
```sql
SELECT
    lastweek.created_week AS 上周,
    lastweek.active_user_type AS 上周用户类型,
    COUNT(DISTINCT lastweek.user_id) AS 上周工具WAU,
    COUNT(DISTINCT thisweek.user_id) AS 本周工具WAU,
    IF(COUNT(DISTINCT lastweek.user_id) = 0, 0.0, ROUND(CAST(COUNT(DISTINCT thisweek.user_id) AS DOUBLE) / CAST(COUNT(DISTINCT lastweek.user_id) AS DOUBLE), 4)) AS 工具次周留存
FROM (
    SELECT
        user_id,
        created_week,
        user_created_week,
        coohom_user_type,
        IF(user_created_week = created_week, '新注册', '老用户') AS active_user_type
    FROM hive_prod.exabrain.dw_flw_wt_coohomtool_i_d
    WHERE ds >= DATE_FORMAT(DATE_SUB(DATE_TRUNC('week', CURRENT_DATE()), INTERVAL '12' WEEK), '%Y%m%d')
        AND ds < DATE_FORMAT(DATE_TRUNC('week', CURRENT_DATE()), '%Y%m%d')
        AND user_id IS NOT NULL
        AND ARRAY_CONTAINS(['个人用户'], coohom_user_type)
    GROUP BY user_id, created_week, user_created_week, coohom_user_type, IF(user_created_week = created_week, '新注册', '老用户')
) lastweek
LEFT JOIN (
    SELECT
        user_id,
        created_week,
        user_created_week,
        last_created_week,
        coohom_user_type,
        IF(user_created_week = last_created_week, '新注册', '老用户') AS active_user_type
    FROM hive_prod.exabrain.dw_flw_wt_coohomtool_i_d
    WHERE ds >= DATE_FORMAT(DATE_SUB(DATE_TRUNC('week', CURRENT_DATE()), INTERVAL '12' WEEK), '%Y%m%d')
        AND ds <= DATE_FORMAT(CURRENT_DATE() - INTERVAL '1' DAY, '%Y%m%d')
        AND user_id IS NOT NULL
        AND ARRAY_CONTAINS(['个人用户'], coohom_user_type)
    GROUP BY user_id, created_week, user_created_week, last_created_week, coohom_user_type, IF(user_created_week = last_created_week, '新注册', '老用户')
) thisweek
ON lastweek.user_id = thisweek.user_id
    AND lastweek.created_week = thisweek.last_created_week
    AND lastweek.active_user_type = thisweek.active_user_type
GROUP BY lastweek.created_week, lastweek.active_user_type
ORDER BY 上周
LIMIT 10000

```

---
*生成时间: 2026-02-26 12:03:17
