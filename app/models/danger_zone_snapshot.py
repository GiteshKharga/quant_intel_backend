# app/models/danger_zone_snapshot.py

from app.extensions import db
from datetime import datetime

class DangerZoneSnapshot(db.Model):
    __tablename__ = "danger_zone_snapshots"

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    symbol = db.Column(db.String(64), nullable=False, index=True)
    data = db.Column(db.JSON, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
