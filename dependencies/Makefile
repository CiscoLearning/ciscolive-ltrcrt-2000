USER := "ralphschmieder"
NAME := "ltrcrt2000"

.PHONY: all

all: .built

.built: Dockerfile pyproject.toml uv.lock
	docker buildx build -t $(NAME) .
	-docker image remove $(USER)/$(NAME):latest
	docker tag $(NAME):latest $(USER)/$(NAME):latest
	docker push $(USER)/$(NAME)
	uv export --format requirements-txt --no-hashes >requirements.txt
	touch $@
