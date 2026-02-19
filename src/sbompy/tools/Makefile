# Variables
SBOM_DIR = sbom_data
ENV_FILE = .env

# Get the TPot version and repository
TPOT_VERSION = $(shell cat $(ENV_FILE) | grep TPOT_VERSION | cut -d '=' -f 2)
TPOT_REPO = $(shell cat $(ENV_FILE) | grep TPOT_REPO | cut -d '=' -f 2)

VM_SBOM_FILE = $(SBOM_DIR)/vm_sbom.json

# List of images
IMAGES = conpot cowrie dionaea elasticpot elasticsearch ewsposter fatt kibana logstash map nginx p0f redis spiderfoot suricata

# Default target
all: docker-all vm-all


# All docker 
docker-all: check_env $(SBOM_DIR) generate_docker_sboms


# All vm 
vm-all: check_syft generate_vm_sbom


# Check if the environment file exists

check_env:
	@if [ ! -f $(ENV_FILE) ]; then \
		echo "Environment file not found"; \
		exit 1; \
	fi
	@echo "Environment file found"




# Install sbom-cli-plugin
install_sbom_plugin:
	@if [ "$$(id -u)" -eq 0 ]; then \
		echo "Please don't run as root"; \
		exit 1; \
	fi
	@if ! command -v docker &> /dev/null; then \
		echo "Docker could not be found"; \
		exit 1; \
	fi
	mkdir -p ~/.docker
	curl -sSfL https://raw.githubusercontent.com/docker/sbom-cli-plugin/main/install.sh | sh -s --


# Create the SBOM directory
$(SBOM_DIR):
	mkdir -p $(SBOM_DIR)

# Generate SBOMs for all images
generate_docker_sboms: $(IMAGES:%=$(SBOM_DIR)/%.json)

# Rule to generate SBOM for a single image
$(SBOM_DIR)/%.json: 
	docker sbom $(TPOT_REPO)/$*:$(TPOT_VERSION) --format syft-json  --output $@

# Clean up generated SBOM files
clean:
	rm -rf $(SBOM_DIR)


# Check if Syft is installed, and install if not
check_syft:
	@if ! command -v syft &> /dev/null; then \
		echo "Syft not found, installing..."; \
		curl -sSfL https://raw.githubusercontent.com/anchore/syft/main/install.sh | sudo sh -s -- -b /usr/local/bin; \
	else \
		echo "Syft is already installed."; \
	fi


# Generate the SBOM
generate_vm_sbom: $(SBOM_DIR) check_syft
	@echo "Generating SBOM for the entire system..."
	@sudo syft / -o cyclonedx-json=$(VM_SBOM_FILE)
	@if [ -f $(VM_SBOM_FILE) ]; then \
		echo "SBOM successfully created: $(VM_SBOM_FILE)"; \
	else \
		echo "Error: SBOM generation failed!"; \
	fi



# Help target
help:
	@echo "Available targets:"
	@echo "  all                	- Check environment and generate SBOMs for everything in the vm "
	@echo "  check_env          	- Check if the environment file exists"
	@echo "  install_sbom_plugin 	- Install the SBOM CLI plugin for Docker"
	@echo "  generate_docker_sboms     	- Generate SBOMs for all images"
	@echo "  clean              	- Remove generated SBOM files"
	@echo "  docker-all 			- Check environment and generate SBOMs for all docker images"
	@echo "  check_syft     		- Check if Syft is installed and install it if not"
	@echo "  generate_sbom  		- Generate the SBOM for the system"
	@echo "  clean          		- Remove generated files"
	@echo "  help           		- Show this help message"


.PHONY: all help docker-all generate_docker_sboms check_env clean install_sbom_plugin check_syft generate_vm_sbom
