# 生成的查询：

## Coohom周报 SQL 查询 - 2026-02-23

**目标日期**: 2026-02-23 (20260223)

**周范围**: 20260223 ~ 20260228

**报告日期**: 2026-02-28

---

## 日期参数

| 参数               | 值             | 应该的值 |
| ------------------ | -------------- | -------- |
| week_monday        | `20260223`   |          |
| week_saturday      | `20260228`   |          |
| week_sunday        | `20260301`   |          |
| last_week_monday   | `20260216`   |          |
| last_week_saturday | `20260221`   |          |
| last_week_sunday   | `20260222`   |          |
| partition_start    | `20260216`   |          |
| partition_end      | `20260301`   |          |
| snapshot_date      | `20260301`   |          |
| history_start_date | `20251231`   |          |
| pay_start_date     | `20251231`   |          |
| pay_end_date       | `20260228`   |          |
| report_date        | `2026-02-28` |          |
| week_offset        | `0`          |          |

---

## TRAFFIC - 01_traffic_weekly.sql

```sql
SELECT
    CASE '周'
        WHEN '日' THEN created_day
        WHEN '周' THEN DATE_FORMAT(DATE_ADD(STR_TO_DATE(created_day, '%Y%m%d'), INTERVAL -DAYOFWEEK(STR_TO_DATE(created_day, '%Y%m%d')) DAY), '%Y%m%d')
        WHEN '月' THEN substr(created_day, 1, 6)
        ELSE NULL
    END AS 日期,
    ads_channel_classify AS 渠道,
    COUNT(DISTINCT CASE
        WHEN (
            (fst_registered_time IS NULL)
            OR (date_format(fst_registered_time, '%Y%m%d') = created_day)
        )
        AND (coalesce(date_format(fst_visit_coohom_time, '%Y%m%d'), created_day) = created_day)
        THEN qhdi
    END) AS 新访客数,
    COUNT(DISTINCT CASE
        WHEN (
            (fst_registered_time IS NULL)
            OR (date_format(fst_registered_time, '%Y%m%d') = created_day)
        )
        AND (coalesce(date_format(fst_visit_coohom_time, '%Y%m%d'), created_day) = created_day)
        THEN register_user_id
    END) AS 新访客注册数,
    IF(
        COUNT(DISTINCT CASE
            WHEN (
                (fst_registered_time IS NULL)
                OR (date_format(fst_registered_time, '%Y%m%d') = created_day)
            )
            AND (coalesce(date_format(fst_visit_coohom_time, '%Y%m%d'), created_day) = created_day)
            THEN qhdi
        END) = 0,
        NULL,
        ROUND(
            COUNT(DISTINCT CASE
                WHEN (
                    (fst_registered_time IS NULL)
                    OR (date_format(fst_registered_time, '%Y%m%d') = created_day)
                )
                AND (coalesce(date_format(fst_visit_coohom_time, '%Y%m%d'), created_day) = created_day)
                THEN register_user_id
                END)
            / IFNULL(COUNT(DISTINCT CASE
                WHEN (
                    (fst_registered_time IS NULL)
                    OR (date_format(fst_registered_time, '%Y%m%d') = created_day)
                )
                AND (coalesce(date_format(fst_visit_coohom_time, '%Y%m%d'), created_day) = created_day)
                THEN qhdi
                END) = 0, COUNT(DISTINCT CASE
                WHEN (
                    (fst_registered_time IS NULL)
                    OR (date_format(fst_registered_time, '%Y%m%d') = created_day)
                )
                AND (coalesce(date_format(fst_visit_coohom_time, '%Y%m%d'), created_day) = created_day)
                THEN qhdi
                END)
            ),
            6
        )
    ) AS 新访客注册转化率
FROM hive_prod.exabrain.dwb_coohom_user_visit_register_i_d
WHERE ds BETWEEN '20260216' AND '20260301'
    AND ads_channel_classify IN ('paid ads','organic search','referral','ai search','social media','email','affiliate & kol','operations','desktop app','mobile app search','other')
GROUP BY
    CASE '周'
        WHEN '日' THEN created_day
        WHEN '周' THEN DATE_FORMAT(DATE_ADD(STR_TO_DATE(created_day, '%Y%m%d'), INTERVAL -DAYOFWEEK(STR_TO_DATE(created_day, '%Y%m%d')) DAY), '%Y%m%d')
        WHEN '月' THEN substr(created_day, 1, 6)
        ELSE NULL
    END,
    ads_channel_classify
ORDER BY 日期 ASC
LIMIT 10000

```

---

## ACTIVATION - 02_activation_ready.sql

```sql
SELECT
    a.created_time AS 日期,
    COUNT(DISTINCT a.userid) AS 新注册用户数,
    ROUND(COUNT(DISTINCT b.userid) / COUNT(DISTINCT a.userid), 6) AS 注册到进工具转化率,
    COUNT(DISTINCT b.userid) AS 进工具用户数,
    ROUND(COUNT(DISTINCT d.userid) / COUNT(DISTINCT b.userid), 6) AS 进工具到有效画户型转化率,
    COUNT(DISTINCT d.userid) AS 有效画户型用户数,
    ROUND(COUNT(DISTINCT e.userid) / COUNT(DISTINCT d.userid), 6) AS 有效画户型到有效拖模型转化率,
    COUNT(DISTINCT e.userid) AS 有效拖模型用户数,
    ROUND(COUNT(DISTINCT c.userid) / COUNT(DISTINCT e.userid), 6) AS 有效拖模型到渲染转化率,
    COUNT(DISTINCT c.userid) AS 渲染用户数,
    ROUND(COUNT(DISTINCT b.userid) / COUNT(DISTINCT a.userid), 6) AS 进工具总转化率,
    ROUND(COUNT(DISTINCT d.userid) / COUNT(DISTINCT a.userid), 6) AS 有效画户型总转化率,
    ROUND(COUNT(DISTINCT e.userid) / COUNT(DISTINCT a.userid), 6) AS 有效拖模型总转化率,
    ROUND(COUNT(DISTINCT c.userid) / COUNT(DISTINCT a.userid), 6) AS 渲染总转化率
FROM
    (
      select
          usr_1.created_time, usr_1.created_day, usr_1.created_week, usr_1.userid, usr_1.qhdi, usr_2.locale_site, usr_2.locale, qhdi.ads_channel_classify
      from (
    		SELECT CASE '周'
    				WHEN '周' THEN created_week
    				WHEN '日' THEN created_day
    				WHEN '月' THEN CONCAT(SUBSTR(created_day, 1, 6), '01')
    			END AS created_time,
    			created_day,
    			created_week,
    			kujiale_user_id AS userid,
    			qhdi
    		FROM hive_prod.exabrain.dwb_usr_coohom_user_s_d
    		WHERE ds = '20260301'
                AND created_day BETWEEN '20260216' AND '20260301'
                AND IF(ARRAY_LENGTH(['个人用户']) > 0, ARRAY_CONTAINS(['个人用户'], coohom_user_type), TRUE)
                AND IF(ARRAY_LENGTH([]) > 0, ARRAY_CONTAINS([], coohom_user_level), TRUE)
                AND IF(LENGTH('') > 0, coohom_register_tool_version = '', TRUE)
                AND IF(ARRAY_LENGTH(['PC Apps','WEB']) > 0, ARRAY_CONTAINS(['PC Apps','WEB'], cohom_register_platform), TRUE)
                AND IF(ARRAY_LENGTH([]) > 0, ARRAY_CONTAINS([], cohom_register_country_en), TRUE)
                AND IF(ARRAY_LENGTH([]) > 0, ARRAY_CONTAINS([], cohom_register_country_sc), TRUE)
                AND IF(ARRAY_LENGTH([]) > 0, ARRAY_CONTAINS([], cohom_register_utmsource), TRUE)
                AND deleted = FALSE
                AND international_user_id <> 3099059
    	) usr_1
        INNER JOIN (
            SELECT kujiale_user_id AS userid, locale_site, locale
            FROM hive_prod.kdw_dw.dwb_usr_coohom_user_s_d
            WHERE ds = '20260301'
        ) usr_2 ON usr_1.userid = usr_2.userid
        LEFT JOIN (
            SELECT qhdi, ads_channel_classify
            FROM hive_prod.exabrain.dwb_usr_coohom_qhdi_extended_s_d
            WHERE ds = '20260301'
        ) qhdi
        ON usr_1.qhdi = qhdi.qhdi
        WHERE
         IF(ARRAY_LENGTH([]) > 0, ARRAY_CONTAINS([], ads_channel_classify), TRUE)
        AND IF(ARRAY_LENGTH([]) > 0, ARRAY_CONTAINS([], locale_site), TRUE)
        AND IF(ARRAY_LENGTH([]) > 0, ARRAY_CONTAINS([], locale), TRUE)

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
        FROM
            hive_prod.exabrain.dw_flw_wt_coohomtool_i_d
        WHERE
            ds BETWEEN '20260216' AND DATE_FORMAT(DATE_ADD('20260301', INTERVAL 6 DAY), '%Y%m%d')
    ) b ON a.userid = b.userid
    AND b.ds BETWEEN a.created_day AND DATE_FORMAT(DATE_ADD(a.created_day, INTERVAL 6 DAY), '%Y%m%d')
    LEFT JOIN (
        SELECT
            user_id AS userid,
            ds,
            design_created,
            CASE WHEN copylog_parent_id > 0 THEN '是' ELSE '否' END AS is_copy_design
        FROM
            hive_prod.exabrain.dm_cntnt_i18n_project_design_s_d
        WHERE
            ds = '20260301'
            AND is_coohom_original = TRUE
            AND IF(LENGTH('') = 0, TRUE, IF('' = '是', copylog_parent_id > 0, COALESCE(copylog_parent_id, 0) <= 0))
            AND area >= 30
    ) d ON b.userid = d.userid
    AND d.design_created BETWEEN a.created_day AND DATE_FORMAT(DATE_ADD(a.created_day, INTERVAL 6 DAY), '%Y%m%d')
    LEFT JOIN (
        SELECT
            userid,
            ds,
            MIN(ds) AS ds
        FROM
            hive_prod.kdw_log.dwd_log_yuntuModelAfterDrag
        WHERE
            ds BETWEEN '20260216' AND DATE_FORMAT(DATE_ADD('20260301', INTERVAL 6 DAY), '%Y%m%d')
        GROUP BY
            userid, ds
        HAVING COUNT(1) > 6
    ) e ON b.userid = e.userid
      AND e.ds BETWEEN a.created_day AND DATE_FORMAT(DATE_ADD(a.created_day, INTERVAL 6 DAY), '%Y%m%d')
      AND e.userid = d.userid
    LEFT JOIN (
        SELECT
            user_id AS userid,
            MIN(ds) ds
        FROM
            hive_prod.exabrain.dw_flw_wt_coohomrendering_i_d
        WHERE
            ds BETWEEN '20260216' AND DATE_FORMAT(DATE_ADD('20260301', INTERVAL 6 DAY), '%Y%m%d')
        GROUP BY user_id
    ) c ON e.userid = c.userid
      AND c.ds BETWEEN a.created_day AND DATE_FORMAT(DATE_ADD(a.created_day, INTERVAL 6 DAY), '%Y%m%d')
GROUP BY
    a.created_time
ORDER BY
    a.created_time

```

---

## ENGAGEMENT - 03_engagement_new_old_users.sql

```sql
SELECT lastweek.created_week AS 周, lastweek.active_user_type AS `用户类型（新老）`, COUNT(DISTINCT lastweek.user_id) AS `上周工具WAU`
FROM (
	SELECT user_id, created_week, user_created_week, coohom_user_type
		, IF(user_created_week = created_week, '新注册', '老用户') AS active_user_type
	FROM hive_prod.exabrain.dw_flw_wt_coohomtool_i_d
	WHERE ds >= '20260216'
		AND ds <= '20260301'
		AND user_id IS NOT NULL
		AND IF(LENGTH('') > 0, CAST(account_id AS VARCHAR) = '', TRUE)
		AND IF(CARDINALITY(SPLIT(REPLACE("", "'", ""), ',')) > 0, ARRAY_CONTAINS(SPLIT(REPLACE("", "'", ""), ','), COALESCE(active_country_sc, coohom_register_country_sc)), TRUE) -- 筛选国家
		AND IF(CARDINALITY(SPLIT(REPLACE("", "'", ""), ',')) > 0, ARRAY_CONTAINS(SPLIT(REPLACE("", "'", ""), ','), tool_name), TRUE)
		AND IF(CARDINALITY(SPLIT(REPLACE("'个人用户'", "'", ""), ',')) > 0, ARRAY_CONTAINS(SPLIT(REPLACE("'个人用户'", "'", ""), ','), coohom_user_type), TRUE)
		AND IF(CARDINALITY(SPLIT(REPLACE("", "'", ""), ',')) > 0, ARRAY_CONTAINS(SPLIT(REPLACE("", "'", ""), ','), coohom_user_level), TRUE)
		AND IF(CARDINALITY(SPLIT(REPLACE("", "'", ""), ',')) > 0, ARRAY_CONTAINS(SPLIT(REPLACE("", "'", ""), ','), coohom_register_platform), TRUE)
	GROUP BY user_id, created_week, user_created_week, coohom_user_type, IF(user_created_week = created_week, '新注册', '老用户')
) lastweek
GROUP BY lastweek.created_week, lastweek.active_user_type
ORDER BY 周
LIMIT 10000

```

---

## RETENTION - 04_retention.sql

```sql
SELECT lastweek.created_week AS 上周, lastweek.active_user_type AS 上周用户类型, COUNT(DISTINCT lastweek.user_id) AS `上周工具WAU`
	, COUNT(DISTINCT thisweek.user_id) AS `本周工具WAU`
	, IF(COUNT(DISTINCT lastweek.user_id) = 0, 0.0, ROUND(COUNT(DISTINCT thisweek.user_id) / COUNT(DISTINCT lastweek.user_id), 4)) AS 工具次周留存
FROM (
	SELECT user_id, created_week, user_created_week, coohom_user_type
		, IF(user_created_week = created_week, '新注册', '老用户') AS active_user_type
	FROM hive_prod.exabrain.dw_flw_wt_coohomtool_i_d
	WHERE ds >= '20260216'
		AND ds < DATE_FORMAT(DATE_ADD(STR_TO_DATE('20260301', '%Y%m%d'), INTERVAL -(DAYOFWEEK(STR_TO_DATE('20260301', '%Y%m%d')) - 1) DAY), '%Y%m%d')
		AND user_id IS NOT NULL
		AND IF(LENGTH('') > 0, CAST(account_id AS VARCHAR) = '', TRUE)
		AND IF(CARDINALITY(SPLIT(REPLACE("", "'", ""), ',')) > 0, ARRAY_CONTAINS(SPLIT(REPLACE("", "'", ""), ','), COALESCE(active_country_sc, coohom_register_country_sc)), TRUE) -- 筛选国家
		AND IF(CARDINALITY(SPLIT(REPLACE("", "'", ""), ',')) > 0, ARRAY_CONTAINS(SPLIT(REPLACE("", "'", ""), ','), tool_name), TRUE)
		AND IF(CARDINALITY(SPLIT(REPLACE("'个人用户'", "'", ""), ',')) > 0, ARRAY_CONTAINS(SPLIT(REPLACE("'个人用户'", "'", ""), ','), coohom_user_type), TRUE)
		AND IF(CARDINALITY(SPLIT(REPLACE("", "'", ""), ',')) > 0, ARRAY_CONTAINS(SPLIT(REPLACE("", "'", ""), ','), coohom_user_level), TRUE)
		AND IF(CARDINALITY(SPLIT(REPLACE("", "'", ""), ',')) > 0, ARRAY_CONTAINS(SPLIT(REPLACE("", "'", ""), ','), coohom_register_platform), TRUE)
	GROUP BY user_id, created_week, user_created_week, coohom_user_type, IF(user_created_week = created_week, '新注册', '老用户')
) lastweek
	LEFT JOIN (
		SELECT user_id, created_week, user_created_week, last_created_week, coohom_user_type
			, IF(user_created_week = last_created_week, '新注册', '老用户') AS active_user_type
		FROM hive_prod.exabrain.dw_flw_wt_coohomtool_i_d
		WHERE ds >= '20260216'
			AND ds <= '20260301'
			AND user_id IS NOT NULL
			AND IF(LENGTH('') > 0, CAST(account_id AS VARCHAR) = '', TRUE)
			AND IF(CARDINALITY(SPLIT(REPLACE("", "'", ""), ',')) > 0, ARRAY_CONTAINS(SPLIT(REPLACE("", "'", ""), ','), tool_name), TRUE)
			AND IF(CARDINALITY(SPLIT(REPLACE("'个人用户'", "'", ""), ',')) > 0, ARRAY_CONTAINS(SPLIT(REPLACE("'个人用户'", "'", ""), ','), coohom_user_type), TRUE)
			AND IF(CARDINALITY(SPLIT(REPLACE("", "'", ""), ',')) > 0, ARRAY_CONTAINS(SPLIT(REPLACE("", "'", ""), ','), coohom_user_level), TRUE)
			AND IF(CARDINALITY(SPLIT(REPLACE("", "'", ""), ',')) > 0, ARRAY_CONTAINS(SPLIT(REPLACE("", "'", ""), ','), coohom_register_platform), TRUE)
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

## REVENUE - 05_revenue.sql

```sql
WITH usr AS (
  select
      usr_1.userid
  from (
		SELECT CASE '周'
				WHEN '周' THEN created_week
				WHEN '日' THEN created_day
				WHEN '月' THEN CONCAT(SUBSTR(created_day, 1, 6), '01')
			END AS created_time, created_day, created_week, kujiale_user_id AS userid, ds, qhdi
		FROM hive_prod.exabrain.dwb_usr_coohom_user_s_d
		WHERE ds = '20260301'
			AND IF(CARDINALITY(SPLIT(REPLACE("", "'", ""), ',')) > 0, ARRAY_CONTAINS(SPLIT(REPLACE("", "'", ""), ','), coohom_register_platform), TRUE)
			AND IF(CARDINALITY(SPLIT(REPLACE("", "'", ""), ',')) > 0, ARRAY_CONTAINS(SPLIT(REPLACE("", "'", ""), ','), cohom_register_utmsource), TRUE)
			-- AND deleted = false
			-- AND international_user_id <> 3099059
	) usr_1
    INNER JOIN (
        SELECT kujiale_user_id AS userid, locale_site, locale
        FROM hive_prod.kdw_dw.dwb_usr_coohom_user_s_d
        WHERE ds = '20260301'
    ) usr_2 ON usr_1.userid = usr_2.userid
    LEFT JOIN (
        SELECT qhdi, ads_channel_classify
        FROM hive_prod.exabrain.dwb_usr_coohom_qhdi_extended_s_d
        WHERE ds = '20260301'
    ) qhdi
    ON usr_1.qhdi = qhdi.qhdi
    WHERE IF(CARDINALITY(SPLIT(REPLACE("", "'", ""), ',')) > 0, ARRAY_CONTAINS(SPLIT(REPLACE("", "'", ""), ','), locale_site), TRUE)
      AND IF(CARDINALITY(SPLIT(REPLACE("", "'", ""), ',')) > 0, ARRAY_CONTAINS(SPLIT(REPLACE("", "'", ""), ','), locale), TRUE)
      AND IF(CARDINALITY(SPLIT(REPLACE("", "'", ""), ',')) > 0, ARRAY_CONTAINS(SPLIT(REPLACE("", "'", ""), ','), ads_channel_classify), TRUE)
    )

SELECT
    CASE '周'
      WHEN '日' THEN pay_success_day
      WHEN '周' THEN pay_success_week
      WHEN '月' THEN pay_success_month
      WHEN '季度' THEN CONCAT(SUBSTRING(pay_success_day, 1, 4), LPAD(CEIL(MONTH(pay_success_day) / 3), 2, '0'), '01')
      WHEN '半年' THEN IF(MONTH(pay_success_day) <= 6, CONCAT(SUBSTRING(pay_success_day, 1, 4), '0101'), CONCAT(SUBSTRING(pay_success_day, 1, 4), '0701'))
    END AS 日期 -- **总/新/续 订阅OR购买收入
	, ROUND(SUM(COALESCE(amt_usd, 0)), 1) AS Total_Amt
	, ROUND(SUM(IF(order_type_user = 'NewSubscribe', COALESCE(amt_usd, 0), 0)), 1) AS NewSubscribe_Amt
	, ROUND(SUM(IF(order_type_user = 'Renewal', COALESCE(amt_usd, 0), 0)), 1) AS Renewal_Amt

  -- **总/新/续 订阅OR购买用户数, 不购买单品渲染券
	, COUNT(DISTINCT IF(sub_mode_type IN ('normal_subscription_mode', 'single_subscription_mode'), user_id, NULL)) AS Total_Paid_Users
	, COUNT(DISTINCT IF(order_type_user = 'NewSubscribe' AND sub_mode_type IN ('normal_subscription_mode', 'single_subscription_mode'), user_id, NULL)) AS NewSubscribe_Users
	, COUNT(DISTINCT IF(order_type_user = 'Renewal'      AND sub_mode_type IN ('normal_subscription_mode', 'single_subscription_mode'), user_id, NULL)) AS Renewal_Users

  -- **总/新/续 订阅OR购买 客单价, 不购买单品渲染券
	, ROUND(IF(COUNT(DISTINCT IF(sub_mode_type IN ('normal_subscription_mode', 'single_subscription_mode'), user_id, NULL)) = 0, NULL, SUM(IF(sub_mode_type IN ('normal_subscription_mode', 'single_subscription_mode'), COALESCE(amt_usd, 0), 0)) * 1.00 / COUNT(DISTINCT IF(sub_mode_type IN ('normal_subscription_mode', 'single_subscription_mode'), user_id, NULL))), 1) AS 整体客单价
	, ROUND(IF(COUNT(DISTINCT IF(order_type_user = 'NewSubscribe'
		AND sub_mode_type IN ('normal_subscription_mode', 'single_subscription_mode'), user_id, NULL)) = 0, NULL, SUM(IF(order_type_user = 'NewSubscribe'
		AND sub_mode_type IN ('normal_subscription_mode', 'single_subscription_mode'), COALESCE(amt_usd, 0), 0)) * 1.00 / COUNT(DISTINCT IF(order_type_user = 'NewSubscribe'
		AND sub_mode_type IN ('normal_subscription_mode', 'single_subscription_mode'), user_id, NULL))), 1) AS 新签首购客单价
	, COALESCE(ROUND(IF(COUNT(DISTINCT IF(order_type_user = 'Renewal'
		AND sub_mode_type IN ('normal_subscription_mode', 'single_subscription_mode'), user_id, NULL)) = 0, NULL, SUM(IF(order_type_user = 'Renewal'
		AND sub_mode_type IN ('normal_subscription_mode', 'single_subscription_mode'), COALESCE(amt_usd, 0), 0)) * 1.00 / COUNT(DISTINCT IF(order_type_user = 'Renewal'
		AND sub_mode_type IN ('normal_subscription_mode', 'single_subscription_mode'), user_id, NULL))), 1), 0) AS 续约复购客单价
  FROM hive_prod.kdw_dw.dws_coohom_trd_daily_toc_invoice_s_d
WHERE ds = '20260301'
	AND pay_success_day BETWEEN '20251231' AND '20260228'
	AND COALESCE(amt_usd, 0) > 0
    AND kjl_user_id IN (
      SELECT * FROM usr
    )
AND IF(ARRAY_LENGTH([]) > 0, ARRAY_CONTAINS([], coohom_user_level), TRUE)
AND IF(ARRAY_LENGTH([]) > 0, ARRAY_CONTAINS([], coohom_user_type), TRUE)
AND IF(ARRAY_LENGTH([]) > 0, ARRAY_CONTAINS([], COALESCE(country_en, active_country_en)), TRUE)
AND IF(ARRAY_LENGTH([]) > 0, ARRAY_CONTAINS([], COALESCE(country_chs, active_country_sc)), TRUE)
AND IF(ARRAY_LENGTH([]) > 0, ARRAY_CONTAINS([], sku_mode), TRUE)
AND IF(ARRAY_LENGTH([]) > 0, ARRAY_CONTAINS([], sku_type), TRUE)
AND IF(ARRAY_LENGTH([]) > 0, ARRAY_CONTAINS([], sku_interval), TRUE)
AND IF(LENGTH('') > 0, is_freetrial = '', TRUE)
AND IF(LENGTH('')> 0, TRUE, CASE ''
                                                                    WHEN '是' THEN COALESCE(country_chs, active_country_sc) IN (SELECT country_chs FROM hive_prod.kdw_dw.dim_coohom_bluesea_region_country_a_d)
                                                                    WHEN '否' THEN COALESCE(country_chs, active_country_sc) NOT IN (SELECT country_chs FROM hive_prod.kdw_dw.dim_coohom_bluesea_region_country_a_d)
                                                                    ELSE TRUE
                                                              END)
AND IF(LENGTH('')> 0, TRUE, CASE ''
                                                                    WHEN '是' THEN COALESCE(country_chs, active_country_sc) IN (SELECT country_chs FROM hive_prod.kdw_dw.dim_coohom_freemium_region_country_a_d)
                                                                    WHEN '否' THEN COALESCE(country_chs, active_country_sc) NOT IN (SELECT country_chs FROM hive_prod.kdw_dw.dim_coohom_freemium_region_country_a_d)
                                                                    ELSE TRUE
                                                              END)
AND IF(ARRAY_LENGTH([])> 0,
    ARRAY_CONTAINS([], (CASE sub_mode_type
		WHEN 'normal_subscription_mode' THEN '付费订阅'
		WHEN 'single_coupon_mode' THEN '单品买券'
		WHEN 'single_subscription_mode' THEN '单品买会员'
		ELSE '其他'
	END)), TRUE)
GROUP BY CASE '周'
      WHEN '日' THEN pay_success_day
      WHEN '周' THEN pay_success_week
      WHEN '月' THEN pay_success_month
      WHEN '季度' THEN CONCAT(SUBSTRING(pay_success_day, 1, 4), LPAD(CEIL(MONTH(pay_success_day) / 3), 2, '0'), '01')
      WHEN '半年' THEN IF(MONTH(pay_success_day) <= 6, CONCAT(SUBSTRING(pay_success_day, 1, 4), '0101'), CONCAT(SUBSTRING(pay_success_day, 1, 4), '0701'))
    END
ORDER BY 日期
LIMIT 100000

```

---









# 线上的sql（认证过的，完全正确）





## TRAFFIC - 01

```sql
SELECT
    `create_date` AS `日期`,
    `ads_channel_classify` AS `渠道`,
    `new_effective_guest_cnt` AS `新访客数`,
    `new_effective_register_cnt` AS `新访客注册数`,
    IF(
        `new_effective_guest_cnt` = 0,
        NULL,
        CAST(`new_effective_register_cnt` AS DOUBLE) / CAST(`new_effective_guest_cnt` AS DOUBLE)
    ) AS `新访客注册转化率`
FROM (
    SELECT
        CASE '周'
            WHEN '日' THEN `created_day`
            WHEN '周' THEN DATE_FORMAT(DATE_TRUNC('week', STR_TO_DATE(`created_day`, '%Y%m%d')), '%Y%m%d')
            WHEN '月' THEN SUBSTR(`created_day`, 1, 6)
            ELSE NULL
        END AS `create_date`,
        `ads_channel_classify`,
        COUNT(DISTINCT `qhdi`) AS `guest_cnt`,
        COUNT(DISTINCT CASE WHEN `visit_user_id` IS NOT NULL THEN `qhdi` END) AS `login_cnt`,
        COUNT(DISTINCT CASE WHEN `fst_registered_time` IS NULL OR DATE_FORMAT(`fst_registered_time`, '%Y%m%d') = `created_day` THEN `qhdi` END) AS `effective_guest_cnt`,
        COUNT(DISTINCT CASE WHEN (`fst_registered_time` IS NULL OR DATE_FORMAT(`fst_registered_time`, '%Y%m%d') = `created_day`) AND COALESCE(DATE_FORMAT(`fst_visit_coohom_time`, '%Y%m%d'), `created_day`) = `created_day` THEN `qhdi` END) AS `new_effective_guest_cnt`,
        COUNT(DISTINCT `register_user_id`) AS `register_cnt`,
        COUNT(DISTINCT CASE WHEN `visit_user_id` IS NOT NULL THEN `register_user_id` END) AS `login_register_cnt`,
        COUNT(DISTINCT CASE WHEN `fst_registered_time` IS NULL OR DATE_FORMAT(`fst_registered_time`, '%Y%m%d') = `created_day` THEN `register_user_id` END) AS `effective_register_cnt`,
        COUNT(DISTINCT CASE WHEN (`fst_registered_time` IS NULL OR DATE_FORMAT(`fst_registered_time`, '%Y%m%d') = `created_day`) AND COALESCE(DATE_FORMAT(`fst_visit_coohom_time`, '%Y%m%d'), `created_day`) = `created_day` THEN `register_user_id` END) AS `new_effective_register_cnt`
    FROM hive_prod.`exabrain`.`dwb_coohom_user_visit_register_i_d`
    WHERE `ds` BETWEEN DATE_FORMAT(DATE_SUB(DATE_TRUNC('week', CURRENT_DATE()) - INTERVAL '1' DAY, INTERVAL '12' WEEK), '%Y%m%d')
        AND DATE_FORMAT(DATE_TRUNC('week', CURRENT_DATE()) - INTERVAL '1' DAY, '%Y%m%d')
        AND ARRAY_CONTAINS(SPLIT(REPLACE("'paid ads','organic search','referral','ai search','social media','email','affiliate & kol','operations','desktop app','mobile app search','other'", "'", ""), ','), `ads_channel_classify`)
        AND NOT (`ads_channel_classify` = 'direct' AND `fst_visit_country_sc` = '美国')
        AND `fst_visit_ua` <> 'meta-externalads/1.1 (+https://developers.facebook.com/docs/sharing/webmasters/crawler)'
        AND `fst_visit_ua` <> 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.6478.114 Safari/537.36'
    GROUP BY
        CASE '周'
            WHEN '日' THEN `created_day`
            WHEN '周' THEN DATE_FORMAT(DATE_TRUNC('week', STR_TO_DATE(`created_day`, '%Y%m%d')), '%Y%m%d')
            WHEN '月' THEN SUBSTR(`created_day`, 1, 6)
            ELSE NULL
        END,
        `ads_channel_classify`
) `visit`
ORDER BY `日期` ASC, `new_effective_guest_cnt` DESC
LIMIT 10000


```

---

## ACTIVATION - 02

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

## ENGAGEMENT - 03

```sql
SELECT
    lastweek.created_week AS 周,
    COUNT(DISTINCT lastweek.user_id) AS 全用户WAU,
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
) thisweek ON lastweek.user_id = thisweek.user_id
    AND lastweek.created_week = thisweek.last_created_week
    AND lastweek.active_user_type = thisweek.active_user_type
GROUP BY lastweek.created_week, lastweek.coohom_user_type
ORDER BY 周
LIMIT 10000

```

---

## RETENTION - 04

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
) thisweek ON lastweek.user_id = thisweek.user_id
    AND lastweek.created_week = thisweek.last_created_week
    AND lastweek.active_user_type = thisweek.active_user_type
GROUP BY lastweek.created_week, lastweek.active_user_type
ORDER BY 上周
LIMIT 10000


```

---

## REVENUE - 05

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





从输出看到：
  - 所有日期都是'20251124'、'20251201'、'20251208'等，没有'20260224'的数据
  - 目标周范围：20260224 ~ 20260302

  SQL查询的数据确实没有目标周的数据！这说明SQL的WHERE条件使用了CURRENT_DATE()，它返回的是当前服务器时间的数据，而不是我们期望的目标周
  数据。

## 1.流量

**整体表现 - 目标周 (20260216)**

- 总新访客: **129,103人**
- 总注册数: **23,067人**
- 整体转化率: **17.9%**

**环比上周 - (20260209)变化**

- 新访客: **-3.3%** ↓
- 注册数: **-10.1%** ↓
- 注册转化率: **-7.07%** ↓

**注意项**

- **organic search:** 新访客从60,927回升至63,895（+4.8%），转化率9.1%
- **paid ads:** 新访客从40,339降至36,919（-8.5%），转化率42.8%

## 2.转化

| 步骤          | 上周 (20260209) | 目标周 (20260216) | 环比变化 |
| ------------- | --------------- | ----------------- | -------- |
| 新注册用户数  | 25,409          | 22,554            | ↓ -11.3% |
| 注册→进工具   | 76.78%          | 80.19%            | ↑ +3.41% |
| 进工具→画户型 | 63.15%          | 62.74%            | ↓ -0.41% |
| 画户型→拖模型 | 32.75%          | 34.06%            | ↑ +1.31% |
| 拖模型→渲染   | 31.38%          | 29.99%            | ↓ -1.39% |
| **总转化率**  | 4.98%           | 5.05%             | ↑ +0.07% |





## 3.周活

**当周WAU（目标周 (20260216)）：**

- 当周WAU达到 **46,877人**，环比上周-6.0%，呈下降趋势
- 新用户WAU: 19,528人（环比-6.5%）
- 老用户WAU: 27,349人（环比-5.7%）

**历史趋势**

- 近8周历史平均WAU: **50,761**人





## 4.留存

**留存率统计（20260209周，因为0216周结束0209周的次周留存才算完整）**

**老用户留存率：** 44.2%

- 老用户留存率44.2%，处于近6周正常水平

**新用户留存率：** 10.1%

- 新用户留存率10.1%，处于近6周正常水平

**历史趋势（近6周）**

- 老用户次周留存平均值: **45.4%**
- 新用户次周留存平均值: **10.3%**





## 5.收入

**当周目标周 (20260216) 收入 53,078 美元**，较上周**-6,677** 美元↓，增长率 -11.2%。

其中，续约收入-5,171 美元（增长率 -10.3%），新签收入-1,506 美元（增长率 -15.9%）。

- **账单分层（二级）**：
  - 连续续约（-2,818 美元）
  - 召回（-1,607 美元）
  - 新签（-1,506 美元）
- **有效国家**：
  - 新加坡（-1,575 美元）
  - 埃及（-1,458 美元）
  - 美国（-1,273 美元）
- **sku**：
  - pro_month_cyclical（-1,899 美元）
  - pro_year_cyclical（-963 美元）
  - pro_plus_year_cyclical（-916 美元）

