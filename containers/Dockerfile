FROM python:3.9-slim as base

ENV DEBIAN_FRONTEND=noninteractive

RUN useradd --create-home --shell /bin/bash tsx_user

RUN apt-get update && \
apt-get install -y --no-install-recommends libgdal-dev r-base git python3-dev build-essential libharfbuzz-dev libfribidi-dev  libfontconfig1-dev libgit2-dev libssl-dev  default-mysql-client

FROM base as prod

LABEL org.opencontainers.image.source https://github.com/nesp-tsr3-1/tsx

WORKDIR /root
COPY requirements.txt .

RUN pip install -r requirements.txt

RUN R --no-save <<EOF
options(Ncpus = 1)
install.packages("devtools")
library(devtools)
install.packages("ggplot2")
install_github("nesp-tsr3-1/rlpi", dependencies=TRUE)
install.packages("IRkernel")
install.packages("tidyverse")
install.packages("data.table")
EOF

COPY sample-data/ sample-data/
COPY tsx/ tsx/
COPY db/ db/
COPY r/ r/
COPY containers/tsx.conf tsx.conf
COPY containers/bashrc .bashrc
COPY containers/my.cnf .my.cnf

CMD ["bash"]
