select
    r.review_id,
    r.order_id,
    try_cast(r.user_id as bigint) as customer_id,
    try_cast(r.restaurant_id as bigint) as restaurant_id,
    try_cast(r.rating as integer) as rating,
    r.comment::varchar(65535) as comment,
    r.review_date::date as review_date,
    res.city as city
from {{ source('raw', 'reviews') }} r
left join {{ ref('stg_restaurants') }} res on try_cast(r.restaurant_id as bigint) = res.restaurant_id
where r.comment is not null