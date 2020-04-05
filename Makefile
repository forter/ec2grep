ECR_URL 				?= 174522763890.dkr.ecr.us-east-1.amazonaws.com

.PHONY: build
build: build-py2 build-py3

build-py2: PYTHON_VERSION = 2.7.17
build-py3: PYTHON_VERSION = 3.8.1


build-py3 build-py2:
	@echo "======= Building Python $(PYTHON_VERSION) ========"
	docker build --pull --build-arg "PYTHON_VERSION=$(PYTHON_VERSION)" .

ci-test:
	echo "No tests"

dist:
	echo "Actual dist is done in the post-dist stage"

ci-lint:
	@echo "======= Linting ========"
	docker run \
		-v $(PWD)/:/app/ \
		-v $(PWD)/test-reports:/test-reports/ \
		${ECR_URL}/python-black

black:
	docker run \
		-v $(PWD)/:/app/ \
		--entrypoint black \
		${ECR_URL}/python-black \
		/app/

