# cypher queries

# Find experiments that have finished (deployment end_time is set) but haven't been processed yet (experiment end_time is null)
CYPHER_FIND_COMPLETABLE_EXPERIMENTS = """
MATCH (ex:Experiment)-[:DEPLOYMENT_INFO]->(d:Deployment)
WHERE d.end_time IS NOT NULL AND ex.end_time IS NULL AND ex.start_time IS NOT NULL
RETURN ex.experiment_id AS experiment_id, ex.start_time AS start_time_ms, d.end_time AS end_time_ms
LIMIT 500
"""

#Calculate accuracy for a SPECIFIC experiment
CYPHER_CALCULATE_ACCURACY = """
MATCH (ri:RawImage)-[pb:PROCESSED_BY]->(e:Experiment {experiment_id: $experiment_id})
WITH ri, pb, e, apoc.convert.fromJsonList(pb.scores) AS scoresList
WHERE scoresList IS NOT NULL 
UNWIND scoresList AS score
WITH ri, e, score.label AS label, score.probability AS probability
ORDER BY probability DESC
WITH ri, e,
    CASE WHEN collect(probability)[0] < $confidence_threshold THEN 'empty' ELSE collect(label)[0] END AS predicted_label,
    CASE WHEN ri.ground_truth IS NULL OR ri.ground_truth = 'unknown' THEN 'empty' ELSE ri.ground_truth END AS ground_truth
WHERE predicted_label IS NOT NULL AND ground_truth IS NOT NULL
WITH ri, e, predicted_label, ground_truth,
    CASE WHEN ground_truth = predicted_label THEN 1 ELSE 0 END AS correct 
WITH e, count(ri) as image_count, sum(correct) as correct_count
WHERE image_count > 0 
RETURN e.experiment_id AS experimentId, (toFloat(correct_count) / image_count) * 100.0 AS averageAccuracy
"""

# Update Experiment with end_time, duration, and accuracy
CYPHER_UPDATE_COMPLETED_EXPERIMENT = """
MATCH (ex:Experiment {experiment_id: $experiment_id})
SET ex.end_time = $end_time_ms,
    ex.average_accuracy = $accuracy,
    ex.start_datetime = datetime({epochMillis: $start_time_ms}), 
    ex.end_datetime = datetime({epochMillis: $end_time_ms}),  
    ex.experiment_duration = duration.between(ex.start_datetime, ex.end_datetime)
RETURN ex.experiment_id as id, ex.experiment_duration as duration, ex.average_accuracy as accuracy
"""

# Find experiments with low accuracy that haven't been alerted yet
CYPHER_FIND_LOW_ACCURACY_FOR_ALERT = """
MATCH (e:Experiment)
WHERE e.accuracy IS NOT NULL AND e.accuracy < $accuracy_threshold
MATCH (e)-[:USED]->(m:Model)
RETURN e.id AS experiment_id, e.accuracy AS accuracy, properties(e) AS metadata, m.model_id AS model_id
LIMIT $batch_size 
"""

