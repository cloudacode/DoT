FROM python:2.7.13-alpine

COPY app /app
WORKDIR /app

ENV DOT_PORT 53
ENV DNS_SERVER_IP '1.1.1.1'
ENV DNS_SERVER_PORT 853

CMD ["python","dns_over_tls.py"]