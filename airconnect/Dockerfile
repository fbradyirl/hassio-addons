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

# Required  For an armv6 (Pi A and Zero)
RUN wget http://mirrordirector.raspbian.org/raspbian/pool/main/o/openssl/libssl1.0.0_1.0.1t-1+deb8u8_armhf.deb
RUN dpkg -i libssl1.0.0_1.0.1t-1+deb8u8_armhf.deb

# Download AirConnect
RUN wget --output-document=/bin/airupnp-arm https://raw.githubusercontent.com/philippe44/AirConnect/master/bin/airupnp-arm && chmod +x /bin/airupnp-arm
RUN wget --output-document=/bin/aircast-arm https://raw.githubusercontent.com/philippe44/AirConnect/master/bin/aircast-arm && chmod +x /bin/aircast-arm

ENTRYPOINT ["supervisord", "--nodaemon", "--configuration", "/etc/supervisord.conf"]