# Docker image name
DOCKER_USERNAME?=issgupat
DOCKER_IMAGE_NAME?=sbompy
DOCKER_IMAGE_NAME_MODIFIED?=sbompy-modified
TAG?=latest
DOCKERFILE ?= Dockerfile
DOCKERFILE_MODIFIED ?= Dockerfile.modified


.PHONY: build build-modified delete delete-modified push help


# ╔════════════════════════════════════════╗
# ║ Docker Image Build, Delete, and Upload ║
# ╚════════════════════════════════════════╝

build:
	docker build \
		-t $(DOCKER_IMAGE_NAME) \
		-f ./src/$(DOCKERFILE) ../.
	@echo "Docker image $(DOCKER_IMAGE_NAME)  built successfully."

# Build new image based on the previous one with updated scripts
build-modified:
	docker build \
		--build-arg BASE_IMAGE=$(DOCKER_IMAGE_NAME) \
		-t $(DOCKER_IMAGE_NAME_MODIFIED) \
		-f ./src/$(DOCKERFILE_MODIFIED) ../.

build-alpine:
	docker build -t $(DOCKER_IMAGE_NAME):alpine -f ./src/Dockerfile.alpine ../.
	@echo "Docker image $(DOCKER_IMAGE_NAME):alpine built successfully."


delete:
	@docker rmi -f $(DOCKER_IMAGE_NAME)
	@echo "Docker image $(DOCKER_IMAGE_NAME) deleted successfully."

delete-modified:
	@docker rmi -f $(DOCKER_IMAGE_NAME_MODIFIED)
	@echo "Docker image $(DOCKER_IMAGE_NAME_MODIFIED) deleted successfully."

push:
	@docker tag $(DOCKER_IMAGE_NAME) $(DOCKER_USERNAME)/$(DOCKER_IMAGE_NAME):$(TAG)
	@docker push $(DOCKER_USERNAME)/$(DOCKER_IMAGE_NAME)
	@echo "Docker image $(DOCKER_USERNAME)/$(DOCKER_IMAGE_NAME) pushed to Docker Hub successfully."



compose-up:
	docker compose up --build 

compose-down:
	docker compose down


# ╔════════════════╗
# ║ Help Function  ║
# ╚════════════════╝

help:
	@echo "Makefile commands:"
	@echo "  build                - Build the Docker image."
	@echo "  build-modified       - Build a modified Docker image based on the previous one."
	@echo "  delete               - Delete the Docker image."
	@echo "  delete-modified      - Delete the modified Docker image."
	@echo "  push                 - Push the Docker image to Docker Hub."
