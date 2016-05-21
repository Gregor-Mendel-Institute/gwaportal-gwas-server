# Dockerfile for docker-gwaportal-gwas-server
# Version 0.1

FROM timeu/docker-gwas-base
MAINTAINER Uemit Seren <uemit.seren@gmail.com>

WORKDIR /tmp 

RUN mkdir /GWAS_STUDY_FOLDER && mkdir /GENOTYPE_FOLDER

COPY . /tmp

RUN /env/bin/pip install . && rm -fr /tmp/*

VOLUME ["/GWAS_STUDY_FOLDER","/GENOTYPE_FOLDER"]


ENV GWAS_STUDY_FOLDER /GWAS_STUDY_FOLDER

ENV GENOTYPE_FOLDER /GENOTYPE_FOLDER

CMD ["/env/bin/gunicorn","gwasrv:api"]