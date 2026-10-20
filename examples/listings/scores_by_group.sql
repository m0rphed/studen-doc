SELECT s.group_id,
       AVG(r.score) AS mean_score,
       COUNT(*)     AS n
FROM results AS r
JOIN students AS s ON s.id = r.student_id
WHERE r.score IS NOT NULL
GROUP BY s.group_id
HAVING COUNT(*) > 5
ORDER BY mean_score DESC;
