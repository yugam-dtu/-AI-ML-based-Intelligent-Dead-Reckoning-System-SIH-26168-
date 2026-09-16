import re

with open(r'app\src\main\java\com\sih\idr\MainActivity.kt', 'r', encoding='utf-8') as f:
    content = f.read()

# Add target variables
if "private var targetLat: Double = 0.0" not in content:
    content = content.replace('private var isNavigating = false', 'private var isNavigating = false\n    private var targetLat: Double = 0.0\n    private var targetLon: Double = 0.0')

# 1. Fix handleRouteRequest to allow empty From field (Current Location)
new_handle_route = """    private fun handleRouteRequest() {
        val fromQuery = inputFrom.text.toString()
        val toQuery = inputTo.text.toString()

        if (toQuery.isEmpty()) {
            android.widget.Toast.makeText(this, "Please enter a destination", android.widget.Toast.LENGTH_SHORT).show()
            return
        }

        tvStatus.text = "Geocoding addresses..."
        
        Thread {
            val startCoords = if (fromQuery.isEmpty() || fromQuery.lowercase() == "my location") {
                if (SensorService.navigationEngine.currentLat != 0.0) {
                    Pair(SensorService.navigationEngine.currentLat, SensorService.navigationEngine.currentLon)
                } else {
                    null // Will trigger error below
                }
            } else {
                getCoordinatesFromNominatim(fromQuery)
            }
            
            val endCoords = getCoordinatesFromNominatim(toQuery)"""

content = re.sub(r'    private fun handleRouteRequest\(\) \{.*?val endCoords = getCoordinatesFromNominatim\(toQuery\)', new_handle_route, content, flags=re.DOTALL)

# 2. Save target coordinates when route is found
content = content.replace('SensorService.navigationEngine.currentLon = startCoords.second', 'SensorService.navigationEngine.currentLon = startCoords.second\n                            targetLat = endCoords.first\n                            targetLon = endCoords.second')

# 3. Update the updateVehicleLocationOnMap function to show ETA and Speed
new_update_ui = """        // Change UI based on whether we are online or offline AI/ML mode
        if (state == NavigationEngine.NavState.ONLINE_GNSS) {
            vehicleMarker?.title = "Online (GNSS)"
            tvStatus.setTextColor(android.graphics.Color.parseColor("#555555"))
        } else {
            vehicleMarker?.title = "Offline (AI)"
            tvStatus.setTextColor(android.graphics.Color.RED)
        }
        
        if (isNavigating && targetLat != 0.0) {
            val speed = SensorService.navigationEngine.currentSpeedMps
            val results = FloatArray(1)
            android.location.Location.distanceBetween(lat, lon, targetLat, targetLon, results)
            val distanceRemaining = results[0]
            val etaMins = if (speed > 0.5) (distanceRemaining / speed) / 60.0 else 0.0
            
            val statusMode = if (state == NavigationEngine.NavState.ONLINE_GNSS) "GPS" else "AI"
            tvStatus.text = String.format("[%s] Spd: %.1f m/s | ETA: %.1f mins | %.1f km left", statusMode, speed, etaMins, distanceRemaining/1000.0)
        } else if (!isNavigating) {
            if (state == NavigationEngine.NavState.ONLINE_GNSS) {
                tvStatus.text = "System Status: ONLINE (GPS Active)"
            } else {
                tvStatus.text = "System Status: OFFLINE AI Dead Reckoning Active"
            }
        }"""
        
content = re.sub(r'        // Change UI based on whether we are online or offline AI/ML mode.*?tvStatus\.text = "System Status: OFFLINE AI Dead Reckoning Active"\n            \}\n        \}', new_update_ui, content, flags=re.DOTALL)

with open(r'app\src\main\java\com\sih\idr\MainActivity.kt', 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated MainActivity logic!")
