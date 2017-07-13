FROM pretix/standalone

USER root

ADD . /pretix/pretix_avgchart

WORKDIR /pretix/pretix_avgchart
RUN python3 setup.py develop

WORKDIR /pretix/src
USER pretixuser
RUN cd /pretix/src && make production
