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

ARG BUILD_ARCH

RUN echo "BUILD_ARCH: ${BUILD_ARCH}"

# Download AirConnect
RUN wget --output-document=/bin/airupnp-${BUILD_ARCH} https://raw.githubusercontent.com/philippe44/AirConnect/master/bin/airupnp-${BUILD_ARCH} && chmod +x /bin/airupnp-${BUILD_ARCH}
RUN wget --output-document=/bin/aircast-${BUILD_ARCH} https://raw.githubusercontent.com/philippe44/AirConnect/master/bin/aircast-${BUILD_ARCH} && chmod +x /bin/aircast-${BUILD_ARCH}

ENTRYPOINT ["supervisord", "--nodaemon", "--configuration", "/etc/supervisord.conf"]