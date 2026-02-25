-- 收入 - 账单分层分析
-- 用于获取不同分层（连续续约、升级、召回、新签等）的收入数据

-- 注意：此查询需要根据实际账单分层字段进行调整
-- 假设存在 subscription_tier 或类似字段

SELECT
    case '周'
      when '日' then pay_success_day
      when '周' then pay_success_week
      when '月' then pay_success_month
    end AS `日期`
    -- 账单分层逻辑
    , case
        when order_type_user = 'NewSubscribe' then '新签'
        when order_type_user = 'Renewal' then
            case
                when is_upgrade = true then '升级'
                when is_downgrade = true then '降级'
                when consecutive_renewal_count >= 2 then '连续续约'
                else '召回'
            end
        else '其他'
    end AS `账单分层`
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
    , count(DISTINCT user_id) AS `用户数`
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
    , case
        when order_type_user = 'NewSubscribe' then '新签'
        when order_type_user = 'Renewal' then
            case
                when is_upgrade = true then '升级'
                when is_downgrade = true then '降级'
                when consecutive_renewal_count >= 2 then '连续续约'
                else '召回'
            end
        else '其他'
    end
ORDER BY `日期` DESC, `收入_美元` DESC
LIMIT 100000

-- 说明：
-- 1. is_upgrade, is_downgrade, consecutive_renewal_count 等字段可能需要根据实际表结构调整
-- 2. 如果没有这些字段，可能需要通过用户行为计算得出
-- 3. 账单分层定义：
--    - 新签: 首次购买
--    - 连续续约: 连续多周续约
--    - 升级: 从低级别升级到高级别
--    - 降级: 从高级别降级到低级别
--    - 召回: 之前流失后重新购买
