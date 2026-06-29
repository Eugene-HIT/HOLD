kt_path = r'D:\ADHD\MyApplication\app\src\main\java\com\example\myapplication\MainActivity.kt'
with open(kt_path, 'r', encoding='utf-8') as f:
    kt_content = f.read()

back_to_trigger = '''btnBackToPool.setOnClickListener {
            helpDetailView.visibility = android.view.View.GONE
            reparentViews(false)
            poolView.visibility = android.view.View.VISIBLE
            findViewById<android.view.View>(R.id.bottom_nav_container).visibility = android.view.View.VISIBLE
        }'''

to_replace = '''btnBackToPool.setOnClickListener {
            helpDetailView.visibility = android.view.View.GONE
            poolView.visibility = android.view.View.VISIBLE
            findViewById<android.view.View>(R.id.bottom_nav_container).visibility = android.view.View.VISIBLE
        }'''

kt_content = kt_content.replace(to_replace, back_to_trigger)

with open(kt_path, 'w', encoding='utf-8') as f:
    f.write(kt_content)
