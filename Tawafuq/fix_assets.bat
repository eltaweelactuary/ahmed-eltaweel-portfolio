@echo off
echo [1/3] Creating assets folder...
if not exist assets mkdir assets
echo [2/3] Copying images...
copy "C:\Users\Ahmed\.gemini\antigravity\brain\39cb00ea-89a8-4ccd-84f1-118bd959a658\tawafuq_logo_1774545072777.png" "assets\logo.png"
copy "C:\Users\Ahmed\.gemini\antigravity\brain\39cb00ea-89a8-4ccd-84f1-118bd959a658\tawafuq_hero_image_1774545055077.png" "assets\hero.png"
echo [3/3] Done! Updating Git...
git add assets/
git commit -m "Fix: Add missing logo and hero images"
git push origin main
echo.
echo Process complete! Website should be fixed in a minute.
pause
