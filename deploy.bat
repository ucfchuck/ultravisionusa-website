@echo off
echo Adding GitHub remote...
git remote add origin https://github.com/ucfchuck/ultravisionusa-website.git

echo Pushing to GitHub...
git push -u origin master

echo.
echo Done! Site will be live at:
echo https://ucfchuck.github.io/ultravisionusa-website
echo.
echo Enable GitHub Pages:
echo 1. Go to https://github.com/ucfchuck/ultravisionusa-website/settings/pages
echo 2. Source: Deploy from branch
echo 3. Branch: master
echo 4. Folder: / (root)
echo 5. Save
pause
