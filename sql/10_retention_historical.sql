-- 留存 - 近12周新用户/老用户留存
-- 用于获取近12周留存率平均值

WITH weekly_users AS (
    SELECT
        user_id
        , created_week
        , user_created_week
        , coalesce(active_country_sc, coohom_register_country_sc) AS country
        , if(user_created_week = created_week, '新注册', '老用户') AS active_user_type
    FROM hive_prod.exabrain.dw_flw_wt_coohomtool_i_d
    WHERE ds >= '{{historical_start}}'
        AND ds <= '{{ds}}'
        AND user_id IS NOT NULL
        AND if(length('{{account_id}}') > 0, CAST(account_id AS varchar) = '{{account_id}}', true)
        AND IF(CARDINALITY(split(replace('{{country_filter}}', "'", ""), ',')) > 0,
            array_contains(split(replace('{{country_filter}}', "'", ""), ','), coalesce(active_country_sc, coohom_register_country_sc)),
            TRUE)
        AND if(cardinality(split(replace('{{tool_filter}}', "'", ""), ',')) > 0,
            array_contains(split(replace('{{tool_filter}}', "'", ""), ','), tool_name), true)
        AND if(cardinality(split(replace('{{user_type_filter}}', "'", ""), ',')) > 0,
            array_contains(split(replace('{{user_type_filter}}', "'", ""), ','), coohom_user_type), true)
        AND if(cardinality(split(replace('{{user_level_filter}}', "'", ""), ',')) > 0,
            array_contains(split(replace('{{user_level_filter}}', "'", ""), ','), coohom_user_level), true)
        AND if(cardinality(split(replace('{{platform_filter}}', "'", ""), ',')) > 0,
            array_contains(split(replace('{{platform_filter}}', "'", ""), ','), coohom_register_platform), true)
    GROUP BY user_id, created_week, user_created_week, coalesce(active_country_sc, coohom_register_country_sc)
),

retention_calc AS (
    SELECT
        lastweek.created_week AS `周`
        , lastweek.active_user_type AS `用户类型`
        , count(DISTINCT lastweek.user_id) AS `上周用户数`
        , count(DISTINCT thisweek.user_id) AS `本周留存用户数`
        , if(
            count(DISTINCT lastweek.user_id) = 0,
            0.0,
            round(CAST(count(DISTINCT thisweek.user_id) AS double) / CAST(count(DISTINCT lastweek.user_id) AS double), 4)
        ) AS `次周留存率`
    FROM weekly_users lastweek
    LEFT JOIN weekly_users thisweek
        ON lastweek.user_id = thisweek.user_id
        AND lastweek.created_week = thisweek.last_created_week
        AND lastweek.active_user_type = thisweek.active_user_type
    WHERE lastweek.created_week >= '{{recent_12w_start}}'
    GROUP BY lastweek.created_week, lastweek.active_user_type
)

SELECT
    `周`
    , `用户类型`
    , `上周用户数`
    , `本周留存用户数`
    , `次周留存率`
FROM retention_calc
ORDER BY `周` DESC
LIMIT 1000

-- 同时计算平均值
SELECT
    `用户类型`
    , round(avg(`次周留存率`), 4) AS `近12周平均留存率`
FROM retention_calc
GROUP BY `用户类型`
