FROM python:3.11-alpine

LABEL maintainer="https://github.com/Sver0411/daily-push"
LABEL description="Daily course schedule + weather notifier"

# Set timezone
RUN apk add --no-cache tzdata && \
    cp /usr/share/zoneinfo/Asia/Shanghai /etc/localtime && \
    echo "Asia/Shanghai" > /etc/timezone

WORKDIR /app

COPY daily_push.py .

# Inject via environment variables
ENV FEISHU_WEBHOOK=""
ENV CITY="Beijing"

CMD ["python3", "daily_push.py"]
