.PHONY: up network down

# Ensure network exists
network:
	docker network create ckn-network || true

# Check Neo4j health
check-neo4j-server:
	@while ! docker exec neo4j_server cypher-shell -u neo4j -p PWD_HERE "RETURN 1" > /dev/null 2>&1; do \
		echo "neo4j-server starting..."; \
		sleep 5; \
	done

# Bring up services
up: network
	docker-compose up -d

	# Check if neo4j-server has started and then add constraints
	$(MAKE) check-neo4j-server
	docker cp ckn_kg/constraints.cypher neo4j_server:/constraints.cypher
	docker exec -it neo4j_server cypher-shell -u neo4j -p PWD_HERE -f /constraints.cypher

# Bring down services
down:
	docker-compose down
	docker network rm ckn-network || true
