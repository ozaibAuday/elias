# استخدم صورة Python الرسمية
FROM python:3.12-slim

# تعيين مجلد العمل داخل الحاوية
WORKDIR /app

# نسخ ملف المتطلبات وتثبيتها
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# نسخ باقي ملفات المشروع
COPY . .

# تعيين متغير البيئة لملف config.env
ENV DOTENV_PATH=config.env

# الأمر لتشغيل البوت
CMD ["python", "main.py"]
