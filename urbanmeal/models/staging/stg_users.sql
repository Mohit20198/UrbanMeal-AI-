select 
    try_cast(user_id as bigint) as customer_id, 
    name as customer_name, 
    lower(email) as email,
    try_cast(age as integer) as age, 
    gender, 
    marital_status, 
    occupation,
    monthly_income as income_band, 
    education, 
    try_cast(family_size as integer) as family_size
from {{ source('raw', 'users') }} 
where try_cast(user_id as bigint) is not null