.PHONY: all

all: .built

.built: Dockerfile pyproject.toml uv.lock
	docker buildx build -t ltrcrt2000 .
	-docker image remove ralphschmieder/ltrcrt-2000:latest
	docker tag ltrcrt2000:latest  ralphschmieder/ltrcrt-2000:latest
	docker push ralphschmieder/ltrcrt-2000
	uv export --format requirements-txt --no-hashes >requirements.txt
	touch $@
