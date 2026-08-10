/*
 MedTourEasy — Patient Conversion & Provider Performance Intelligence
   File: 03_sql_provider_scorecard.sql
   Purpose: SQL analysis layer covering joins, aggregations, window/rank
            functions, cohort conversion, SLA breach analysis, and the
            final provider scorecard used for FR-06.
   Database: mte_patient_intelligence.db (SQLite)
   Author: Ayan Suvra Bosu
*/

/*
Q1 - Sanity Check
*/
SELECT 
    pj.patient_id,
    pj.provider_id,
    pj.treatment_completed,
    pm.region,
    pm.specialty_area
FROM patient_journey pj
JOIN provider_master pm ON pj.provider_id = pm.provider_id
LIMIT 10;

/*
Q2 - Provider conversion rates
*/
SELECT 
    provider_id,
    COUNT(*) AS total_patients,
    ROUND(AVG(consultation_booked) * 100, 2) AS consultation_rate_pct,
    ROUND(AVG(treatment_completed) * 100, 2) AS treatment_rate_pct
FROM patient_journey
GROUP BY provider_id
ORDER BY treatment_rate_pct DESC;

/*
Q3 - Country-level conversion
*/
SELECT 
    pj.country,
    cr.region,
    COUNT(*) AS total_patients,
    ROUND(AVG(pj.consultation_booked) * 100, 2) AS consultation_rate_pct,
    ROUND(AVG(pj.treatment_completed) * 100, 2) AS treatment_rate_pct
FROM patient_journey pj
JOIN country_reference cr ON pj.country = cr.country
GROUP BY pj.country, cr.region
ORDER BY treatment_rate_pct DESC;

/*
Q4 - Rank providers by treatment rate Within their region
*/
WITH provider_stats AS (
    SELECT 
        pj.provider_id,
        pm.region,
        COUNT(*) AS total_patients,
        AVG(pj.treatment_completed) AS treatment_rate
    FROM patient_journey pj
    JOIN provider_master pm ON pj.provider_id = pm.provider_id
    GROUP BY pj.provider_id, pm.region
)
SELECT 
    provider_id,
    region,
    total_patients,
    ROUND(treatment_rate * 100, 2) AS treatment_rate_pct,
    RANK() OVER (PARTITION BY region ORDER BY treatment_rate DESC) AS region_rank
FROM provider_stats
ORDER BY region, region_rank;

/*
Q5 - Monthly cohort conversion
*/
WITH monthly AS (
    SELECT 
        strftime('%Y-%m', inquiry_date) AS cohort_month,
        COUNT(*) AS inquiries,
        SUM(treatment_completed) AS completions
    FROM patient_journey
    GROUP BY cohort_month
)
SELECT 
    cohort_month,
    inquiries,
    completions,
    ROUND(completions * 100.0 / inquiries, 2) AS conversion_rate_pct,
    SUM(inquiries) OVER (ORDER BY cohort_month) AS cumulative_inquiries,
    SUM(completions) OVER (ORDER BY cohort_month) AS cumulative_completions
FROM monthly
ORDER BY cohort_month;

/*
Q6 - SLA breach flag
*/
SELECT 
    pj.patient_id,
    pj.provider_id,
    pj.response_time_hours,
    cr.baseline_response_expectation_hours,
    CASE 
        WHEN pj.response_time_hours > cr.baseline_response_expectation_hours THEN 1
        ELSE 0
    END AS sla_breach,
    pj.consultation_booked,
    pj.treatment_completed
FROM patient_journey pj
JOIN country_reference cr ON pj.country = cr.country;

/*
Q7 - SLA breach vs conversionm
*/
WITH sla_flagged AS (
    SELECT 
        pj.patient_id,
        pj.consultation_booked,
        pj.treatment_completed,
        CASE 
            WHEN pj.response_time_hours > cr.baseline_response_expectation_hours THEN 1
            ELSE 0
        END AS sla_breach
    FROM patient_journey pj
    JOIN country_reference cr ON pj.country = cr.country
)
SELECT 
    sla_breach,
    COUNT(*) AS total_patients,
    ROUND(AVG(consultation_booked) * 100, 2) AS consultation_rate_pct,
    ROUND(AVG(treatment_completed) * 100, 2) AS treatment_rate_pct
FROM sla_flagged
GROUP BY sla_breach;

/*
Q8 - Full provider scorecard
*/
WITH provider_sla AS (
    SELECT 
        pj.provider_id,
        AVG(CASE WHEN pj.response_time_hours > cr.baseline_response_expectation_hours THEN 1.0 ELSE 0.0 END) AS sla_breach_rate
    FROM patient_journey pj
    JOIN country_reference cr ON pj.country = cr.country
    GROUP BY pj.provider_id
),
provider_outcomes AS (
    SELECT 
        pj.provider_id,
        COUNT(*) AS total_patients,
        AVG(pj.consultation_booked) AS consultation_rate,
        AVG(pj.treatment_completed) AS treatment_rate,
        AVG(pj.follow_up_completed) AS follow_up_rate,
        AVG(pj.satisfaction_score) AS avg_satisfaction,
        AVG(pj.actual_revenue_inr - pj.service_cost_inr) AS avg_margin
    FROM patient_journey pj
    GROUP BY pj.provider_id
)
SELECT 
    po.provider_id,
    pm.region,
    pm.specialty_area,
    po.total_patients,
    ROUND(po.consultation_rate * 100, 2) AS consultation_rate_pct,
    ROUND(po.treatment_rate * 100, 2) AS treatment_rate_pct,
    ROUND(ps.sla_breach_rate * 100, 2) AS sla_breach_rate_pct,
    ROUND(po.follow_up_rate * 100, 2) AS follow_up_rate_pct,
    ROUND(po.avg_satisfaction, 2) AS avg_satisfaction,
    ROUND(po.avg_margin, 2) AS avg_margin_inr
FROM provider_outcomes po
JOIN provider_sla ps ON po.provider_id = ps.provider_id
JOIN provider_master pm ON po.provider_id = pm.provider_id
ORDER BY treatment_rate_pct DESC;