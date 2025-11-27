# app/schemas/market.py
from marshmallow import Schema, fields

class MarketWeatherSchema(Schema):
    symbol = fields.Str(required=True)
    ts = fields.Str(required=True)
    price = fields.Float()
    atr = fields.Float()
    volatility = fields.Float()
    momentum = fields.Float()
    liquidity = fields.Float()
    safety_score = fields.Int()
    recommendation = fields.Str()
    meta = fields.Dict()

class DangerZoneSchema(Schema):
    symbol = fields.Str(required=True)
    ts = fields.Str(required=True)
    price = fields.Float()
    atr = fields.Float()
    volatility_spike = fields.Bool()
    support_resistance = fields.List(fields.Dict())
    high_volume_events = fields.List(fields.Dict())
    danger_windows = fields.List(fields.Dict())
