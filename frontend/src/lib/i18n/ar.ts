// Arabic translations. Keys must mirror en.ts exactly (TranslationKey is
// the union of en's keys; missing entries produce a compile error here).

import { en } from "./en";

export const ar: Record<keyof typeof en, string> = {
  // App / nav
  "app.title": "تتبع التقدم في القرآن",
  "nav.dashboard": "لوحة التحكم",
  "nav.students": "الطلاب",
  "nav.matrix": "المصفوفة",
  "nav.classes": "الفصول",
  "nav.users": "المستخدمون",
  "nav.import": "استيراد",
  "nav.notifications": "الإشعارات",
  "nav.logout": "تسجيل الخروج",

  // Auth
  "auth.signIn": "تسجيل الدخول",
  "auth.email": "البريد الإلكتروني",
  "auth.password": "كلمة المرور",
  "auth.signingIn": "جاري تسجيل الدخول...",
  "auth.demoHint":
    "بيانات تجريبية: teacher@example.com / teacher123! و admin@example.com / admin123!.",

  // Common verbs / labels
  "common.save": "حفظ",
  "common.saving": "جاري الحفظ...",
  "common.cancel": "إلغاء",
  "common.delete": "حذف",
  "common.edit": "تعديل",
  "common.create": "إنشاء",
  "common.creating": "جاري الإنشاء...",
  "common.loading": "جاري التحميل...",
  "common.search": "بحث",
  "common.close": "إغلاق",
  "common.archive": "أرشفة",
  "common.active": "نشط",
  "common.inactive": "غير نشط",
  "common.you": "أنت",
  "common.notes": "ملاحظات",
  "common.optional": "اختياري",
  "common.history": "السجل",

  // Dashboard
  "dashboard.title": "لوحة التحكم",
  "dashboard.activeStudents": "الطلاب النشطون",
  "dashboard.avgMastery": "متوسط الإتقان (المدرسة)",
  "dashboard.avgCompletion": "متوسط الإكمال (المدرسة)",
  "dashboard.statusDistribution": "توزيع الحالة في المدرسة",
  "dashboard.statusHelp": "إجمالي كل (طالب، سورة).",

  // Students
  "students.title": "الطلاب",
  "students.new": "طالب جديد",
  "students.fullName": "الاسم الكامل",
  "students.gender": "الجنس",
  "students.male": "ذكر",
  "students.female": "أنثى",
  "students.guardianName": "اسم ولي الأمر",
  "students.guardianPhone": "هاتف ولي الأمر",
  "students.status": "الحالة",
  "students.empty": "لا يوجد طلاب بعد. اضغط على \"طالب جديد\" لإضافة طالب.",
  "students.showArchived": "إظهار المؤرشفين",
  "students.archiveConfirm":
    "هل تريد أرشفة هذا الطالب؟ سيتم الاحتفاظ ببياناته ولكنه سيختفي من القائمة الافتراضية.",

  // Matrix
  "matrix.title": "المصفوفة",
  "matrix.legend": "المفتاح:",
  "matrix.includeArchived": "تضمين المؤرشفين",
  "matrix.empty": "لا يوجد طلاب بعد.",
  "matrix.openStudent": "← فتح الطالب",
  "matrix.completion": "نسبة الإكمال %",
  "matrix.studentSurah": "الطالب ↓ / السورة ←",

  // Memorization status
  "status.NOT_STARTED": "لم يبدأ",
  "status.IN_PROGRESS": "قيد التقدم",
  "status.REVIEW_REQUIRED": "يتطلب مراجعة",
  "status.WEAK": "ضعيف",
  "status.STRONG": "قوي",
  "status.MASTERED": "متقن",

  // Notifications
  "notifications.title": "الإشعارات",
  "notifications.unreadOnly": "غير المقروءة فقط",
  "notifications.markAllRead": "تحديد الكل كمقروء",
  "notifications.markRead": "تحديد كمقروء",
  "notifications.empty": "لا توجد إشعارات بعد.",
  "notifications.emptyUnread": "لا توجد إشعارات غير مقروءة.",
  "notifications.allCaughtUp": "لا توجد إشعارات جديدة.",
  "notifications.viewAll": "عرض الكل ←",
  "notifications.openStudent": "← فتح الطالب",
  "notifications.bellLabel": "الإشعارات ({count} غير مقروءة)",

  // Notification type labels (short)
  "notifType.PROGRESS_REGRESSED": "تراجع",
  "notifType.LOW_EVALUATION": "درجة منخفضة",
  "notifType.STUDENT_ADDED": "طالب جديد",
  "notifType.OVERDUE_REVIEW": "متأخر",
  "notifType.MANUAL": "إشعار",
  // Long labels
  "notifType.PROGRESS_REGRESSED.long": "تراجع في الحفظ",
  "notifType.LOW_EVALUATION.long": "تقييم منخفض",
  "notifType.STUDENT_ADDED.long": "طالب جديد",
  "notifType.OVERDUE_REVIEW.long": "مراجعة متأخرة",
  "notifType.MANUAL.long": "إشعار",

  // Offline / PWA
  "pwa.offlineTitle": "أنت غير متصل.",
  "pwa.offlineDesc":
    "القراءة لا تزال تعمل من الذاكرة المؤقتة. لا يمكن حفظ التغييرات الجديدة حتى تعود للاتصال.",

  // Class detail
  "classDetail.studentCount": "الطلاب",
  "classDetail.avgMastery": "متوسط الإتقان",
  "classDetail.avgCompletion": "متوسط الإكمال",
  "classDetail.statusDistribution": "توزيع الحالة في الفصل",
  "classDetail.statusHelp": "إجمالي كل (طالب، سورة) في هذا الفصل.",
  "classDetail.members": "الأعضاء",
  "classDetail.noMembers": "لم يتم تعيين أي طالب لهذا الفصل بعد.",
  "classDetail.openStudent": "فتح الملف ←",

  // Revision suggestions (§12-C)
  "revision.title": "مراجعات مقترحة",
  "revision.subtitle": "سور تحتاج إلى مراجعة، مرتبة حسب الأولوية.",
  "revision.empty": "لا توجد مراجعات مطلوبة حاليًا. أحسنت!",
  "revision.loading": "جاري حساب المقترحات...",
  "revision.daysAgo": "منذ {days} يوم",
  "revision.neverReviewed": "لم تُراجع من قبل",
  "revision.completion": "اكتمل {percent}%",
  // Reason labels
  "revision.reason.WEAK": "ضعيف — يحتاج إلى تثبيت",
  "revision.reason.REVIEW_REQUIRED": "محدد للمراجعة",
  "revision.reason.STALE_MASTERED": "متقن لكن لم يُراجع مؤخرًا",
  "revision.reason.STALE_STRONG": "قوي لكن لم يُراجع مؤخرًا",
  "revision.reason.IN_PROGRESS": "تابع التقدم في هذه السورة",

  // Language switcher
  "lang.toggle": "اللغة",
};
