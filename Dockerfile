FROM docker.dbc.dk/dbc-python3
LABEL MAINTAINER=metascrum

RUN pip install --upgrade pip
RUN apt-get install -y --no-install-recommends wget

RUN apt-get remove -y wget
RUN apt-get autoremove -y
COPY src src
COPY setup.py setup.py
RUN pip install -e .
CMD ["main"]
