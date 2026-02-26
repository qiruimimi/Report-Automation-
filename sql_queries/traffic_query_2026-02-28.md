# TRAFFIC SQL Query - 2026-02-28

## 数据参数

- **target_date**: `2026-02-28`

## SQL文件
01_traffic_weekly.sql

## 完整SQL语句
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
*生成时间: 2026-02-26 12:03:14
