-- 收入 - SKU维度分析
-- 用于获取不同SKU（pro_year_cyclical等）的收入数据

SELECT
    case '周'
      when '日' then pay_success_day
      when '周' then pay_success_week
      when '月' then pay_success_month
    end AS `日期`
    , coalesce(sku_mode, 'Unknown') AS `SKU模式`
    , coalesce(sku_type, 'Unknown') AS `SKU类型`
    , coalesce(sku_interval, 'Unknown') AS `SKU周期`
    , round(sum(coalesce(amt_usd, 0)), 1) AS `收入_美元`
    , count(DISTINCT user_id) AS `付费用户数`
    , round(
        if(
            count(DISTINCT user_id) = 0,
            NULL,
            sum(coalesce(amt_usd, 0)) * 1.00 / count(DISTINCT user_id)
        ),
        1
    ) AS `客单价_美元`
    , round(sum(if(order_type_user = 'NewSubscribe', coalesce(amt_usd, 0), 0)), 1) AS `新签收入_美元`
    , count(DISTINCT if(order_type_user = 'NewSubscribe', user_id, NULL)) AS `新签用户数`
    , round(sum(if(order_type_user = 'Renewal', coalesce(amt_usd, 0), 0)), 1) AS `续约收入_美元`
    , count(DISTINCT if(order_type_user = 'Renewal', user_id, NULL)) AS `续约用户数`
FROM hive_prod.kdw_dw.dws_coohom_trd_daily_toc_invoice_s_d
WHERE ds = '{{ds}}'
    AND pay_success_day BETWEEN '{{date_start}}' AND '{{date_end}}'
    AND coalesce(amt_usd, 0) > 0
    AND kjl_user_id in (
      -- 用户筛选CTE（与主查询保持一致）
      select usr_1.kujiale_user_id
      from (
        SELECT kujiale_user_id
        FROM hive_prod.exabrain.dwb_usr_coohom_user_s_d
        WHERE ds = '{{ds}}'
          AND deleted = false
      ) usr_1
    )
GROUP BY
    case '周'
      when '日' then pay_success_day
      when '周' then pay_success_week
      when '月' then pay_success_month
    end
    , sku_mode
    , sku_type
    , sku_interval
ORDER BY `日期` DESC, `收入_美元` DESC
LIMIT 100000
