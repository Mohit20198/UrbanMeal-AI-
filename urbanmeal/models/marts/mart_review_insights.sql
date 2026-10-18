{{ config(tags=['ai']) }}

select 
    rr.city,
    e.topic,
    e.sentiment_label,
    count(*) as reviews,
    round(avg(e.sentiment_score), 3) as avg_sentiment_score,
    round(avg(rr.rating), 2) as avg_star_rating,
    count(case when e.key_issue is not null then 1 end) as flagged_issues
from {{ source('ai', 'review_enriched') }} e
inner join {{ ref('stg_reviews') }} rr on e.review_id = cast(rr.review_id as varchar)
group by 1, 2, 3