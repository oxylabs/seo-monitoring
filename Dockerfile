FROM python:3.10

RUN mkdir /app
WORKDIR /app

RUN apt update && \
apt install -y python3-distutils python3-setuptools python3-lxml

COPY requirements.txt ./
RUN pip install --upgrade pip wheel setuptools
RUN pip install --no-cache-dir -r requirements.txt

RUN groupadd -r scrapers && useradd -m -r -g scrapers oxy
RUN chown oxy /app
USER oxy

RUN /usr/local/bin/python -c "import nltk; nltk.download('punkt')"
RUN /usr/local/bin/python -c "import nltk; nltk.download('stopwords')"
COPY . .
