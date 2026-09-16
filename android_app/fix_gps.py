import re

with open(r'app\src\main\java\com\sih\idr\SensorService.kt', 'r', encoding='utf-8') as f:
    content = f.read()

# Add NETWORK_PROVIDER
new_gps = """        // Register GPS updates (Requires permissions handled in Activity)
        try {
            if (locationManager.isProviderEnabled(LocationManager.GPS_PROVIDER)) {
                locationManager.requestLocationUpdates(LocationManager.GPS_PROVIDER, 1000L, 0f, this)
            }
            if (locationManager.isProviderEnabled(LocationManager.NETWORK_PROVIDER)) {
                locationManager.requestLocationUpdates(LocationManager.NETWORK_PROVIDER, 1000L, 0f, this)
            }
        } catch (e: SecurityException) {"""

content = re.sub(r'        // Register GPS updates.*?try \{.*?locationManager\.requestLocationUpdates\(\s*LocationManager\.GPS_PROVIDER,.*?this\s*\).*?\} catch \(e: SecurityException\) \{', new_gps, content, flags=re.DOTALL)

with open(r'app\src\main\java\com\sih\idr\SensorService.kt', 'w', encoding='utf-8') as f:
    f.write(content)
