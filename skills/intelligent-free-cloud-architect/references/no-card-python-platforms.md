# أفضل 3 خيارات بلا بطاقة: Python + بيانات دائمة

> **تاريخ تحقق المعايير:** أغسطس 2026. «بلا بطاقة» لا يعني مناسباً لتشغيل 24/7 أو مناسباً لكل تطبيق Python. افحص دائماً حدود الذاكرة والنوم ونوع قاعدة البيانات قبل الاختيار.

## الترتيب

| الترتيب | البنية | لماذا تدخل القائمة | الحد الحاسم | ملاءمة tozyw |
|---:|---|---|---|---:|
| 1 | **Cloudflare Workers (Python Beta) + D1 + R2** | Python Workers وD1 (SQL بدلالة SQLite) وR2 تعمل في طبقة واحدة، وتوجد خطة مجانية بلا بطاقة. | Workers Free يحد CPU إلى 10ms لكل طلب؛ ليست بيئة Pandas/Selenium/Streamlit طويلة. | لا كتشغيل حالي؛ نعم إذا أُعيد بناء API خفيف لاحقاً. |
| 2 | **Render Free + Neon Free Postgres** | Render يدعم Python وDocker والنشر من Git بلا بطاقة؛ Neon Free قاعدة Postgres دائمة بلا بطاقة. | Render 512MB/0.1 vCPU وينام بعد 15 دقيقة؛ القرص محلي مؤقت. | لا للتطبيق كاملاً؛ جيد لنموذج Python صغير عديم الحالة. |
| 3 | **Vercel Hobby + Neon Free Postgres** | Vercel يدعم Python Functions، والنشر Git-native؛ Neon يوفر DB دائمة بلا بطاقة. | functions serverless وليست عملية طويلة/قرصاً محلياً؛ Hobby شخصي غير تجاري. | لا للمشروع التجاري/التحليلي الحالي؛ جيد API خفيف أو admin صغير. |

## لماذا ليست Oracle في هذه القائمة؟

Oracle Always Free هو الأفضل مواردياً لـtozyw عند الحصول عليه، لكنه يطلب بطاقة للتحقق. لا تعرضه كإجابة على شرط «بلا بطاقة»، بل كخيار منفصل: **مجاني ضمن حد مع تحقق بطاقة**.

## لماذا استُبعد Koyeb وPythonAnywhere؟

Koyeb يوضح رسمياً أن الحساب يتطلب بطاقة للتحقق، لذا يستبعد مباشرة من شرط المستخدم حتى مع وجود web service مجانية. PythonAnywhere لديه حساب مجاني بملفات خاصة، لكنه لا يثبت في صفحة تسعيره شرط «بلا بطاقة» بصورة كافية، وخطته المجانية لا تحتوي always-on أو scheduled tasks ولها outbound Internet مقيد؛ صنّفه خيار تجربة فقط بعد تحقق signup المباشر.

## شروط الاختيار

### 1. Cloudflare Workers + D1 + R2

استخدمه عندما تكون العملية HTTP قصيرة وعديمة الحالة وتقبل قيود Workers، أو عند نقل أجزاء صغيرة من التطبيق إلى API. D1 خدمة مُدارة بمظهر SQL متوافق مع SQLite، لكنه ليس ملف SQLite تفتحه مكتبة `sqlite3` مباشرة. يجب أن تكتب طبقة وصول داعمة لواجهة Workers/D1.

- Python Workers ما زال Beta.
- D1 Free: 5GB تخزين إجمالي، 5M rows read/day، 100K rows written/day.
- Workers Free: 100K requests/day و10ms CPU لكل invocation.
- لا تضع pandas، Chrome، Selenium، أو تحليل طويل داخل Worker.

### 2. Render Free + Neon Free

استخدمه لتجربة Python web صغيرة، مع إبقاء البيانات في Neon عبر اتصال Postgres بدلاً من filesystem Render المؤقت.

- Render Free يدعم Python/Docker والنشر من Git بلا بطاقة.
- ينام بعد 15 دقيقة خمول، يمنح 512MB و0.1 vCPU، ويملك 750 ساعة instance شهرياً؛ لذلك لا يصلح للـjobs أو SQLite محلي.
- Neon Free دائم وبلا بطاقة: 0.5GB تخزين/project، 100 CU-hours/project، autoscaling حتى 8GB، ويصغّر compute بعد 5 دقائق.
- لا تعتمد على Render Free Postgres بدلاً من Neon؛ قاعدة Render المجانية تنتهي بعد 30 يوماً.

### 3. Vercel Hobby + Neon Free

استخدمه لواجهة أو API Python قصير يتصل بـNeon. لا تستخدمه لخادم Streamlit أو عمال background أو عمليات scraping.

- Vercel يوفر Python Functions؛ حد حجم حزمة Python غير المضغوطة 500MB.
- Hobby مجاني للاستخدام الشخصي غير التجاري فقط؛ راجع الشروط قبل استخدام مشروع متجر/عمل.
- لا توجد ديمومة filesystem؛ ضع البيانات في Neon أو R2، لا SQLite محلي.
- الاستعلامات والعمليات القصيرة فقط؛ لا تنقل محرك tozyw كما هو.

## بديل أخف دون خادم Python

إذا كان المطلوب تخزين حالة صغيرة أو إعدادات فقط، استخدم **Cloudflare D1** أو **Neon** من دون خدمة Python دائمة. لا تقترح هذا بديلاً لتطبيق يحتاج Streamlit/Pandas/Selenium.

## المصادر الرسمية

- Cloudflare Python Workers: https://developers.cloudflare.com/workers/languages/python/
- Cloudflare Workers/D1 pricing: https://developers.cloudflare.com/workers/platform/pricing/
- Cloudflare D1: https://www.cloudflare.com/products/d1/
- Render Free limits: https://render.com/docs/free
- Render free-tier comparison and no-card statement: https://render.com/articles/platforms-with-a-real-free-tier-for-developers-in-2026
- Neon pricing: https://neon.com/pricing
- Vercel Python runtime: https://vercel.com/docs/functions/runtimes/python
- Vercel Hobby: https://vercel.com/docs/plans/hobby
- Koyeb card requirement: https://www.koyeb.com/docs/faqs/pricing
- PythonAnywhere pricing: https://www.pythonanywhere.com/pricing/
