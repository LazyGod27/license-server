from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from . import db
import json


class License(db.Model):
    __tablename__ = 'licenses'
    
    id = db.Column(db.Integer, primary_key=True)
    license_key = db.Column(db.String(100), unique=True, nullable=False, index=True)
    product_id = db.Column(db.String(50), nullable=False)
    max_activations = db.Column(db.Integer, default=1)
    expires_at = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    license_metadata = db.Column(db.Text, default='{}')
    username = db.Column(db.String(50), nullable=True)
    
    activations = db.relationship('Activation', backref='license', lazy='dynamic')

class Activation(db.Model):
    __tablename__ = 'activations'
    
    id = db.Column(db.Integer, primary_key=True)
    license_id = db.Column(db.Integer, db.ForeignKey('licenses.id'), nullable=False)
    hardware_id = db.Column(db.String(256), nullable=False, index=True)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(256))
    activated_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    is_revoked = db.Column(db.Boolean, default=False)

class AuditLog(db.Model):
    __tablename__ = 'audit_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    action = db.Column(db.String(50), nullable=False)
    license_key = db.Column(db.String(100))
    hardware_id = db.Column(db.String(256))
    ip_address = db.Column(db.String(45))
    success = db.Column(db.Boolean)
    details = db.Column(db.Text)