ARG BUILD_FROM
FROM ${BUILD_FROM}


# Setup base system
RUN \
    echo 'deb http://deb.debian.org/debian jessie main' >> /etc/apt/sources.list \
    \
    && apt-get update \
    \
    && apt-get install -y supervisor wget \
    \
    && rm -f -r \
        /tmp/* \
        /var/lib/apt/lists/*

COPY supervisord.conf /etc

# Download AirConnect
RUN wget --output-document=/bin/airupnp-arm https://raw.githubusercontent.com/philippe44/AirConnect/master/bin/airupnp-arm5 && chmod +x /bin/airupnp-arm
RUN wget --output-document=/bin/aircast-arm https://raw.githubusercontent.com/philippe44/AirConnect/master/bin/aircast-arm5 && chmod +x /bin/aircast-arm

ENTRYPOINT ["supervisord", "--nodaemon", "--configuration", "/etc/supervisord.conf"]