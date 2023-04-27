VERSION=0.0.10

run:
	docker-compose up

build:
	docker build . -f Dockerfile -t reecepbcups/rpc-cache:$(VERSION)
	docker build . -f Dockerfile.rest -t reecepbcups/api-cache:$(VERSION)

push:
	docker push reecepbcups/api-cache:$(VERSION)
	docker push reecepbcups/rpc-cache:$(VERSION)