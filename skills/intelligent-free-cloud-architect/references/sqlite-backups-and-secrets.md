# SQLite: النسخ المشفر وحماية الأسرار

## قرار وجهة النسخ

| الوجهة | الحكم | متى تستخدمها | القيد الحاسم |
|---|---|---|---|
| Google Drive عبر `rclone crypt` | **الخيار المفضل لنسخة خارجية مجانية** | خادم دائم يملك ملف SQLite ويستطيع تشغيل timer. | يحتاج OAuth/حساب Google مرة واحدة؛ يجب حفظ إعداد rclone وكلمة مروره كأسرار. |
| مستودع GitHub خاص + Release assets مشفرة بـ`age` | **نسخة ثانية اختيارية** | أرشيفات قليلة وصغيرة واحتياج استعادة مستقلة. | Releases ليست خدمة backup مخصصة؛ افصلها في مستودع خاص ولا ترفع شيئاً غير مشفر. |
| GitHub Actions artifacts | **لا تستخدمه كنسخة احتياطية رئيسية** | اختبار أو artifact عابر فقط. | له سياسة احتفاظ ولا يصل إلى SQLite الحية على خادم منفصل. |
| Render Free filesystem | **مرفوض كمصدر SQLite** | لا شيء سوى نموذج عديم الحالة. | الملفات محلية مؤقتة والخدمة تنام؛ لا يمكن ضمان النسخ من قاعدة حية. |

لا يشغّل GitHub Actions أو Render Free النسخة الاحتياطية لقاعدة `tozyw` ما لم تكن القاعدة متاحة لهما فعلاً. شغّل النسخ على **نفس الخادم أو volume** الذي يملك `data/`، بعد أخذ لقطة متسقة عبر SQLite Backup API.

## Google Drive: التصميم الصحيح

1. أنشئ remote مخصصاً في rclone بنطاق `drive.file` أو مجلد/Shared Drive مخصص للنسخ؛ لا تمنح الوصول الكامل إلى كل Drive إن لم يكن ضرورياً.
2. أنشئ remote من نوع `crypt` يلتف حول مسار منفصل في Drive. استخدم تشفير اسم الملف والمجلد الافتراضيين.
3. فعّل تشفير إعداد rclone نفسه. إن بقي ملف `rclone.conf` أو كلمة مروره مكشوفين، يمكن استعادة كل الملفات المشفرة.
4. خزّن `rclone.conf` و`RCLONE_CONFIG_PASS` في مدير أسرار الخادم، لا في Git ولا في `.env` دائم في home directory.
5. شغّل `rclone copy` لا `sync` لنسخ أرشيفات مؤرخة؛ لا تحذف النسخ البعيدة من عملية النسخ اليومية. طبق سياسة retention مستقلة ومراجعة.
6. اختبر شهرياً: نزّل أرشيفاً، تحقق من SHA-256، فك التشفير، ثم افتح SQLite وفحص سريع للجداول.

> إعداد Drive الأول يحتاج موافقة المستخدم في المتصفح؛ وثائق rclone تذكر أن إعداد Google Drive يحصل على token عبر المتصفح. بعد ذلك لا تحتاج العملية اليومية إلى متصفح.

## GitHub: النسخة الثانية لا المصدر الوحيد

استخدم مستودعاً **خاصاً منفصلاً** باسم واضح للنسخ. أرشف `tar.gz` بعد لقطة SQLite متسقة، ثم شفّره بـ`age` باستخدام public recipient قبل أي رفع. خزّن مفتاح فك التشفير خارج GitHub، مثل مدير كلمات مرور أو Vault.

يقبل GitHub Release حتى 1000 asset لكل release، وبحد 2GiB للملف الواحد. هذا يجعلها مناسبة لأرشيفات مشفرة محدودة الحجم، وليس لنسخ لا نهائية أو قواعد تتجاوز الحد. لا ترفع قاعدة `.db` أو ملف `.env` أو إعداد rclone بصيغتها الصريحة.

## Always Free: نمط الأسرار الأفضل

استخدم طبقات منفصلة:

| الطبقة | ما يوضع فيها | القاعدة |
|---|---|---|
| OCI Vault | API keys، كلمات مرور، config rclone، مفاتيح tokens | أنشئ secret مستقلاً لكل قيمة؛ شفره بمفتاح Vault وأعط VM هوية instance لا مفتاحاً طويلاً. |
| GitHub Environment `production` | deploy hook أو أسرار CI الضرورية فقط | احمِ البيئة والفرع، واقصر الإتاحة على `main`. |
| Render Environment | `DATABASE_URL` وأسرار runtime | لا تضع القيمة في `render.yaml`؛ استعمل `sync: false` أو لوحة الأسرار. |
| خادم التطبيق | نسخة زمنية مؤقتة في ملف بصلاحية `0600` عند الحاجة | لا تسجلها، وامسح الملف المؤقت بعد المهمة. |

استخدم OIDC بين GitHub Actions والسحابة عند وجود إعداد موثق للمزود؛ يخفض الحاجة إلى credentials طويلة العمر. لا تحول هذه التوصية إلى تنفيذ قبل تقييد claims بالمستودع والفرع والبيئة. عند عدم توفر OIDC، أنشئ مفتاح deploy منفصلاً، محدود الصلاحية وقابلاً للإبطال، ولا تعطه صلاحية عامة.

## قواعد لا تتغير

- لا تنسخ ملف SQLite خلال الكتابة عبر `cp` عادي؛ استخدم SQLite Backup API أو أداة واعية بـWAL.
- لا تضع قاعدة التشغيل في Git، ولا تسحب بيانات الإنتاج إلى GitHub runner بهدف النسخ.
- لا تخلط replication السريع مع retention. حذف أو فساد المصدر قد يُنسخ، لذلك احتفظ بأرشيفات مؤرخة.
- لا تدّعِ أن Neon بديل مباشر لملف SQLite. يلزم migration طبقة البيانات واختبارات import/rollback قبل جعله مصدر الحقيقة.
- لا تدخل OAuth أو تنشئ Vault أو مفاتيح أو repos خاصة قبل موافقة المستخدم الواضحة.

## مصادر للتحقق المتكرر

- Google Drive uploads: https://developers.google.com/workspace/drive/api/guides/manage-uploads
- rclone Drive: https://rclone.org/drive/
- rclone crypt: https://rclone.org/crypt/
- OCI Always Free / Vault: https://docs.oracle.com/iaas/Content/FreeTier/freetier_topic-Always_Free_Resources.htm
- GitHub Releases: https://docs.github.com/en/repositories/releasing-projects-on-github/about-releases
- GitHub OIDC: https://docs.github.com/actions/security-for-github-actions/security-hardening-your-deployments/configuring-openid-connect-in-cloud-providers
