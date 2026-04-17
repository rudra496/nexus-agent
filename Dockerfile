FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ src/
COPY setup.py pyproject.toml ./

RUN pip install -e .

RUN mkdir -p /workspace/.nexus/{skills,plugins,memory}
WORKDIR /workspace

ENTRYPOINT ["nexus"]
CMD ["--help"]
