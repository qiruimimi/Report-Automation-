# ACTIVATION SQL Query - 2026-02-25

## 数据参数


## SQL文件
02_activation_ready.sql

## 完整SQL语句
```sql
WITH user_daily_pv AS (
    -- Step 1: 按照日期和用户统计每日 PV
    SELECT
        userid,
        ds,
        COUNT(1) AS pv
    FROM hive_prod.kdw_log.dwd_log_yuntuModelAfterDrag
    WHERE ds BETWEEN DATE_FORMAT(DATE_SUB(DATE_TRUNC('week', CURRENT_DATE()), INTERVAL '8' WEEK), '%Y%m%d')
        AND DATE_FORMAT(DATE_ADD(DATE_TRUNC('week', CURRENT_DATE()) - INTERVAL '1' DAY, INTERVAL '6' DAY), '%Y%m%d')
    GROUP BY userid, ds
),
user_rolling_pv AS (
    -- Step 2: 计算滚动窗口内7天的总 PV
    SELECT
        a.userid,
        a.ds,
        SUM(b.pv) AS total_pv
    FROM user_daily_pv a
    LEFT JOIN user_daily_pv b ON a.userid = b.userid
        AND b.ds BETWEEN DATE_FORMAT(DATE_ADD(a.ds, INTERVAL -6 DAY), '%Y%m%d') AND a.ds
    GROUP BY a.userid, a.ds
    HAVING SUM(b.pv) > 6
),
e AS (
    SELECT
        userid,
        MIN(ds) AS ds
    FROM user_rolling_pv
    GROUP BY userid
)
SELECT
    a.created_time AS `日期`,
    COUNT(DISTINCT a.userid) AS `新注册用户数`,
    ROUND(COUNT(DISTINCT b.userid) / CAST(COUNT(DISTINCT a.userid) AS DOUBLE), 6) AS `注册到进工具转化率`,
    COUNT(DISTINCT b.userid) AS `进工具用户数`,
    ROUND(COUNT(DISTINCT d.userid) / CAST(COUNT(DISTINCT b.userid) AS DOUBLE), 6) AS `进工具到有效画户型转化率`,
    COUNT(DISTINCT d.userid) AS `有效画户型用户数`,
    ROUND(COUNT(DISTINCT e.userid) / CAST(COUNT(DISTINCT d.userid) AS DOUBLE), 6) AS `有效画户型到有效拖模型转化率`,
    COUNT(DISTINCT e.userid) AS `有效拖模型用户数`,
    ROUND(COUNT(DISTINCT c.userid) / CAST(COUNT(DISTINCT e.userid) AS DOUBLE), 6) AS `有效拖模型到渲染转化率`,
    COUNT(DISTINCT c.userid) AS `渲染用户数`,
    ROUND(COUNT(DISTINCT b.userid) / CAST(COUNT(DISTINCT a.userid) AS DOUBLE), 6) AS `进工具总转化率`,
    ROUND(COUNT(DISTINCT d.userid) / CAST(COUNT(DISTINCT a.userid) AS DOUBLE), 6) AS `有效画户型总转化率`,
    ROUND(COUNT(DISTINCT e.userid) / CAST(COUNT(DISTINCT a.userid) AS DOUBLE), 6) AS `有效拖模型总转化率`,
    ROUND(COUNT(DISTINCT c.userid) / CAST(COUNT(DISTINCT a.userid) AS DOUBLE), 6) AS `渲染总转化率`
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
        usr_2.locale_site,
        usr_2.locale,
        qhdi_ext.ads_channel_classify
    FROM (
        SELECT
            CASE '周'
                WHEN '周' THEN created_week
                WHEN '日' THEN created_day
                WHEN '月' THEN CONCAT(SUBSTR(created_day, 1, 6), '01')
            END AS created_time,
            created_day,
            created_week,
            kujiale_user_id,
            ds,
            qhdi
        FROM hive_prod.exabrain.dwb_usr_coohom_user_s_d
        WHERE ds = DATE_FORMAT(CURRENT_DATE() - INTERVAL '1' DAY, '%Y%m%d')
            AND created_day BETWEEN DATE_FORMAT(DATE_SUB(DATE_TRUNC('week', CURRENT_DATE()), INTERVAL '8' WEEK), '%Y%m%d')
                AND DATE_FORMAT(DATE_TRUNC('week', CURRENT_DATE()) - INTERVAL '1' DAY, '%Y%m%d')
            AND ARRAY_CONTAINS(['个人用户'], coohom_user_type)
            AND ARRAY_CONTAINS(['PC Apps', 'WEB'], coohom_register_platform)
            AND deleted = FALSE
            AND international_user_id <> 3099059
    ) usr_1
    INNER JOIN (
        SELECT kujiale_user_id AS userid, locale_site, locale
        FROM hive_prod.kdw_dw.dwb_usr_coohom_user_s_d
        WHERE ds = DATE_FORMAT(CURRENT_DATE() - INTERVAL '1' DAY, '%Y%m%d')
    ) usr_2 ON usr_1.kujiale_user_id = usr_2.userid
    LEFT JOIN (
        SELECT qhdi, ads_channel_classify
        FROM hive_prod.exabrain.dwb_usr_coohom_qhdi_extended_s_d
        WHERE ds = DATE_FORMAT(CURRENT_DATE() - INTERVAL '1' DAY, '%Y%m%d')
    ) qhdi_ext ON usr_1.qhdi = qhdi_ext.qhdi
) a
LEFT JOIN (
    SELECT
        CASE '周'
            WHEN '周' THEN created_week
            WHEN '日' THEN created_day
            WHEN '月' THEN CONCAT(created_month, '01')
        END AS created_time,
        user_id AS userid,
        ds
    FROM hive_prod.exabrain.dw_flw_wt_coohomtool_i_d
    WHERE ds BETWEEN DATE_FORMAT(DATE_SUB(DATE_TRUNC('week', CURRENT_DATE()), INTERVAL '8' WEEK), '%Y%m%d')
        AND DATE_FORMAT(DATE_ADD(DATE_TRUNC('week', CURRENT_DATE()) - INTERVAL '1' DAY, INTERVAL '6' DAY), '%Y%m%d')
) b ON a.userid = b.userid
    AND b.ds BETWEEN a.created_day AND DATE_FORMAT(DATE_ADD(a.created_day, INTERVAL 6 DAY), '%Y%m%d')
LEFT JOIN (
    SELECT
        user_id AS userid,
        ds,
        design_created,
        CASE WHEN copylog_parent_id > 0 THEN '是' ELSE '否' END AS is_copy_design
    FROM hive_prod.exabrain.dm_cntnt_i18n_project_design_s_d
    WHERE ds = DATE_FORMAT(CURRENT_DATE() - INTERVAL '1' DAY, '%Y%m%d')
        AND is_coohom_original = TRUE
        AND area >= 30
) d ON b.userid = d.userid
    AND d.design_created BETWEEN a.created_day AND DATE_FORMAT(DATE_ADD(a.created_day, INTERVAL 6 DAY), '%Y%m%d')
LEFT JOIN e ON d.userid = e.userid
    AND e.ds BETWEEN a.created_day AND DATE_FORMAT(DATE_ADD(a.created_day, INTERVAL 6 DAY), '%Y%m%d')
LEFT JOIN (
    SELECT
        user_id AS userid,
        MIN(ds) AS ds
    FROM hive_prod.exabrain.dw_flw_wt_coohomrendering_i_d
    WHERE ds BETWEEN DATE_FORMAT(DATE_SUB(DATE_TRUNC('week', CURRENT_DATE()), INTERVAL '8' WEEK), '%Y%m%d')
        AND DATE_FORMAT(DATE_ADD(DATE_TRUNC('week', CURRENT_DATE()) - INTERVAL '1' DAY, INTERVAL '6' DAY), '%Y%m%d')
    GROUP BY user_id
) c ON e.userid = c.userid
    AND c.ds BETWEEN a.created_day AND DATE_FORMAT(DATE_ADD(a.created_day, INTERVAL 6 DAY), '%Y%m%d')
GROUP BY a.created_time
ORDER BY a.created_time

```

---
*生成时间: 2026-02-25 23:46:33
