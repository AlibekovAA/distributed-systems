FROM debian:bookworm-slim

RUN apt-get update && \
    apt-get install -y curl openjdk-17-jre-headless --no-install-recommends && \
    curl -o allure-2.24.1.tgz -Ls https://repo.maven.apache.org/maven2/io/qameta/allure/allure-commandline/2.24.1/allure-commandline-2.24.1.tgz && \
    tar -xz -C /opt/ -f allure-2.24.1.tgz && \
    ln -s /opt/allure-2.24.1/bin/allure /usr/bin/allure && \
    rm allure-2.24.1.tgz && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

ENV PATH="/opt/allure-2.24.1/bin:$PATH"
ENV JAVA_HOME="/usr/lib/jvm/java-17-openjdk-amd64"
ENV PATH="$JAVA_HOME/bin:$PATH"
