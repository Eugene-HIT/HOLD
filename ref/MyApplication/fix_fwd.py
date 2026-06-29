kt_path = r'D:\ADHD\MyApplication\app\src\main\java\com\example\myapplication\MainActivity.kt'
with open(kt_path, 'r', encoding='utf-8') as f:
    kt_content = f.read()

fwd_to_trigger = '''                      tvDetailTitle.text = item.name + " 的求助"
                      tvDetailTask.text = item.task
                      helpDetailView.visibility = android.view.View.VISIBLE
                      reparentViews(true)
                  }'''

to_replace = '''                      tvDetailTitle.text = item.name + " 的求助"
                      tvDetailTask.text = item.task
                      helpDetailView.visibility = android.view.View.VISIBLE
                  }'''

kt_content = kt_content.replace(to_replace, fwd_to_trigger)

with open(kt_path, 'w', encoding='utf-8') as f:
    f.write(kt_content)
