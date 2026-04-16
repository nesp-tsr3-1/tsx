FROM debian:stable-slim as base

ENV DEBIAN_FRONTEND=noninteractive

RUN useradd --create-home --shell /bin/bash tsx_user

RUN apt-get update && \
apt-get install -y --no-install-recommends libgdal-dev r-base r-base-dev git build-essential libharfbuzz-dev libfribidi-dev  libfontconfig1-dev libgit2-dev libssl-dev  default-mysql-client libbz2-dev curl

RUN mkdir /tsx

WORKDIR /tsx
COPY pyproject.toml uv.lock .

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy from the cache instead of linking since it's a mounted volume
ENV UV_LINK_MODE=copy
# Omit development dependencies
ENV UV_NO_DEV=1
# Ensure installed tools can be executed out of the box
ENV UV_TOOL_BIN_DIR=/usr/local/bin

RUN uv python install 3.12.12
RUN uv sync

RUN mkdir renv
COPY renv.lock .Rprofile .
COPY renv/activate.R renv
COPY renv/settings.json renv

RUN Rscript -e 'renv::restore()'

#----- Workflow CLI -----

FROM base AS cli

COPY <<EOF /root/.my.cnf
[client]
user=tsx
password=tsx
host=mysql
database=tsx
skip-ssl
EOF

RUN echo 'PS1="TSX:\w# "' >> /root/.bashrc

CMD ["bash"]

#----- Jupyter Lab ------

FROM base AS jupyter

CMD ["uv", "run", "--with", "jupyterlab", "jupyter", "lab", "--allow-root", "--ip", "0.0.0.0", "--no-browser", "--LabApp.token=''"]

#----- Test -----

FROM base as test

COPY tsx.conf.test tsx.conf.test

COPY <<EOF /root/.my.cnf
[client]
user=root
password=root
host=mysql
database=information_schema
skip-ssl
EOF


CMD ["uv", "run", "python", "-m", "pytest", "tests"]

#----- Front-end

FROM node:22 as frontend
USER 1000
RUN mkdir -p /home/node/app/node_modules
