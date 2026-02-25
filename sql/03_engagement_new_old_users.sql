SELECT
    lastweek.created_week AS 周,
    COUNT(DISTINCT CASE WHEN lastweek.active_user_type = '新注册' THEN lastweek.user_id END) AS 新用户WAU,
    COUNT(DISTINCT CASE WHEN lastweek.active_user_type = '老用户' THEN lastweek.user_id END) AS 老用户WAU
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
GROUP BY lastweek.created_week
ORDER BY 周
LIMIT 10000
