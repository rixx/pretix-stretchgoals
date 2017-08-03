FROM pretix/standalone

USER root

ADD . /pretix/pretix_stretchgoals

WORKDIR /pretix/pretix_stretchgoals
RUN python3 setup.py develop

WORKDIR /pretix/src
USER pretixuser
RUN cd /pretix/src && make production
