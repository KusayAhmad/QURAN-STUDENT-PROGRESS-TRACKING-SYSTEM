// English source-of-truth dictionary. Adding a key here forces ar.ts to add it
// (compile error in i18n.ts otherwise).

export const en = {
  // App / nav
  "app.title": "Quran Progress Tracker",
  "nav.dashboard": "Dashboard",
  "nav.students": "Students",
  "nav.matrix": "Matrix",
  "nav.users": "Users",
  "nav.import": "Import",
  "nav.notifications": "Notifications",
  "nav.logout": "Logout",

  // Auth
  "auth.signIn": "Sign in",
  "auth.email": "Email",
  "auth.password": "Password",
  "auth.signingIn": "Signing in...",
  "auth.demoHint":
    "Demo seed creates teacher@example.com / teacher123! and admin@example.com / admin123!.",

  // Common verbs / labels
  "common.save": "Save",
  "common.saving": "Saving...",
  "common.cancel": "Cancel",
  "common.delete": "Delete",
  "common.edit": "Edit",
  "common.create": "Create",
  "common.creating": "Creating...",
  "common.loading": "Loading...",
  "common.search": "Search",
  "common.close": "Close",
  "common.archive": "Archive",
  "common.active": "Active",
  "common.inactive": "Inactive",
  "common.you": "you",
  "common.notes": "Notes",
  "common.optional": "optional",
  "common.history": "History",

  // Dashboard
  "dashboard.title": "Dashboard",
  "dashboard.activeStudents": "Active students",
  "dashboard.avgMastery": "Avg. mastery (school)",
  "dashboard.avgCompletion": "Avg. completion (school)",
  "dashboard.statusDistribution": "Status distribution across school",
  "dashboard.statusHelp": "Aggregate of every (student, surah) slot.",

  // Students
  "students.title": "Students",
  "students.new": "New student",
  "students.fullName": "Full name",
  "students.gender": "Gender",
  "students.male": "Male",
  "students.female": "Female",
  "students.guardianName": "Guardian name",
  "students.guardianPhone": "Guardian phone",
  "students.status": "Status",
  "students.empty": "No students yet. Click \"New student\" to add one.",
  "students.showArchived": "Show archived",
  "students.archiveConfirm":
    "Archive this student? Their data is preserved but they will be hidden from the default list.",

  // Matrix
  "matrix.title": "Matrix",
  "matrix.legend": "Legend:",
  "matrix.includeArchived": "Include archived",
  "matrix.empty": "No students yet.",
  "matrix.openStudent": "Open student →",
  "matrix.completion": "Completion %",
  "matrix.studentSurah": "Student ↓ / Surah →",

  // Memorization status
  "status.NOT_STARTED": "Not started",
  "status.IN_PROGRESS": "In progress",
  "status.REVIEW_REQUIRED": "Review required",
  "status.WEAK": "Weak",
  "status.STRONG": "Strong",
  "status.MASTERED": "Mastered",

  // Notifications
  "notifications.title": "Notifications",
  "notifications.unreadOnly": "Unread only",
  "notifications.markAllRead": "Mark all read",
  "notifications.markRead": "Mark read",
  "notifications.empty": "No notifications yet.",
  "notifications.emptyUnread": "No unread notifications.",
  "notifications.allCaughtUp": "You're all caught up.",
  "notifications.viewAll": "View all →",
  "notifications.openStudent": "Open student →",

  // Notification type labels (short, for the bell)
  "notifType.PROGRESS_REGRESSED": "Regression",
  "notifType.LOW_EVALUATION": "Low score",
  "notifType.STUDENT_ADDED": "New student",
  "notifType.OVERDUE_REVIEW": "Overdue",
  "notifType.MANUAL": "Notice",
  // Long labels for the inbox page
  "notifType.PROGRESS_REGRESSED.long": "Regression",
  "notifType.LOW_EVALUATION.long": "Low evaluation",
  "notifType.STUDENT_ADDED.long": "New student",
  "notifType.OVERDUE_REVIEW.long": "Overdue review",
  "notifType.MANUAL.long": "Notice",

  // Offline / PWA
  "pwa.offlineTitle": "You're offline.",
  "pwa.offlineDesc":
    "Reads still work from cache. New changes can't be saved until you reconnect.",

  // Language switcher
  "lang.toggle": "Language",
} as const;
