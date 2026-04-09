# Tawafuq (توافق)

This is a premium marriage matching platform project.

## Project Structure
- `index.html`: Main landing page.
- `style.css`: Modern glassmorphic styles.
- `app.js`: Interactive frontend logic.
- `assets/`: Contains the logo and hero image.

## النشر (Deployment)
1. ارفع الكود إلى GitHub.
2. اذهب إلى `Settings` > `Pages`.
3. اختر `GitHub Actions` كمصدر للنشر (Source).
4. سيعمل ملف `.github/workflows/static.yml` الذي أعددته لك على نشر الموقع تلقائياً.

## نظام الدردشة (Firebase Setup)
1. أنشئ مشروعاً في [Firebase Console](https://console.firebase.google.com/).
2. فعل `Authentication` (Email/Password).
3. فعل `Realtime Database`.
4. انسخ إعدادات الـ Config وضعها في ملف `config.js`.
