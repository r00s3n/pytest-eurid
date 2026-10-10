FROM python:3.12-slim

WORKDIR /opt/pytest

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Default command: run only tests marked "smoke"
CMD ["pytest", "-m", "smoke", "--junitxml=results/junit.xml"]
