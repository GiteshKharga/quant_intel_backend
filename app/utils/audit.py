# app/utils/audit.py
from functools import wraps
from flask import request, current_app
from app.extensions import db
from app.models.audit import AuditLog

# We do a lazy import of flask_jwt_extended to avoid import-time failure
def _get_jwt_identity():
    try:
        from flask_jwt_extended import get_jwt_identity
    except Exception:
        # jwt not available — return a no-op function
        return lambda: None
    return get_jwt_identity


def audit_endpoint(endpoint_name=None):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            get_jwt = _get_jwt_identity()
            try:
                user = get_jwt()
            except Exception:
                user = None

            try:
                payload = request.get_json() if request.is_json else request.args.to_dict()
            except Exception:
                payload = None

            result = func(*args, **kwargs)

            try:
                # Only persist a JSON-serializable summary (avoid storing huge objects)
                rec = AuditLog(
                    endpoint=endpoint_name or request.path,
                    user_id=str(user) if user else None,
                    payload=payload,
                    result=result if isinstance(result, dict) else None,
                )
                db.session.add(rec)
                db.session.commit()
            except Exception:
                db.session.rollback()
                current_app.logger.exception("Failed to write audit log")

            return result
        return wrapper
    return decorator
