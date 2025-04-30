ARG BUILD_FROM=ghcr.io/home-assistant/amd64-base:latest
FROM ${BUILD_FROM}

# Set labels
LABEL maintainer="yourname@example.com"

# Pull the existing StreamMaster image content
COPY --from=ghcr.io/carlreid/streammaster:latest / / 

# Set working directory
WORKDIR /config

# Expose the web UI port
EXPOSE 7095

# Command to run
CMD [ "/init" ]