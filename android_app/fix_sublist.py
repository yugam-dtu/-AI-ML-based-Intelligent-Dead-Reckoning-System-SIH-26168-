import re

with open(r'app\src\main\java\com\sih\idr\MainActivity.kt', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace('val newPoints = points.subList(closestIdx, points.size)', 'val newPoints = ArrayList(points.subList(closestIdx, points.size))')

with open(r'app\src\main\java\com\sih\idr\MainActivity.kt', 'w', encoding='utf-8') as f:
    f.write(content)
