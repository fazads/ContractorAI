backend:
	cd backend && uvicorn app.main:app --reload --port 8000

frontend:
	cd frontend && npm install && npm run dev

docker-build:
	docker compose build

docker-run:
	docker compose up --build
