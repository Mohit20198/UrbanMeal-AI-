with digit_0_9 as (
    select 0 as d union all select 1 union all select 2 union all select 3 union all select 4
    union all select 5 union all select 6 union all select 7 union all select 8 union all select 9
),
seq as (
    select (d3.d * 1000 + d2.d * 100 + d1.d * 10 + d0.d) as n
    from digit_0_9 d0
    cross join digit_0_9 d1
    cross join digit_0_9 d2
    cross join digit_0_9 d3
    where (d3.d * 1000 + d2.d * 100 + d1.d * 10 + d0.d) <= 1200
),
spine as (
    select dateadd(day, n, '2024-01-01'::date)::date as date_day
    from seq
)
select 
    date_day, 
    extract(year from date_day)::integer as year, 
    extract(month from date_day)::integer as month, 
    to_char(date_day, 'Mon') as month_name,
    to_char(date_day, 'Dy') as day_name, 
    case when extract(dow from date_day) in (0, 6) then true else false end as is_weekend
from spine 
where date_day <= '2026-12-31'::date