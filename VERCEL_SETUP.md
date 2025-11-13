# Vercel Environment Variables Setup

## Required Environment Variable for Railway Database

Add this environment variable in your Vercel project:

### Variable Name:
```
DATABASE_URL
```

### Variable Value:
```
postgresql://postgres:yrGjdFRaNNLUvzLwCxrTivOFGBpKKWoJ@ballast.proxy.rlwy.net:22903/railway
```

## Steps to Add in Vercel:

1. Go to your Vercel project dashboard
2. Click on **Settings** → **Environment Variables**
3. Click **Add New**
4. Enter:
   - **Key**: `DATABASE_URL`
   - **Value**: `postgresql://postgres:yrGjdFRaNNLUvzLwCxrTivOFGBpKKWoJ@ballast.proxy.rlwy.net:22903/railway`
   - **Environment**: Select **Production**, **Preview**, and **Development** (or at least **Production**)
5. Click **Save**
6. **Redeploy** your project for the changes to take effect

## Verification:

After deployment, check your Vercel function logs. You should see:
```
✅ Database connected - Using PostgreSQL
```

If you see:
```
⚠️  Database connection failed: ...
```

Then check:
- The DATABASE_URL is correctly set in Vercel
- Railway database is running and accessible
- The password is correct

## Railway Database Details:

- **Host**: `ballast.proxy.rlwy.net`
- **Port**: `22903`
- **Database**: `railway`
- **User**: `postgres`
- **Password**: `yrGjdFRaNNLUvzLwCxrTivOFGBpKKWoJ`

