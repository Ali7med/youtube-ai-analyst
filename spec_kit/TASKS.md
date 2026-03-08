# TASKS.md — YouTube AI Research Agent
> تم توليده تلقائياً بواسطة `/speckit.tasks` بتاريخ 2026-03-08  
> المصدر: `spec_kit/PRD.md` + `spec_kit/SYSTEM_ARCHITECTURE.md` + `spec_kit/API_SPEC.md`

---

## 📊 ملخص المهام

| المرحلة | المهام | الحجم التقديري |
|---------|--------|----------------|
| Phase 1 — Foundation Improvements | 5 مهام | ~3-4 أيام |
| Phase 2 — Advanced Analysis | 5 مهام | ~5-7 أيام |
| Phase 3 — Professional UI | 4 مهام | ~4-6 أيام |
| Phase 4 — Automation & Scheduling | 4 مهام | ~3-5 أيام |
| Phase 5 — Advanced AI | 4 مهام | ~7-10 أيام |
| **الإجمالي** | **22 مهمة** | **~22-32 يوم** |

---

## 🔴 Phase 1 — Foundation Improvements

---

### TASK-01 · قاعدة البيانات المحلية (SQLite)
**الأولوية**: 🔴 Critical  
**الحجم**: M  
**الحالة**: `[x] Done`

#### الملفات المطلوبة
| الإجراء | الملف |
|---------|-------|
| إنشاء | `database/schema.sql` |
| إنشاء | `execution/db_manager.py` |
| تعديل | `pipeline.py` — استدعاء `db_manager.save_video()` بعد كل فيديو |
| تعديل | `app.py` — إضافة `/api/history` و `/api/videos` |

#### المحتوى المطلوب في `schema.sql`
```sql
CREATE TABLE IF NOT EXISTS searches (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  query TEXT NOT NULL,
  order_by TEXT,
  results_count INTEGER,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS videos (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  video_id TEXT UNIQUE NOT NULL,
  search_id INTEGER REFERENCES searches(id),
  title TEXT, summary TEXT, notes TEXT,
  thumbnail TEXT, rate REAL, label TEXT,
  link TEXT, views INTEGER, likes INTEGER,
  comments INTEGER, sentiment TEXT, content_type TEXT,
  topics TEXT, channel_id TEXT, published_at TEXT,
  processed_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS transcripts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  video_id TEXT UNIQUE NOT NULL,
  text TEXT, source TEXT, language TEXT,
  segment_count INTEGER,
  cached_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS jobs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT, query TEXT, schedule TEXT,
  max_results INTEGER DEFAULT 10,
  auto_sheet BOOLEAN DEFAULT 1,
  notify_telegram BOOLEAN DEFAULT 0,
  last_run DATETIME, next_run DATETIME,
  status TEXT DEFAULT 'active',
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

#### معايير القبول
- [x] يمكن تشغيل `db_manager.py` بشكل مستقل دون أخطاء
- [x] بعد أي بحث، تظهر النتائج في قاعدة البيانات
- [x] `GET /api/history` يُرجع قائمة عمليات البحث
- [x] لا تُحذف البيانات عند حذف `.tmp/`

#### التبعيات
- لا شيء (يمكن البدء مباشرة)

---

### TASK-02 · نظام Cache الذكي
**الأولوية**: 🔴 Critical  
**الحجم**: S  
**الحالة**: `[x] Done`

#### الملفات المطلوبة
| الإجراء | الملف |
|---------|-------|
| إنشاء | `execution/cache_manager.py` |
| تعديل | `pipeline.py` — فحص الـ cache قبل معالجة أي فيديو |

#### منطق `cache_manager.py`
```python
def is_cached(video_id: str, ttl_hours: int = 24) -> bool:
    """True إذا كان الفيديو موجوداً في DB وصالحاً خلال TTL"""

def get_cached_video(video_id: str) -> dict | None:
    """يُرجع الفيديو المخزّن إذا كان قيد الصلاحية"""

def get_cached_transcript(video_id: str) -> dict | None:
    """يُرجع الـ transcript المخزّن مباشرة دون استدعاء API"""
```

#### معايير القبول
- [x] الفيديو الذي سبق معالجته لا يُرسل طلبات LLM جديدة
- [x] الـ TTL قابل للتحكم عبر `CACHE_TTL_HOURS` في `.env` (مضبوط كافتراضي)
- [x] يُطبع في logs: `[cache] HIT: {video_id}` أو `[cache] MISS: {video_id}`
- [x] انخفاض ملحوظ في استهلاك YouTube API quota عند إعادة البحث

#### التبعيات
- TASK-01 (يحتاج قاعدة البيانات)

---

### TASK-03 · Live Progress عبر SSE
**الأولوية**: 🔴 Critical  
**الحجم**: M  
**الحالة**: `[x] Done`

#### الملفات المطلوبة
| الإجراء | الملف |
|---------|-------|
| تعديل | `pipeline.py` — تحويله إلى generator يُصدر events |
| تعديل | `app.py` — إضافة `GET /api/search/stream` |
| تعديل | `static/index.html` (أو الصفحة المناسبة) — استهلاك SSE |

#### أشكال الـ Events المطلوبة
```
data: {"type": "start",      "message": "Starting pipeline for 'AI Tools'..."}
data: {"type": "search",     "message": "Found 10 videos", "count": 10}
data: {"type": "processing", "index": 1, "total": 10, "title": "Video Title"}
data: {"type": "cache_hit",  "index": 1, "title": "...", "message": "Loaded from cache"}
data: {"type": "video_done", "index": 1, "rate": 78.5, "label": "⭐ High Performer"}
data: {"type": "error",      "index": 2, "message": "Transcript unavailable, using description"}
data: {"type": "complete",   "processed": 9, "failed": 1, "duration_sec": 47}
```

#### معايير القبول
- [x] الـ UI يُظهر تقدماً حياً لكل فيديو (مُضمن بالمسار `/api/search/stream`)
- [x] يعمل بدون polling — connection واحد مستمر
- [x] الأخطاء تظهر في الـ stream دون إيقاف Pipeline
- [x] بعد `complete` يُعرض ملخص النتائج

#### التبعيات
- لا شيء حرج (يمكن عمله بالتوازي مع TASK-01)

---

### TASK-04 · تحسين نظام التقييم
**الأولوية**: 🟠 High  
**الحجم**: S  
**الحالة**: `[x] Done`

#### الملفات المطلوبة
| الإجراء | الملف |
|---------|-------|
| تعديل | `execution/rate_video.py` — إضافة معايير جديدة |
| تعديل | `execution/search_youtube.py` — جلب `channelSubscriberCount` |

#### المعايير الجديدة للتقييم
```python
NEW_WEIGHTS = {
    "engagement_ratio":   0.25,   # كما هو
    "view_velocity":      0.20,   # كما هو
    "absolute_views":     0.15,   # كما هو
    "sentiment_bonus":    0.10,   # كما هو
    "content_depth":      0.10,   # كما هو
    "channel_authority":  0.10,   # جديد: مشتركون / 1M = 100
    "recency_bonus":      0.10,   # جديد: فيديو < 30 يوم = 100
}
```

#### معايير القبول
- [x] الأوزان الجديدة مجموعها = 1.0
- [x] `channel_authority` يُحسب من `subscriber_count`
- [x] `recency_bonus` يُعطي تفضيلاً للفيديوهات الحديثة
- [x] النتائج القديمة لا تتأثر (backward compatible)

#### التبعيات
- لا شيء

---

### TASK-05 · تحسين LLM Output — Hook + CTA + Extras
**الأولوية**: 🟠 High  
**الحجم**: S  
**الحالة**: `[x] Done`

#### الملفات المطلوبة
| الإجراء | الملف |
|---------|-------|
| تعديل | `execution/summarize_transcript.py` — توسعة الـ prompt و schema |
| تعديل | `execution/sheets_append.py` — إضافة أعمدة جديدة |
| تعديل | `pipeline.py` — تمرير الحقول الجديدة للـ row |

#### Schema الجديد المطلوب من LLM
```json
{
  "summary": "...",
  "notes": "• ...\n• ...",
  "topics": ["topic1", "topic2"],
  "sentiment": "positive | neutral | negative",
  "content_type": "tutorial | review | news | discussion | entertainment | other",
  "hook": "الجملة الافتتاحية التي شدّت المشاهد",
  "cta": "نداء التحرك في نهاية الفيديو",
  "target_audience": "وصف الجمهور المستهدف بجملة واحدة",
  "content_gap": "ما لم يغطه الفيديو وكان يجب أن يغطيه"
}
```

#### معايير القبول
- [x] LLM يُرجع الحقول الأربعة الجديدة باستمرار
- [x] auto-repair يعمل مع الـ schema الجديد
- [x] `hook` و `cta` يظهران في Google Sheets كأعمدة مستقلة
- [x] الأعمدة الجديدة في Sheets مُضافة بـ `ensure_header_row()`

#### التبعيات
- لا شيء

---

## 🟠 Phase 2 — Advanced Analysis

---

### TASK-06 · تحليل القناة الكاملة
**الأولوية**: 🟠 High  
**الحجم**: M  
**الحالة**: `[x] Done`

#### الملفات المطلوبة
| الإجراء | الملف |
|---------|-------|
| إنشاء | `execution/analyze_channel.py` |
| إنشاء | `directives/channel_analysis.md` |
| تعديل | `app.py` — إضافة `POST /api/channels/analyze` |
| تعديل | `spec_kit/SYSTEM_ARCHITECTURE.md` — ملاحظة أن db يحتوي channels table |

#### وظائف `analyze_channel.py`
```python
def get_channel_stats(channel_id: str) -> dict:
    """يجلب: subscribers, total_views, video_count, created_at"""

def get_channel_recent_videos(channel_id: str, max: int = 20) -> list:
    """يجلب آخر N فيديو مع إحصائياتها"""

def calculate_channel_score(stats: dict, recent_videos: list) -> dict:
    """يحسب growth_trend, avg_rate, upload_frequency, channel_score"""

def analyze_channel(channel_url: str) -> dict:
    """الدالة الرئيسية — تجمع كل ما سبق"""
```

#### معايير القبول
- [x] `POST /api/channels/analyze` يُرجع `channel_score` من 0-100
- [x] يكتشف: صاعد / ثابت / هابط بناءً على مشاهدات آخر 10 فيديوهات
- [x] يحسب متوسط وتيرة النشر (videos/week)
- [x] يُخزّن في channels table بقاعدة البيانات

#### التبعيات
- TASK-01 (قاعدة البيانات)

---

### TASK-07 · محرك تحليل الترندات
**الأولوية**: 🟠 High  
**الحجم**: M  
**الحالة**: `[x] Done`

#### الملفات المطلوبة
| الإجراء | الملف |
|---------|-------|
| إنشاء | `execution/trend_analyzer.py` |
| تعديل | `app.py` — إضافة `GET /api/trends` |

#### وظائف `trend_analyzer.py`
```python
def extract_keywords(text: str) -> list[str]:
    """استخراج كلمات مفتاحية من العنوان + الملاحظات + الـ topics"""

def aggregate_trends(days: int = 30, niche: str = None) -> list[dict]:
    """تجميع الكلمات الأكثر تكراراً عبر كل searches في المدة المحددة"""

def get_trending_topics(top_n: int = 20) -> list[dict]:
    """الكلمات مع: frequency, trend_direction (up/stable/down)"""
```

#### معايير القبول
- [x] `GET /api/trends?days=30` يُرجع قائمة مرتبة بالـ keywords
- [x] كل keyword يحتوي: `word`, `count`, `direction`, `first_seen`, `last_seen`
- [x] يستخدم بيانات من قاعدة البيانات المحلية (لا API خارجي)

#### التبعيات
- TASK-01 (قاعدة البيانات)
- TASK-05 (enriched topics من LLM)

---

### TASK-08 · محرك مقارنة الفيديوهات
**الأولوية**: 🟡 Medium  
**الحجم**: S  
**الحالة**: `[x] Done`

#### الملفات المطلوبة
| الإجراء | الملف |
|---------|-------|
| إنشاء | `execution/compare_videos.py` |
| تعديل | `app.py` — إضافة `POST /api/videos/compare` |

#### معايير القبول
- [x] يقبل مصفوفة `video_ids` (2 أو أكثر)
- [x] يُرجع مقارنة منظمة: نقاط قوة/ضعف لكل فيديو
- [x] يُحدد "الفيديو الفائز" ولماذا
- [x] يعمل فقط على فيديوهات مخزّنة في DB (لا API calls)

#### التبعيات
- TASK-01 (قاعدة البيانات)
- TASK-05 (hook/cta data)

---

### TASK-09 · تحليل المنافسين
**الأولوية**: 🟡 Medium  
**الحجم**: L  
**الحالة**: `[x] Done`

#### الملفات المطلوبة
| الإجراء | الملف |
|---------|-------|
| إنشاء | `execution/competitor_analyzer.py` |
| تعديل | `app.py` — إضافة `POST /api/competitors/analyze` |

#### وظائف `competitor_analyzer.py`
```python
def find_content_gaps(my_channel_id: str, competitor_ids: list) -> list:
    """موضوعات يغطيها المنافسون بنجاح ولم تغطها أنت"""

def compare_channels(channel_ids: list) -> dict:
    """مقارنة شاملة: stats, avg_rate, top_topics لكل قناة"""
```

#### معايير القبول
- [x] يُرجع "content_gaps" — قائمة بمواضيع الفرص
- [x] يتعامل مع حتى 5 قنوات منافسة بشكل متزامن
- [x] نتيجة "فرصة المحتوى" مُرتبة بقيمة البحث المقدرة

#### التبعيات
- TASK-06 (تحليل القناة)
- TASK-07 (trend analyzer)

---

### TASK-10 · تحسين صفحة History وعرض النتائج
**الأولوية**: 🟠 High  
**الحجم**: M  
**الحالة**: `[x] Done`

#### الملفات المطلوبة
| الإجراء | الملف |
|---------|-------|
| تعديل | `app.py` — إضافة `GET /api/history`, `GET /api/videos`, `DELETE /api/history/:id` |
| تعديل | `static/index.html` — إضافة History tab/page |

#### معايير القبول
- [x] المستخدم يرى كل عمليات البحث السابقة مع تاريخها (متوفر في API)
- [x] النقر على بحث سابق يعرض نتائجه كاملة (متوفر في API)
- [x] يمكن حذف بحث من السجل (تم إضافة DELETE /api/history/:id)
- [x] النتائج قابلة للفلترة بـ: min_rate, sentiment, content_type (مغطاة لاحقاً في UI)

#### التبعيات
- TASK-01 (قاعدة البيانات)

---

## 🟡 Phase 3 — Professional UI

---

### TASK-11 · Dashboard متكامل متعدد الصفحات
**الأولوية**: 🟡 Medium  
**الحجم**: L  
**الحالة**: `[x] Done`

#### الملفات المطلوبة
| الإجراء | الملف |
|---------|-------|
| إنشاء | `static/pages/dashboard.html` — إحصائيات عامة |
| إنشاء | `static/pages/research.html` — واجهة البحث المتقدم |
| إنشاء | `static/pages/history.html` — سجل البحوث |
| إنشاء | `static/pages/channels.html` — تحليل القنوات |
| إنشاء | `static/pages/trends.html` — خريطة الترندات |
| إنشاء | `static/pages/jobs.html` — إدارة المهام |
| إنشاء | `static/js/router.js` — SPA client-side routing |
| إنشاء | `static/js/video_card.js` — مكوّن بطاقة الفيديو |
| تعديل | `static/index.html` — تحويله لـ shell مع sidebar navigation |

#### معايير القبول
- [x] Navigation sidebar يعمل بدون reload
- [x] Dashboard يعرض: إجمالي فيديوهات محللة، متوسط rate، توزيع sentiment
- [x] بطاقة الفيديو تعرض thumbnail حقيقي + score breakdown
- [x] Dark mode احترافي وتصميم متسق عبر كل الصفحات

#### التبعيات
- TASK-01, TASK-03, TASK-10

---

### TASK-12 · Charts تفاعلية
**الأولوية**: 🟡 Medium  
**الحجم**: M  
**الحالة**: `[x] Done`

#### الملفات المطلوبة
| الإجراء | الملف |
|---------|-------|
| إنشاء | `static/js/chart_widgets.js` |
| تعديل | صفحات Dashboard + Trends + History |

#### أنواع الـ Charts المطلوبة
- **Score Distribution**: Bar chart لتوزيع الـ rate (0-20, 20-40, ...)
- **Sentiment Pie**: توزيع positive/neutral/negative
- **Top Topics Bar**: أكثر المواضيع تكراراً
- **Rate Over Time**: trend الأداء خلال آخر 30 يوم
- **Score Breakdown Radar**: engagement/velocity/views/sentiment/depth لكل فيديو

#### معايير القبول
- [x] كل Chart يتحدث عند تطبيق فلاتر
- [x] يعمل على Chart.js (CDN — بدون npm)
- [x] Responsive على كل أحجام الشاشات

### TASK-12.5 · عرض نتائج البحث من السجل
**الأولوية**: 🔴 High  
**الحجم**: S  
**الحالة**: `[x] Done`

#### الملفات المطلوبة
| الإجراء | الملف |
|---|---|
| تعديل | `static/pages/history.html` — توجيه المستخدم لصفحة البحث مع تمرير الـ ID |
| تعديل | `static/js/router.js` — التقاط الـ ID وجلب الفيديوهات الخاصة به |
| تعديل | `static/pages/research.html` — عرض كروت الفيديوهات بناءً على بيانات السجل |

#### معايير القبول
- [x] عند النقر على عنصر في صفحة History، يتم فتح صفحة Research وعرض كروت الفيديوهات المسترجعة.
- [x] يتم استخدام الـ API `GET /api/videos?search_id=XX` لجلب البيانات.
- [x] الفيديوهات تعرض باستخدام مكون `Video Card` ويشمل المعلومات المطلوبة.

#### التبعيات
- TASK-11, TASK-12

---

### TASK-13 · Export متعدد الصيغ
**الأولوية**: 🟡 Medium  
**الحجم**: M  
**الحالة**: `[x] Done`

#### الملفات المطلوبة
| الإجراء | الملف |
|---------|-------|
| إنشاء | `execution/report_generator.py` |
| تعديل | `app.py` — إضافة `/api/export/csv`, `/api/export/markdown`, `/api/export/json` |
| تعديل | `static/` — إضافة أزرار Export في الـ UI |

#### الصيغ المطلوبة
- **CSV**: كل الأعمدة, UTF-8 with BOM (لـ Excel Arabic)
- **Markdown**: تقرير جاهز للـ Notion مع جداول وعناوين
- **JSON**: كل البيانات كاملة للتكامل مع أدوات أخرى

#### معايير القبول
- [x] CSV يفتح بشكل صحيح في Excel مع دعم العربية
- [x] Markdown يحتوي: عنوان التقرير، ملخص إحصائي، جدول الفيديوهات
- [x] المستخدم يختار الأعمدة المراد تضمينها في CSV

#### التبعيات
- TASK-01 (قاعدة البيانات)

---

### TASK-14 · Live Progress Bar في الـ UI
**الأولوية**: 🔴 Critical  
**الحجم**: S  
**الحالة**: `[x] Done`

#### الملفات المطلوبة
| الإجراء | الملف |
|---------|-------|
| إنشاء | `static/js/progress_bar.js` |
| تعديل | `static/index.html` (أو research.html) — ربط الـ SSE بالـ UI |

#### معايير القبول
- [x] شريط تقدم يمتلئ بالتدريج مع كل فيديو
- [x] اسم الفيديو الحالي يظهر في الـ log viewer
- [x] الأخطاء تظهر بلون مختلف دون توقف العملية
- [x] عند الانتهاء: "✅ 9/10 videos processed in 47s"

#### التبعيات
- TASK-03 (SSE endpoint)

---

## 🟡 Phase 4 — Automation & Scheduling

---

### TASK-15 · نظام Jobs المجدول
**الأولوية**: 🟡 Medium  
**الحجم**: L  
**الحالة**: `[ ] Todo`

#### الملفات المطلوبة
| الإجراء | الملف |
|---------|-------|
| إنشاء | `execution/scheduler.py` |
| تعديل | `app.py` — إضافة `GET/POST/DELETE /api/jobs` |
| تعديل | `database/schema.sql` — jobs table |
| تعديل | `app.py` — تشغيل APScheduler عند بدء Flask |

#### معايير القبول
- [ ] يمكن إنشاء job مجدول من الـ UI
- [ ] يدعم: `daily_HH:MM`, `weekly_DAY_HH:MM`, `monthly_DD_HH:MM`
- [ ] يُسجّل `last_run` و `next_run` في قاعدة البيانات
- [ ] يعمل كـ background thread مع Flask بدون process منفصل

#### التبعيات
- TASK-01 (قاعدة البيانات)

---

### TASK-16 · Watchlist (مراقبة القنوات والكلمات)
**الأولوية**: 🟡 Medium  
**الحجم**: M  
**الحالة**: `[x] Done`

#### الملفات المطلوبة
| الإجراء | الملف |
|---------|-------|
| إنشاء | `execution/watchlist.py` |
| تعديل | `app.py` — إضافة `GET/POST /api/watchlist` |
| تعديل | `schema.sql` — إضافة watchlist table |

#### معايير القبول
- [x] إضافة قناة للـ Watchlist يُراقبها يومياً
- [x] إضافة keyword يُشغّل بحثاً يومياً
- [x] فيديو جديد من قناة مراقبة → يُعالج تلقائياً
- [x] نتائج تُخزّن في DB وتُرسل كإشعار (TASK-17)

#### التبعيات
- TASK-01, TASK-15

---

### TASK-17 · Telegram Notifications
**الأولوية**: 🟡 Medium  
**الحجم**: S  
**الحالة**: `[x] Done`

#### الملفات المطلوبة
| الإجراء | الملف |
|---------|-------|
| إنشاء | `execution/notify_telegram.py` |
| تعديل | `.env` — إضافة `TELEGRAM_BOT_TOKEN` و `TELEGRAM_CHAT_ID` |
| تعديل | `pipeline.py` — استدعاء Telegram عند rate > 80 |

#### وظائف `notify_telegram.py`
```python
def send_message(text: str) -> bool
def send_viral_alert(video: dict) -> bool
def send_weekly_digest(results: list) -> bool
def send_job_complete(job_name: str, count: int, top_video: dict) -> bool
```

#### معايير القبول
- [x] إشعار فوري بالتيليجرام عند اكتشاف فيديو rate > 80
- [x] الإشعارات تحتوي: عنوان، rate، link، ملخص قصير
- [x] يعمل حتى لو لم يُحدَّد `TELEGRAM_BOT_TOKEN` (يُتجاهل بأمان)

#### التبعيات
- TASK-01

---

### TASK-18 · Script Outline + Content Ideas (سريع)
**الأولوية**: 🟡 Medium  
**الحجم**: M  
**الحالة**: `[x] Done`

#### الملفات المطلوبة
| الإجراء | الملف |
|---------|-------|
| إنشاء | `execution/idea_generator.py` |
| تعديل | `app.py` — إضافة `POST /api/ideas` |

#### معايير القبول
- [x] يُولّد 5-10 أفكار فيديو بناءً على أفضل فيديوهات في DB
- [x] كل فكرة: عنوان مقترح + hook + جمهور مستهدف + نسبة نجاح مقدرة
- [x] يعمل حتى لو كان DB يحتوي 5 فيديوهات فقط

#### التبعيات
- TASK-01, TASK-05

---

## 🔵 Phase 5 — Advanced AI

---

### TASK-19 · دعم متعدد اللغات
**الأولوية**: 🔵 Low  
**الحجم**: S  
**الحالة**: `[ ] Todo`

#### الملفات المطلوبة
| الإجراء | الملف |
|---------|-------|
| تعديل | `execution/summarize_transcript.py` — detect language, respond in same lang |
| تعديل | `execution/get_transcript.py` — محاولة جلب transcript عربي أولاً |

#### معايير القبول
- [ ] فيديو عربي → ملخص وملاحظات بالعربية
- [ ] فيديو إنجليزي → ملخص بالإنجليزية
- [ ] لغة الـ response تُكتب في قاعدة البيانات كحقل `response_language`

#### التبعيات
- TASK-05

---

### TASK-20 · RAG على قاعدة البيانات
**الأولوية**: 🔵 Low  
**الحجم**: XL  
**الحالة**: `[ ] Todo`

#### الملفات المطلوبة
| الإجراء | الملف |
|---------|-------|
| إنشاء | `execution/rag_search.py` |
| تعديل | `database/schema.sql` — إضافة embeddings table |
| تعديل | `app.py` — إضافة `POST /api/rag/search` |
| تعديل | `pipeline.py` — توليد embedding وحفظه بعد كل transcript |

#### المكتبات المطلوبة
```
sentence-transformers  # local embeddings
faiss-cpu OR chromadb  # vector similarity search
```

#### معايير القبول
- [ ] `POST /api/rag/search {"query": "..."}` يُرجع top-5 مقاطع ذات صلة
- [ ] كل نتيجة تحتوي: الفيديو المصدر، المقطع النصي، درجة التشابه
- [ ] البحث يعمل في <3 ثانية على 1000 فيديو محلل

#### التبعيات
- TASK-01 (قاعدة البيانات مع كل الـ transcripts)

---

### TASK-21 · Script Generator متكامل
**الأولوية**: 🔵 Low  
**الحجم**: M  
**الحالة**: `[ ] Todo`

#### الملفات المطلوبة
| الإجراء | الملف |
|---------|-------|
| إنشاء | `execution/script_generator.py` |
| تعديل | `app.py` — إضافة `POST /api/script-outline` |

#### معايير القبول
- [ ] يُولّد: Hook (30 ثانية) → Intro (2 دقيقة) → Main Points → CTA
- [ ] مدة مقترحة لكل قسم
- [ ] مبني على hooks وCTAs من أفضل فيديوهات النيش في DB

#### التبعيات
- TASK-05, TASK-18, TASK-01

---

### TASK-22 · Niche-Specific Rating Profiles
**الأولوية**: 🔵 Low  
**الحجم**: M  
**الحالة**: `[ ] Todo`

#### الملفات المطلوبة
| الإجراء | الملف |
|---------|-------|
| إنشاء | `execution/rating_profiles.py` — ملفات أوزان لكل نيش |
| تعديل | `execution/rate_video.py` — قبول `profile` كمعامل |
| تعديل | `app.py` — `GET /api/rating-profiles` و `POST /api/rating-profiles` |

#### الـ Profiles المقترحة
```python
PROFILES = {
    "tech":          {"engagement_ratio": 0.20, "content_depth": 0.25, ...},
    "entertainment": {"engagement_ratio": 0.35, "recency_bonus": 0.20, ...},
    "education":     {"content_depth": 0.30, "sentiment_bonus": 0.15, ...},
    "news":          {"recency_bonus": 0.35, "view_velocity": 0.30, ...},
}
```

#### معايير القبول
- [ ] المستخدم يختار profile من الـ UI قبل البحث
- [ ] نفس الفيديو يحصل على rate مختلف حسب النيش
- [ ] يمكن إنشاء custom profile من الـ UI

#### التبعيات
- TASK-04

---

## 📌 ترتيب التنفيذ الموصى به

```
TASK-01 → TASK-02 → TASK-03 → TASK-05 → TASK-04
    ↓
TASK-10 → TASK-14 → TASK-11 → TASK-12 → TASK-13
    ↓
TASK-06 → TASK-07 → TASK-08 → TASK-17
    ↓
TASK-15 → TASK-16 → TASK-18
    ↓
TASK-19 → TASK-21 → TASK-22 → TASK-09 → TASK-20
```

---

## ✅ Legend

| الرمز | المعنى |
|-------|--------|
| `[ ]` | لم تبدأ |
| `[~]` | جارية |
| `[x]` | مكتملة |
| 🔴 | أولوية حرجة |
| 🟠 | أولوية عالية |
| 🟡 | أولوية متوسطة |
| 🔵 | أولوية منخفضة |
| S | صغيرة ~0.5-1 يوم |
| M | متوسطة ~1-2 يوم |
| L | كبيرة ~2-4 أيام |
| XL | ضخمة ~4-7 أيام |
