@echo off
echo Installing Tailwind CSS and required dependencies...
cd /d "c:\Users\moksh\CascadeProjects\brain\frontend"

echo Installing Tailwind CSS...
npm install -D tailwindcss postcss autoprefixer

echo Installing Tailwind CSS plugins...
npm install -D @tailwindcss/forms @tailwindcss/typography

echo Tailwind CSS installation complete!
echo.
echo Now restart the development server:
echo cd frontend
echo npm run dev
pause
