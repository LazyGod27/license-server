# Railway to Render Migration Guide

## 🚀 Quick Migration Steps

### 1. Set Up Render Services
1. Create account at [render.com](https://render.com)
2. Create Web Service: `license-server`
3. Create Redis Service: `license-redis`

### 2. Web Service Configuration
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `gunicorn --bind 0.0.0.0:$PORT --workers 1 run:app`
- **Health Check Path**: `/`

### 3. Environment Variables
Set these in your Render Web Service:

```
DATABASE_URL=your_render_postgres_url
REDIS_URL=your_render_redis_url
FLASK_ENV=production
JWT_SECRET=your_jwt_secret_key
ADMIN_API_KEY=your_admin_api_key
```

### 4. Database Migration
1. **Export from Railway:**
   ```bash
   # Connect to Railway PostgreSQL and export data
   pg_dump -h your-railway-host -U your-user your-db > railway_data.sql
   ```

2. **Import to Render:**
   ```bash
   # Connect to Render PostgreSQL and import data
   psql -h your-render-host -U your-user your-db < railway_data.sql
   ```

### 5. URL Changes
- **Old**: `your-app.railway.app/admin`
- **New**: `your-app.onrender.com/admin`

### 6. Test Everything
1. ✅ Admin login works
2. ✅ License generation works  
3. ✅ Redis brute force protection active
4. ✅ All API endpoints functioning

## 🔧 Key Differences

| Feature | Railway | Render |
|---------|---------|--------|
| Free Tier Hours | 500 hours/month | 750 hours/month |
| Redis URL | `redis://default:pass@redis.railway.internal:6379` | `redis://user:pass@host:port` |
| Environment | Railway-specific | Standard Docker |
| Port Binding | Railway handles it | Use `$PORT` variable |

## 🎯 Benefits of Render
- ✅ More free hours (750 vs 500)
- ✅ Better free Redis (persistent)
- ✅ Standard environment (easier debugging)
- ✅ Better performance
- ✅ More reliable

## 🚨 Important Notes
- Update any hardcoded URLs in your code
- Test admin panel thoroughly after migration
- Monitor logs for any Redis connection issues
- Keep Railway backup until Render is fully working
