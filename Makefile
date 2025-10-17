.PHONNY: all lms-start lms-stop

all: lms-start

LMS=${HOME}/.lmstudio/bin/lms

lms-start:
	${LMS} server start

	# support cold start by waiting for service to start
	@sleep 3

	${LMS} load openai/gpt-oss-20b \
		--gpu=max \
		--context-length=10000

	${LMS} load qwen/qwen3-4b-thinking-2507 \
		--gpu=max \
		--context-length=4096

lms-stop:
	${LMS} server stop

	${LMS} unload --all
