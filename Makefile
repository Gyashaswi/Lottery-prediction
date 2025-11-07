.PHONY: update fetch clean load star dq idx

update: fetch clean load star dq idx
	@echo "✅ Pipeline complete."

fetch:
	python -m src.ingest.fetch_api

clean:
	python -m src.ingest.clean_data

load:
	python -m src.ingest.load_to_db

star:
	python -m src.ingest.load_to_star

dq:
	python -m src.ingest.dq_checks

idx:
	python -m src.ingest.build_indices
