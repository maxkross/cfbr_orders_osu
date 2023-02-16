install_venv:
	python -m venv venv && source venv/bin/activate && pip install -r requirements.txt

deploy_venv:
	pip freeze > requirements.txt
