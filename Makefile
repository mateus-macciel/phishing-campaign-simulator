PY ?= python

.PHONY: demo data analyze preview test clean

demo: data analyze preview

data:
	$(PY) src/simulate_campaign.py --employees 600 --seed 42

analyze:
	$(PY) src/analyze.py

preview:
	$(PY) src/render_templates.py

test:
	$(PY) -m unittest discover -s tests -v

clean:
	rm -rf output
