# CareerPulse

منصة ذكية لمطابقة السير الذاتية بالوظائف باستخدام الذكاء الاصطناعي (NLP + Embeddings + XAI).

## هيكل المشروع

```
CareerPulse/
│
├── mobile/flutter_app/     # تطبيق الموبايل بـ Flutter
├── backend/                # واجهة API خلفية بـ FastAPI
│   └── app/
│       ├── api/            # الـ endpoints
│       ├── services/       # منطق الأعمال
│       ├── models/         # نماذج قاعدة البيانات (ORM)
│       ├── schemas/        # Pydantic schemas
│       └── database/       # اتصال وإعدادات قاعدة البيانات
│
├── ml/                      # كود الذكاء الاصطناعي
│   ├── ner/                 # استخراج الكيانات المسماة
│   ├── embeddings/          # تمثيلات النصوص
│   ├── matching/            # خوارزميات المطابقة
│   ├── xai/                 # الذكاء الاصطناعي القابل للتفسير
│   └── what_if/             # تحليل سيناريوهات "ماذا لو"
│
├── data/                    # بيانات المشروع (raw/processed/jobs/resumes)
├── notebooks/                # Jupyter notebooks للتجارب
├── models/                   # نماذج مدربة محفوظة
├── scripts/                  # سكربتات مساعدة
├── tests/                    # اختبارات المشروع
├── docker/                   # ملفات Docker
└── README.md
```

## تشغيل الباك اند

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## تشغيل تطبيق فلاتر

```bash
cd mobile/flutter_app
flutter pub get
flutter run
```

## تشغيل عبر Docker

```bash
cd docker
docker-compose up --build
```
