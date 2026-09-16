import re

with open(r'app\src\main\java\com\sih\idr\MainActivity.kt', 'r', encoding='utf-8') as f:
    content = f.read()

trim_logic = """        // Follow the vehicle if navigation started!
        if (isNavigating) {
            mapView.controller.animateTo(newPoint)
            
            // Trim the blue line behind the vehicle
            currentRouteOverlay?.let { polyline ->
                val points = polyline.actualPoints
                if (points.size > 1) {
                    val windowSize = kotlin.math.min(20, points.size)
                    var closestIdx = 0
                    var minDistance = Float.MAX_VALUE
                    for (i in 0 until windowSize) {
                        val results = FloatArray(1)
                        android.location.Location.distanceBetween(lat, lon, points[i].latitude, points[i].longitude, results)
                        if (results[0] < minDistance) {
                            minDistance = results[0]
                            closestIdx = i
                        }
                    }
                    if (closestIdx > 0) {
                        val newPoints = points.subList(closestIdx, points.size)
                        polyline.setPoints(newPoints)
                    }
                }
            }
        }"""

content = content.replace('        // Follow the vehicle if navigation started!\n        if (isNavigating) {\n            mapView.controller.animateTo(newPoint)\n        }', trim_logic)

with open(r'app\src\main\java\com\sih\idr\MainActivity.kt', 'w', encoding='utf-8') as f:
    f.write(content)
