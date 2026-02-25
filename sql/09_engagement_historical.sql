-- 活跃 - 25周历史WAU
-- 用于获取25周历史平均WAU数据

SELECT
    created_week AS `周`
    , count(DISTINCT user_id) AS `WAU`
    , count(DISTINCT if(user_created_week = created_week, user_id, NULL)) AS `新用户WAU`
    , count(DISTINCT if(user_created_week < created_week, user_id, NULL)) AS `老用户WAU`
FROM (
    SELECT
        user_id
        , created_week
        , user_created_week
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
    GROUP BY user_id, created_week, user_created_week
) user_activity
GROUP BY created_week
ORDER BY `周` DESC
LIMIT 25
