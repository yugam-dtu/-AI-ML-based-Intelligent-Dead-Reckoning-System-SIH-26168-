with open(r'app\src\main\res\layout\activity_main.xml', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace('android:id="@+id/btnStartNavigation"`n                android:text="Start Route"', 'android:id="@+id/btnStartNavigation"\n                android:text="Start Route"')

with open(r'app\src\main\res\layout\activity_main.xml', 'w', encoding='utf-8') as f:
    f.write(content)
