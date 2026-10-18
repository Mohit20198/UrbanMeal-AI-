select 
    order_date, 
    city, 
    count(*) as orders, 
    count(case when is_delivered then 1 end) as delivered_orders,
    round(coalesce(count(case when order_status = 'Cancelled' then 1 end)::float / nullif(count(*), 0), 0), 4) as cancel_rate,
    sum(case when is_delivered then sales_amount else 0 end) as gmv,
    round(coalesce(sum(case when is_delivered then sales_amount else 0 end)::float / nullif(count(case when is_delivered then 1 end), 0), 0), 2) as aov
from {{ ref('fct_orders') }} 
group by 1, 2