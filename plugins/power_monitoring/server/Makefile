# Ensure network exists
network:
	docker network create ckn-network || true

# Bring up services
up: network
	docker-compose up -d

# Bring down services
down:
	docker-compose down
	docker network rm ckn-network || true