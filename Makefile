dev:
	docker compose up

prod:
	docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
