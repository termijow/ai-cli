FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml ./
RUN pip install --no-cache-dir \
    fastapi>=0.109.0 \
    "uvicorn[standard]>=0.27.0" \
    pdfplumber>=0.11.0 \
    python-docx>=1.1.0 \
    markdown>=3.5.0 \
    requests>=2.31.0 \
    httpx>=0.27.0 \
    python-multipart>=0.0.9 \
    "reportlab>=4.0.0"

COPY . .

EXPOSE 3094
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "3094", "--log-level", "info"]
