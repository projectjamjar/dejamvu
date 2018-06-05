PYTHON=python3
PIP=pip3
SRC_DIR=lilo

default: run

###########################################
# Install
###########################################
install: requirements.txt
	$(PIP) install -r requirements.txt

###########################################
# Runners
###########################################
run: install
	$(PYTHON) $(SRC_DIR)/ingest_audio.py


###########################################
# Cleanup
###########################################
clean:
	find . -name "*.pyc" -print0 | xargs -0 rm