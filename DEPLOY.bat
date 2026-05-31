@echo off
REM Deploy SEO AI Agent to Railway + Netlify
REM Usage: Run this file and follow the prompts

echo.
echo ╔════════════════════════════════════════════════════════════════╗
echo ║     SEO AI Agent - Auto Deployment to Railway + Netlify         ║
echo ╚════════════════════════════════════════════════════════════════╝
echo.

REM Step 1: Get GitHub Username
set /p GITHUB_USERNAME="Enter your GitHub username: "
set /p GITHUB_REPO_URL="Enter GitHub HTTPS URL (or press Enter to create new): "

if "%GITHUB_REPO_URL%"=="" (
    set GITHUB_REPO_URL=https://github.com/%GITHUB_USERNAME%/seo-ai-agent.git
    echo Creating new repo URL: %GITHUB_REPO_URL%
)

REM Step 2: Update git remote
echo.
echo [Step 1/4] Updating Git Remote...
git remote remove origin
git remote add origin %GITHUB_REPO_URL%
git branch -M main

REM Step 3: Push to GitHub
echo.
echo [Step 2/4] Pushing to GitHub...
echo You'll need to authenticate with GitHub...
git push -u origin main --force

if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Git push failed!
    echo Make sure your GitHub repo exists and you have push access.
    pause
    exit /b 1
)

REM Step 4: Display Railway instructions
echo.
echo ╔════════════════════════════════════════════════════════════════╗
echo ║                    STEP 3/4: DEPLOY TO RAILWAY                 ║
echo ╚════════════════════════════════════════════════════════════════╝
echo.
echo 1. Open: https://railway.app/new/github
echo 2. Click "Connect to GitHub" and authorize
echo 3. Select repository: seo-ai-agent
echo 4. Click "Deploy Now"
echo.
echo [WAIT for Railway deployment to complete - ~3 minutes]
echo.
echo 5. After deployment, go to your Railway project settings
echo 6. Add Environment Variables:
echo    - ANTHROPIC_API_KEY = (from console.anthropic.com)
echo    - SECRET_KEY = use-any-random-string-here
echo.
echo 7. Copy your Railway URL (it will be like https://xxxx.railway.app)
echo.

pause
set /p RAILWAY_URL="Paste your Railway URL here: "

REM Step 5: Update Netlify env
echo.
echo ╔════════════════════════════════════════════════════════════════╗
echo ║                    STEP 4/4: DEPLOY TO NETLIFY                 ║
echo ╚════════════════════════════════════════════════════════════════╝
echo.
echo 1. Open: https://app.netlify.com/start
echo 2. Click "Connect to GitHub"
echo 3. Select repository: seo-ai-agent
echo 4. Build settings:
echo    - Base directory: frontend
echo    - Build command: npm run build
echo    - Publish directory: frontend/.next
echo.
echo 5. Click "Deploy"
echo.
echo 6. After Netlify deployment, go to Site Settings -> Environment
echo 7. Add variable: NEXT_PUBLIC_API_URL = %RAILWAY_URL%
echo.
echo 8. Trigger redeploy from Netlify Dashboard
echo.

echo.
echo ╔════════════════════════════════════════════════════════════════╗
echo ║                    ✅ DEPLOYMENT COMPLETE!                     ║
echo ╚════════════════════════════════════════════════════════════════╝
echo.
echo Your SEO AI Agent is now LIVE!
echo.
pause
