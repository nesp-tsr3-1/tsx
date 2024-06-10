FROM python:3.9-slim as base

ENV DEBIAN_FRONTEND=noninteractive

RUN useradd --create-home --shell /bin/bash tsx_user

RUN apt-get update && \
apt-get install -y --no-install-recommends libgdal-dev r-base git python3-dev build-essential libharfbuzz-dev libfribidi-dev  libfontconfig1-dev libgit2-dev libssl-dev  default-mysql-client libbz2-dev

FROM base as prod

LABEL org.opencontainers.image.source https://github.com/nesp-tsr3-1/tsx

WORKDIR /root
COPY Pipfile Pipfile.lock .

RUN pip install pipenv
RUN pipenv sync --system

RUN R --no-save <<EOF
options(Ncpus = 1)
install.packages("pak")
pak::pkg_install("ggplot2")
pak::pkg_install("nesp-tsr3-1/rlpi")
pak::pkg_install("IRkernel")
pak::pkg_install("data.table")
pak::pkg_install("dplyr")
pak::pkg_install("plyr")
pak::pkg_install("tidyr")
pak::pkg_install("docopt")
EOF

COPY sample-data/ sample-data/
COPY tsx/ tsx/
COPY db/ db/
COPY r/ r/
COPY containers/tsx.conf tsx.conf
COPY containers/bashrc .bashrc
COPY containers/my.cnf .my.cnf

CMD ["bash"]
