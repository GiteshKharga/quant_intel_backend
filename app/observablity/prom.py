# app/observability/prom.py
from prometheus_flask_exporter import PrometheusMetrics

metrics = None

def init_metrics(app):
    global metrics
    metrics = PrometheusMetrics(app, group_by='path')
    # add custom metrics if needed
    metrics.info('app_info', 'Application info', version='1.0.0')
