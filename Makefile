# Variables
IMAGE_NAME = vo1d/config-merger
TAG := $(shell git rev-parse --short HEAD)
CONTAINER_NAME = config-merger
MOUNT_PATH = $(PWD)

.PHONY: build push run logs kill

build:
	docker build -f automation/docker/Dockerfile -t $(IMAGE_NAME):$(TAG) . && \
	docker tag $(IMAGE_NAME):$(TAG) $(IMAGE_NAME):latest

push:
	docker push $(IMAGE_NAME):$(TAG) && \
	docker push $(IMAGE_NAME):latest

run:
	docker run \
		--rm \
		--name $(CONTAINER_NAME) \
		-v $(MOUNT_PATH):/app \
		$(IMAGE_NAME):$(TAG) \
		-i test \
		-o output.yaml

kill:
	docker rm -f $(CONTAINER_NAME) || true