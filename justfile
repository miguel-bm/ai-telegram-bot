# Build the Docker image using Docker Compose
build:
    docker-compose build

# Run the bot in a Docker container using Docker Compose
run:
    docker-compose up -d

# Stop the running Docker container and remove its resources using Docker Compose
stop:
    docker-compose down

# Rebuild and rerun the Docker container using Docker Compose
rebuild_rerun:
    just down
    just build
    just run

# Enter the command line inside the running Docker container
shell:
    docker exec -it your_bot_container_name /bin/bash

terraform-init:
    #!/bin/sh
    cd terraform
    ./run_terraform.sh init


terraform-validate:
    #!/bin/sh
    cd terraform
    ./run_terraform.sh validate

terraform-plan:
    #!/bin/sh
    cd terraform
    ./run_terraform.sh plan


terraform-apply:
    #!/bin/sh
    cd terraform
    ./run_terraform.sh apply


terraform-destroy:
    #!/bin/sh
    cd terraform
    ./run_terraform.sh destroy
