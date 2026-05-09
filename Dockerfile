FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml setup.py ./
COPY src/ src/

RUN pip install --no-cache-dir .

RUN mkdir -p /workspace/.nexus/{skills,plugins,memory}
WORKDIR /workspace

ENTRYPOINT ["nexus"]
CMD ["--help"]
