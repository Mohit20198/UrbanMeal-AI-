select 
    city, 
    extract(hour from order_timestamp) as order_hour, 
    count(case when is_delivered then 1 end) as delivered_orders,
    round(median(delivery_time_min), 1) as p50, 
    round(percentile_cont(0.9) within group (order by delivery_time_min), 1) as p90
from {{ ref('fct_orders') }} 
where is_delivered 
group by 1, 2