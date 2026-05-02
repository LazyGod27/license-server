# Manual License Creation Guide

## Problem: Failed to Create/Load Licenses

This happens when your new database is empty and doesn't have the required tables. Follow these steps to fix it.

## Step 1: Initialize Database Schema

First, you need to create the database tables:

```bash
# Navigate to your license-server directory
cd C:\Users\Ace\Desktop\license-server

# Activate virtual environment (if you have one)
venv\Scripts\activate

# Initialize database tables
python init_db.py
```

This will:
- Test database connection
- Create all required tables (licenses, activations, audit_logs)
- Show confirmation when complete

## Step 2: Generate Licenses Manually

After database initialization, you can generate licenses using command prompt:

### Basic Usage:
```bash
# Generate 10 default licenses
python generate_licenses.py

# Generate specific number of licenses
python generate_licenses.py 25

# Generate licenses for specific product
python generate_licenses.py 10 GREED-TOOL
python generate_licenses.py 10 MAXGreed
```

### Examples:
```bash
# Generate 5 GreedTool licenses
python generate_licenses.py 5 GREED-TOOL

# Generate 20 MaxGreed licenses  
python generate_licenses.py 20 MAXGreed

# Generate 50 licenses for MAXGreed (premium version)
python generate_licenses.py 50 MAXGreed
```

## Step 3: Check Generated Licenses

The script will show you the first 5 licenses generated:

```
📋 Sample licenses (first 5):
--------------------------------------------------
1. GREED-A1B2-C3D4-E5F6-G7H8
   Product: GREED-TOOL
   Expires: 2026-05-02

2. GREED-I9J8-K7L6-M5N4-O3P2
   Product: GREED-TOOL  
   Expires: 2026-05-02
```

## Product Types

### GREED-TOOL (Standard):
- License format: `GREED-XXXX-XXXX-XXXX-XXXX`
- Features: arena_reset, lobby
- Max activations: 1
- Valid for: 365 days

### MAXGreed (Premium):
- License format: `MAXG-XXXX-XXXX-XXXX-XXXX`
- Features: arena_reset, lobby, unlimited_activations
- Max activations: 5
- Valid for: 365 days

## Troubleshooting

### If init_db.py fails:
```bash
# Check database connection
python -c "from app import create_app; app = create_app(); print('DB OK' if app else 'DB Failed')"

# Check environment variables
echo %DATABASE_URL%
```

### If generate_licenses.py fails:
1. Make sure you ran `init_db.py` first
2. Check that DATABASE_URL is set correctly
3. Verify database connection

### Common Errors:
- "Failed to create licenses" → Database tables don't exist → Run `init_db.py`
- "Failed to load licenses" → Database is empty → Run `generate_licenses.py`
- "Database connection failed" → Wrong DATABASE_URL → Check environment variable

## Quick Start Commands

```bash
# 1. Go to project directory
cd C:\Users\Ace\Desktop\license-server

# 2. Activate virtual environment
venv\Scripts\activate

# 3. Initialize database
python init_db.py

# 4. Generate licenses
python generate_licenses.py 10 GREED-TOOL

# 5. Generate premium licenses
python generate_licenses.py 5 MAXGreed
```

## Environment Setup

If you don't have a virtual environment:

```bash
# Create virtual environment
python -m venv venv

# Activate it
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Database URL Format

Make sure your DATABASE_URL is set correctly:
```
postgresql://license_db_new_ntwx_user:zuDku3V3lGGsWFPJyXVYEbKcSbOV2TBL@dpg-d7qshavavr4c73f5nsdg-a/license_db_new_ntwx
```

## License Features

### Standard (GREED-TOOL):
- Arena reset functionality
- Lobby access
- 1 device activation

### Premium (MAXGreed):
- All standard features
- Unlimited device activations
- Priority support features
