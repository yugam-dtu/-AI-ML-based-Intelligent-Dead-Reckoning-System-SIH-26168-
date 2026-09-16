import re

with open(r'app\src\main\java\com\sih\idr\MainActivity.kt', 'r', encoding='utf-8') as f:
    content = f.read()

crash_handler = """        // Global Exception Handler
        val oldHandler = Thread.getDefaultUncaughtExceptionHandler()
        Thread.setDefaultUncaughtExceptionHandler { thread, throwable ->
            android.util.Log.e("FATAL_ERROR", "Uncaught exception", throwable)
            val intent = android.content.Intent(this, MainActivity::class.java).apply {
                putExtra("CRASH_ERROR", throwable.toString() + "\\n\\n" + throwable.stackTraceToString().take(500))
                addFlags(android.content.Intent.FLAG_ACTIVITY_CLEAR_TOP or android.content.Intent.FLAG_ACTIVITY_NEW_TASK)
            }
            startActivity(intent)
            kotlin.system.exitProcess(1)
        }
        
        intent.getStringExtra("CRASH_ERROR")?.let { errorMsg ->
            android.app.AlertDialog.Builder(this)
                .setTitle("App Crashed!")
                .setMessage(errorMsg)
                .setPositiveButton("OK", null)
                .show()
        }
        
        // Initialize OSMDroid config"""

content = content.replace('        // Initialize OSMDroid config', crash_handler)

with open(r'app\src\main\java\com\sih\idr\MainActivity.kt', 'w', encoding='utf-8') as f:
    f.write(content)
