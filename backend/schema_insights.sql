-- ============================================================
-- Data Insights & Trajectory Views
-- ============================================================

-- 1. Swimmer Lifespan & Dropout Status
DROP MATERIALIZED VIEW IF EXISTS mv_swimmer_lifespan CASCADE;
CREATE MATERIALIZED VIEW mv_swimmer_lifespan AS
WITH swimmer_stats AS (
    SELECT 
        ir.swimmer_id,
        MIN(m.start_date) as first_swim_date,
        MAX(m.start_date) as last_swim_date,
        MIN(ir.age) as starting_age,
        MAX(ir.age) as ending_age
    FROM individual_results ir
    JOIN meets m ON ir.meet_id = m.id
    WHERE ir.age IS NOT NULL AND ir.age > 0
    GROUP BY ir.swimmer_id
),
db_meta AS (
    SELECT MAX(start_date) as max_db_date FROM meets
)
SELECT 
    s.swimmer_id,
    s.starting_age,
    s.ending_age,
    s.first_swim_date,
    s.last_swim_date,
    EXTRACT(YEAR FROM age(s.last_swim_date, s.first_swim_date)) + 
    EXTRACT(MONTH FROM age(s.last_swim_date, s.first_swim_date))/12.0 as years_active,
    CASE 
        WHEN s.last_swim_date >= (db.max_db_date - INTERVAL '18 months') THEN 'Active'
        WHEN s.ending_age >= 18 THEN 'Graduated'
        ELSE 'Quit'
    END as current_status
FROM swimmer_stats s
CROSS JOIN db_meta db
WHERE s.starting_age <= 18;

CREATE UNIQUE INDEX IF NOT EXISTS idx_lifespan_swimmer ON mv_swimmer_lifespan(swimmer_id);


-- 2. Event Percentiles by Age (State averages & elite times)
DROP MATERIALIZED VIEW IF EXISTS mv_event_percentiles_by_age CASCADE;
CREATE MATERIALIZED VIEW mv_event_percentiles_by_age AS
SELECT 
    ir.event_id,
    m.course,
    ir.age,
    COUNT(ir.id) as sample_size,
    percentile_cont(0.75) WITHIN GROUP (ORDER BY ir.finals_time) as p75_time, -- "B" Standard
    percentile_cont(0.50) WITHIN GROUP (ORDER BY ir.finals_time) as p50_time, -- "BB" Standard (Average)
    percentile_cont(0.25) WITHIN GROUP (ORDER BY ir.finals_time) as p25_time, -- "A" Standard
    percentile_cont(0.10) WITHIN GROUP (ORDER BY ir.finals_time) as p10_time, -- "AA" Standard
    percentile_cont(0.05) WITHIN GROUP (ORDER BY ir.finals_time) as p05_time, -- "AAA" Standard
    percentile_cont(0.01) WITHIN GROUP (ORDER BY ir.finals_time) as p01_time  -- "AAAA" Standard
FROM individual_results ir
JOIN meets m ON ir.meet_id = m.id
WHERE ir.finals_time IS NOT NULL 
  AND NOT ir.dq 
  AND ir.age BETWEEN 6 AND 18
GROUP BY ir.event_id, m.course, ir.age
HAVING COUNT(ir.id) >= 20;

CREATE UNIQUE INDEX IF NOT EXISTS idx_percentiles_event_course_age ON mv_event_percentiles_by_age(event_id, course, age);

