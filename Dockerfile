FROM mcr.microsoft.com/playwright/python:v1.55.0-jammy

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# If not using a Playwright base image, you would also do:
#RUN pip install playwright

RUN playwright install --with-deps

WORKDIR /app
COPY app/ .

RUN mkdir -p /app/data && mkdir -p /app/log
ENV HEADLESS=true
ENV PYTHONPATH="/app/legacy/WebService"

EXPOSE 8000
CMD ["gunicorn", "-c", "gunicorn.conf.py", "main:app", "--reload"]
#FOR TESTING ADD - "--reload" AFTER LAST LINE
