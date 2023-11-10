default: help

.PHONY: help test coverage run dev docker-build docker-build-x86 docker-run docker-stop docker-rm redis

help: # Show help for each of the Makefile recipes.
	@grep -E '^[a-zA-Z0-9 -]+:.*#'  Makefile | while read -r l; do printf "\033[1;32m$$(echo $$l | cut -f 1 -d':')\033[00m:$$(echo $$l | cut -f 2- -d'#')\n"; done

test: # run unit tests for backend service
	poetry run isort . --src=app --src=tests
	poetry run pycodestyle --ignore "E501, E402, W503, W504" app
	poetry run coverage run --source=app -m unittest -v
	poetry run coverage report

install: # install dependencies
	poetry install
	poetry run pre-commit install
	@if [ ! -f .env ]; then\
		cp .env.example .env;\
	fi
	@echo ""
	@echo "##### install complete #####"
	@echo "Please fill in .env file"

coverage: # show coverage report
	poetry run coverage report

run: # run service without reload flag
	poetry run uvicorn app.main:app

dev: # run service with reload flag
	poetry run uvicorn app.main:app --reload

build: # build docker image
	docker build -t asia-east1-docker.pkg.dev/tw-rd-sa-zoe-lin/cloud-native-repository/cloud-native-backend .

build-x86: # build x86_64 docker image
	docker build --platform=linux/amd64 -t asia-east1-docker.pkg.dev/tw-rd-sa-zoe-lin/cloud-native-repository/cloud-native-backend .

docker-run: # run docker container with newest image of "cloud-native", backend port would be 8000
	docker run -d --name cloud-native-backend -p 8000:80 cloud-native-backend

docker-stop: # stop cloud-native container
	docker stop cloud-native-backend

docker-rm: # rm cloud-native container
	docker rm cloud-native-backend

redis: # run redis docker
	docker run -d --rm --name redis -p 6379:6379 redis

helm: # helm upgrade
	helm upgrade cloud-native-backend deploy/helm/charts \
        --install \
        --namespace=prod  \
        --values deploy/helm/production/values.yaml \
        --set image.tag=x86-202310241732

show-url: # show helm deployment's service url
	NODE_PORT=$(shell kubectl get --namespace prod -o jsonpath="{.spec.ports[0].nodePort}" services cloud-native-backend); \
	NODE_IP=$(shell kubectl get nodes --namespace prod -o jsonpath="{.items[0].status.addresses[0].address}"); \
	echo http://$${NODE_IP}:$${NODE_PORT}

cloud-sql-proxy: # start up cloud sql proxy for postgres
	docker run -d --rm \
		-v ./config/gcp-service-account.json:/config \
		-p 127.0.0.1:5432:5432 \
		--name cloud_sql_proxy \
		gcr.io/cloudsql-docker/gce-proxy:1.12 /cloud_sql_proxy \
		-instances=tw-rd-sa-zoe-lin:asia-east1:cloud-native-db-instance=tcp:0.0.0.0:5432 -credential_file=/config
