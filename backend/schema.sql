-- Enable the pgvector extension to work with embedding vectors
create extension if not exists vector;

-- Create the complaints table
create table if not exists complaints (
    id bigint primary key generated always as identity,
    description text not null,
    issue_type text,
    severity text,
    ward text,
    latitude double precision,
    longitude double precision,
    image_url text,
    embedding vector(3072), -- Gemini text-embedding-004 has 768 dimensions
    upvote_count integer default 1,
    status text default 'pending',
    name text,
    phone_number text,
    created_at timestamp with time zone default timezone('utc'::text, now())
);

-- Create a function to match complaints based on embedding and distance
create or replace function match_complaints (
    query_embedding vector(768),
    match_threshold float,
    match_count int,
    loc_lat double precision,
    loc_long double precision,
    radius_meters float
)
returns table (
    id bigint,
    description text,
    issue_type text,
    severity text,
    ward text,
    latitude double precision,
    longitude double precision,
    image_url text,
    upvote_count integer,
    status text,
    created_at timestamp with time zone,
    similarity float,
    distance_meters float
)
language plpgsql
as $$
begin
    return query
    select
        c.id,
        c.description,
        c.issue_type,
        c.severity,
        c.ward,
        c.latitude,
        c.longitude,
        c.image_url,
        c.upvote_count,
        c.status,
        c.created_at,
        1 - (c.embedding <=> query_embedding) as similarity,
        -- Calculate distance in meters using the Haversine formula (roughly)
        -- Earth radius is approx 6371000 meters
        case 
            when c.latitude is not null and c.longitude is not null and loc_lat is not null and loc_long is not null then
                6371000 * acos(
                    cos(radians(loc_lat)) * cos(radians(c.latitude)) *
                    cos(radians(c.longitude) - radians(loc_long)) +
                    sin(radians(loc_lat)) * sin(radians(c.latitude))
                )
            else 
                null
        end as distance_meters
    from complaints c
    where 1 - (c.embedding <=> query_embedding) > match_threshold
    -- Filter by radius if location and radius are provided
    and (
        loc_lat is null or loc_long is null or radius_meters is null
        or 
        (
            6371000 * acos(
                cos(radians(loc_lat)) * cos(radians(c.latitude)) *
                cos(radians(c.longitude) - radians(loc_long)) +
                sin(radians(loc_lat)) * sin(radians(c.latitude))
            ) <= radius_meters
        )
    )
    order by c.embedding <=> query_embedding
    limit match_count;
end;
$$;
