@echo off
echo ========================================
echo    Deploying Tawafuq to GitHub
echo ========================================
cd /d "C:\Users\Ahmed\OneDrive\Tawafuq"

git add .
git commit -m "update: Tawafuq platform"
git branch -M main

echo Pushing to GitHub... (a login window may appear)
git push -u origin main

echo.
echo ========================================
echo    DONE! Tawafuq deployed!
echo ========================================
pause
