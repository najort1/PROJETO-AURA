# Aura 2.0 - wrapper de conveniência.
# Em Windows sem GNU Make, use diretamente: python tasks.py <alvo>

PYTHON ?= python

.PHONY: help all ingest synth features train score sentiment rag agent-eval agent-precompute fairness impact dictionary app test lint fmt

help:
	@$(PYTHON) tasks.py help

all ingest synth features train score sentiment rag agent-eval agent-precompute fairness impact dictionary app test lint fmt:
	@$(PYTHON) tasks.py $@
