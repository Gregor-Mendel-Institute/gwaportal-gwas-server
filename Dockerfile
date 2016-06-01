# Dockerfile for docker-gwaportal-gwas-server
# Version 0.1

FROM timeu/docker-gwas-base
MAINTAINER Uemit Seren <uemit.seren@gmail.com>

WORKDIR /tmp 

RUN mkdir /GWAS_STUDY_FOLDER && mkdir /GENOTYPE_FOLDER && mkdir /GWAS_VIEWER_FOLDER

COPY . /tmp

RUN /env/bin/pip install --upgrade pip

# because of this issue https://github.com/matplotlib/matplotlib/pull/5954
RUN /env/bin/pip install --upgrade git+git://github.com/matplotlib/matplotlib.git@31fa2b2ef0aafe6a53f648c4845542bfdeb45f41#egg=matplotlib

RUN /env/bin/pip install . && rm -fr /tmp/*


VOLUME ["/GWAS_STUDY_FOLDER","/GENOTYPE_FOLDER","GWAS_VIEWER_FOLDER"]


ENV GWAS_STUDY_FOLDER /GWAS_STUDY_FOLDER

ENV GENOTYPE_FOLDER /GENOTYPE_FOLDER

ENV GWAS_VIEWER_FOLDER /GWAS_VIEWER_FOLDER

CMD ["/env/bin/gunicorn","-b","0.0.0.0:8000","gwasrv:api"]