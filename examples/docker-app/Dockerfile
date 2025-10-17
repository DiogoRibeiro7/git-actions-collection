FROM python:3.11-slim AS app
WORKDIR /app
COPY app.py .
ARG APP_MESSAGE="Hello from Docker"
ENV APP_MESSAGE=${APP_MESSAGE}
CMD ["python", "app.py"]
