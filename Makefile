.PHONY: up network

# Ensure network exists
network:
	docker network create ckn-network

# Bring up services
up: network
	docker-compose up

# Bring down services
down:
	docker network rm ckn-network
	docker-compose down
