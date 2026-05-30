// Show a small part of the graph
MATCH (n)-[r]->(m)
RETURN n, r, m
LIMIT 50;

// Find devices shared by many users
MATCH (u:User)-[:USED_DEVICE]->(d:Device)
WITH d, count(DISTINCT u) AS users
WHERE users >= 4
RETURN d.device_id AS device_id, users
ORDER BY users DESC
LIMIT 20;

// Find IP addresses with high fraud rate
MATCH (t:Transaction)-[:FROM_IP]->(ip:IPAddress)
WITH ip, count(t) AS total_tx, avg(CASE WHEN t.is_fraud = 1 THEN 1.0 ELSE 0.0 END) AS fraud_rate
WHERE total_tx >= 5
RETURN ip.ip_address AS ip_address, total_tx, fraud_rate
ORDER BY fraud_rate DESC
LIMIT 20;

// Find users connected to a specific device
MATCH (u:User)-[:USED_DEVICE]->(:Device {device_id: "D0001"})
RETURN u.user_id AS user_id
LIMIT 50;
