# app/models/audit.py
from app.extensions import db
from datetime import datetime

class AuditLog(db.Model):
    __tablename__ = "audit_logs"
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    user_id = db.Column(db.String(128), nullable=True)
    endpoint = db.Column(db.String(256), nullable=False)
    payload = db.Column(db.JSON, nullable=True)
    result = db.Column(db.JSON, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
