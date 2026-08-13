# دليل مشروع tozyw: Oracle + GitHub + SQLite

## ملف عبء العمل

- التطبيق Python/Streamlit ويشغَّل عبر `streamlit run app.py`، مع `Procfile` يستخدم `$PORT` و`0.0.0.0`.
- يعتمد على SQLite مع WAL وملفات حالة ضمن `data/`، ومنها قواعد منافسين ولقطات `ui_session/`.
- ينفذ تحليلاً بـPandas وNumPy، وتوثيق المستودع يشير إلى ذروة عملية تقارب 1.1GB. لا تقترح tier بذاكرة 512MB للتشغيل الأساسي.
- يملك عمليات تحليل وجدولة؛ والكشط الاختياري يحتاج Selenium ومتصفحاً على الخادم. افترض الحاجة إلى Ubuntu/Docker أو صلاحيات نظام مناسبة.
- الأسرار المحتملة: OpenRouter وMake وSalla وSupabase وGoogle CSE. لا تدخل أي منها إلى Git.
- المستودع `mahwoussa-boop/tozyw` كان مؤرشفاً أثناء الفحص. تحقق من حالته قبل إعداد CI/CD؛ المستودع المؤرشف read-only ولا يقبل ملفات workflow أو commits جديدة.

## المعمارية الافتراضية

```text
GitHub private، غير مؤرشف
       │  push إلى main بعد مرور الاختبارات
       ▼
GitHub Actions: build/test ثم SSH محدود الصلاحية
       ▼
OCI A1 — Ubuntu ARM64
  /opt/tozyw/release         ← كود الإصدار
  /srv/tozyw/data            ← volume مستقل ودائم
       ├─ pricing_v18.db
       ├─ perfume_pricing.db
       └─ ui_session/
       │
       ├─ تطبيق Streamlit: كاتب واحد فقط لكل SQLite
       ├─ Litestream: replication مضبوط الوتيرة إلى R2
       └─ cron/systemd timer: نسخة SQLite متسقة مشفرة إلى B2
```

استخدم OCI A1 فقط إذا كان المستخدم يقبل متطلب التحقق بالبطاقة. لا تصفه كحل «بلا بطاقة». خصص أقل موارد لازمة داخل حد Always Free، وأنشئ Block Volume أو boot volume كافياً لمسار البيانات. لا تعتمد على توفر سعة A1 من المرة الأولى؛ افحص المنطقة وAvailability Domain.

## ترتيب الإعداد الآمن

1. **تثبيت المستودع.** أنشئ/انقل إلى مستودع خاص غير مؤرشف. فعّل الحماية للفرع `main` بحيث يمر الاختبار قبل الدمج.
2. **إعداد OCI يدوي مرة واحدة بعد موافقة المستخدم.** أنشئ VM Always Free في المنطقة المنزلية، مستخدماً Ubuntu ARM64. أضف مفتاح SSH خاص بالنشر واسمح للمنفذ الضروري فقط. لا تفتح Streamlit مباشرة للعامة.
3. **إعداد الخادم.** أنشئ مستخدم `deployer` بلا صلاحية root تفاعلية، وأعطه `sudo` مقيداً فقط لسكربت release محدد. ضع الكود في `/opt/tozyw/release` والبيانات في `/srv/tozyw/data`.
4. **افصل الإصدار عن البيانات.** لا تستبدل أو تمسح `/srv/tozyw/data` داخل deploy. لا تُدرج قواعد الإنتاج في image أو Git.
5. **أضف أسرار GitHub بعد موافقة صريحة.** استخدم `OCI_HOST` و`OCI_DEPLOY_USER` و`OCI_SSH_PRIVATE_KEY` و`OCI_SSH_KNOWN_HOSTS`. تحفظ مفاتيح التطبيق في الخادم/أداة النشر، لا في workflow إذا لم تكن مطلوبة للبناء.
6. **شغّل النشر على push.** ينفذ workflow الاختبارات ثم يستدعي سكربت release محدوداً. يجب أن يتوقف النشر إن فشل اختبار أو health check؛ لا يقبل fallback صامتاً.
7. **فعّل النسخ.** استخدم Litestream لنسخ قواعد SQLite إلى bucket R2 مضبوط بمفاتيح محدودة، ونسخة يومية متسقة إلى B2 مستقل. اختبر restore شهرياً.
8. **اختر الوصول الخاص.** استخدم شبكة خاصة/بوابة هوية للفريق الداخلي. افحص إعدادات CORS/XSRF في Streamlit قبل أي وصول عام.

## قواعد النشر idempotent

يجب أن ينفذ سكربت النشر التسلسل التالي:

1. قفل deployment يمنع تشغيل إصدارين معاً.
2. استنساخ أو checkout لـSHA المحدد في مجلد release جديد.
3. تثبيت/بناء الاعتمادات ونجاح الاختبارات.
4. فحص أن data volume حاضر وقابل للكتابة، من دون تعديله.
5. تحويل خدمة التطبيق إلى الإصدار الجديد وإجراء health check محلي.
6. الرجوع إلى الإصدار الأخير إن فشل health check.
7. كتابة SHA ووقت النشر إلى سجل محلي لا يحوي أسراراً.

لا تشغّل ترحيلاً destructively على SQLite داخل كل deploy. اجعل أي migration صريحاً، قابلاً للنسخ والرجوع، وموافَقاً عليه عند الحاجة.

## النسخ والاستعادة

| الطبقة | الآلية | RPO مستهدف | ملاحظة |
|---|---|---:|---|
| تشغيل | `/srv/tozyw/data` على قرص دائم | 0 | ليست نسخة احتياطية. |
| قريب | Litestream إلى R2 | 5 دقائق | اضبط `sync-interval` لتحت حدود العمليات المجانية. |
| مستقل | SQLite Backup API ثم ضغط وتشفير إلى B2 | 24 ساعة | احتفظ بسجل احتفاظ منفصل؛ لا تعط مفتاح الرفع حذف الأرشيف. |
| اختبار | restore إلى ملف/خادم مؤقت + فحوص جداول | شهرياً | لا قيمة لنسخة لم تُستعد. |

قبل رفع قواعد إلى R2/B2، افحص حجم البيانات الفعلي وعدد القواعد. اترك 20%–30% هامشاً تحت quota التخزين والعمليات. لا تحسب النسخ المتماثل كنسخة ذات retention؛ حذف أو فساد القاعدة قد يُنسخ، ولهذا تبقى النسخ اليومية المؤرخة ضرورية.

## الأتمتة عبر المتصفح: حد الموافقة

يمكن تنفيذ الاستكشاف، التحقق من المستودع، إعداد الملفات محلياً، ومراقبة حالة النشر تلقائياً. يحتاج موافقة المستخدم قبل تنفيذ أي من الآتي في المتصفح:

- إنشاء حساب أو قبول شروط خدمة، وإدخال أي معلومات شخصية أو بطاقة.
- تثبيت GitHub App أو منح OAuth صلاحية إلى المستودعات.
- إنشاء/إضافة/تغيير سر أو مفتاح أو متغير بيئة.
- إلغاء أرشفة المستودع، جعل المستودع خاصاً، أو push إلى GitHub.
- إنشاء VM أو bucket أو Firewall rule أو نشر عنوان عام.

بعد bootstrap المقبول، لا يحتاج النشر اليومي إلى تدخل: push إلى `main` يشغل الاختبارات والنشر، وtimer الخادم يشغل النسخ والاختبار الدوري للاستعادة. لا تستخدم متصفحاً أو حساباً بشرياً كـcron؛ استخدم GitHub events وsystemd timers/webhooks الموثقة.

## تعريف نجاح عملية التطوير

- commit جديد على `main` يمر بالاختبارات وينشر SHA نفسه فقط.
- restart أو deploy لا يحذف بيانات `data/`.
- حذف تجريبي لنسخة محلية في بيئة استعادة يعيد القاعدة من R2.
- الاستعادة من B2 تعطي قاعدة يمكن فتحها والتحقق منها.
- أسرار GitHub لا تظهر في السجلات، ولا يصل deployer إلا لأمر release المطلوب.
- لا يصل التطبيق الداخلي إلا مستخدم مصرح له.

## المصادر التي يجب إعادة التحقق منها

- OCI Always Free: https://docs.oracle.com/iaas/Content/FreeTier/freetier_topic-Always_Free_Resources.htm
- OCI Free Tier: https://www.oracle.com/cloud/free/
- Litestream إلى S3-compatible: https://litestream.io/guides/s3-compatible/
- Litestream config: https://litestream.io/reference/config/
- Cloudflare R2 pricing: https://developers.cloudflare.com/r2/pricing/
- Backblaze B2 pricing: https://www.backblaze.com/cloud-storage/pricing
- GitHub Action events: https://docs.github.com/actions/using-workflows/events-that-trigger-workflows
- GitHub Actions secrets: https://docs.github.com/actions/security-guides/using-secrets-in-github-actions
- GitHub archive: https://docs.github.com/en/repositories/archiving-a-github-repository/archiving-repositories
