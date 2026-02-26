# REVENUE SQL Query - 2026-02-28

## 数据参数

- **target_date**: `2026-02-28`

## SQL文件
05_revenue.sql

## 完整SQL语句
```sql
WITH usr AS (
    SELECT
        usr_1.userid
    FROM (
        SELECT
            CASE '周'
                WHEN '周' THEN created_week
                WHEN '日' THEN created_day
                WHEN '月' THEN CONCAT(SUBSTR(created_day, 1, 6), '01')
            END AS created_time,
            created_day,
            created_week,
            kujiale_user_id AS userid,
            ds,
            qhdi
        FROM hive_prod.exabrain.dwb_usr_coohom_user_s_d
        WHERE ds = DATE_FORMAT(CURRENT_DATE() - INTERVAL '1' DAY, '%Y%m%d')
    ) usr_1
    INNER JOIN (
        SELECT kujiale_user_id AS userid, locale_site, locale
        FROM hive_prod.kdw_dw.dwb_usr_coohom_user_s_d
        WHERE ds = DATE_FORMAT(CURRENT_DATE() - INTERVAL '1' DAY, '%Y%m%d')
    ) usr_2 ON usr_1.userid = usr_2.userid
    LEFT JOIN (
        SELECT qhdi, ads_channel_classify
        FROM hive_prod.exabrain.dwb_usr_coohom_qhdi_extended_s_d
        WHERE ds = DATE_FORMAT(CURRENT_DATE() - INTERVAL '1' DAY, '%Y%m%d')
    ) qhdi ON usr_1.qhdi = qhdi.qhdi
),
revenue_data AS (
    SELECT
        pay_success_week AS 日期,
        amt_usd,
        order_type_user,
        sub_mode_type,
        user_id
    FROM hive_prod.kdw_dw.dws_coohom_trd_daily_toc_invoice_s_d
    WHERE ds = DATE_FORMAT(CURRENT_DATE() - INTERVAL '1' DAY, '%Y%m%d')
        AND pay_success_day BETWEEN DATE_FORMAT(DATE_SUB(DATE_TRUNC('week', CURRENT_DATE()), INTERVAL '12' WEEK), '%Y%m%d')
            AND DATE_FORMAT(DATE_TRUNC('week', CURRENT_DATE()) - INTERVAL '1' DAY, '%Y%m%d')
        AND COALESCE(amt_usd, 0) > 0
        AND kjl_user_id IN (SELECT * FROM usr)
)
SELECT
    日期,
    ROUND(SUM(COALESCE(amt_usd, 0)), 1) AS 总收入,
    ROUND(SUM(IF(order_type_user = 'NewSubscribe', COALESCE(amt_usd, 0), 0)), 1) AS 新签收入,
    ROUND(SUM(IF(order_type_user = 'Renewal', COALESCE(amt_usd, 0), 0)), 1) AS 续约收入,
    COUNT(DISTINCT IF(sub_mode_type IN ('normal_subscription_mode', 'single_subscription_mode'), user_id, NULL)) AS 付费用户数,
    COUNT(DISTINCT IF(order_type_user = 'NewSubscribe' AND sub_mode_type IN ('normal_subscription_mode', 'single_subscription_mode'), user_id, NULL)) AS 新签用户数,
    COUNT(DISTINCT IF(order_type_user = 'Renewal' AND sub_mode_type IN ('normal_subscription_mode', 'single_subscription_mode'), user_id, NULL)) AS 续约用户数,
    ROUND(IF(COUNT(DISTINCT IF(sub_mode_type IN ('normal_subscription_mode', 'single_subscription_mode'), user_id, NULL)) = 0, NULL, SUM(IF(sub_mode_type IN ('normal_subscription_mode', 'single_subscription_mode'), COALESCE(amt_usd, 0), 0)) * 1.00 / COUNT(DISTINCT IF(sub_mode_type IN ('normal_subscription_mode', 'single_subscription_mode'), user_id, NULL))), 1) AS 整体客单价,
    ROUND(IF(COUNT(DISTINCT IF(order_type_user = 'NewSubscribe' AND sub_mode_type IN ('normal_subscription_mode', 'single_subscription_mode'), user_id, NULL)) = 0, NULL, SUM(IF(order_type_user = 'NewSubscribe' AND sub_mode_type IN ('normal_subscription_mode', 'single_subscription_mode'), COALESCE(amt_usd, 0), 0)) * 1.00 / COUNT(DISTINCT IF(order_type_user = 'NewSubscribe' AND sub_mode_type IN ('normal_subscription_mode', 'single_subscription_mode'), user_id, NULL))), 1) AS 新签客单价,
    COALESCE(ROUND(IF(COUNT(DISTINCT IF(order_type_user = 'Renewal' AND sub_mode_type IN ('normal_subscription_mode', 'single_subscription_mode'), user_id, NULL)) = 0, NULL, SUM(IF(order_type_user = 'Renewal' AND sub_mode_type IN ('normal_subscription_mode', 'single_subscription_mode'), COALESCE(amt_usd, 0), 0)) * 1.00 / COUNT(DISTINCT IF(order_type_user = 'Renewal' AND sub_mode_type IN ('normal_subscription_mode', 'single_subscription_mode'), user_id, NULL))), 1), 0) AS 续约客单价
FROM revenue_data
GROUP BY 日期
ORDER BY 日期
LIMIT 1000000

```

---
*生成时间: 2026-02-26 12:03:19
