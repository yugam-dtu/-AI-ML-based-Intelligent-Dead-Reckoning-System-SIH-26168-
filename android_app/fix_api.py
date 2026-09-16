import re

with open(r'app\src\main\java\com\sih\idr\MainActivity.kt', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Fix setupAutoComplete
new_autocomplete = """                            val encodedQuery = java.net.URLEncoder.encode(query, "UTF-8")
                            val url = java.net.URL("https://photon.komoot.io/api/?q=$encodedQuery&limit=5&bbox=68.1,6.7,97.4,35.5")
                            val connection = url.openConnection() as java.net.HttpURLConnection
                            connection.setRequestProperty("User-Agent", "SIH-IDR-App")
                            if (connection.responseCode == 200) {
                                val response = connection.inputStream.bufferedReader().readText()
                                val jsonObject = org.json.JSONObject(response)
                                val features = jsonObject.getJSONArray("features")
                                val suggestions = mutableListOf<String>()
                                for (i in 0 until features.length()) {
                                    val feature = features.getJSONObject(i)
                                    val props = feature.getJSONObject("properties")
                                    val name = props.optString("name", "")
                                    val city = props.optString("city", props.optString("state", ""))
                                    val displayName = if (name.isNotEmpty() && city.isNotEmpty()) "$name, $city" else if (name.isNotEmpty()) name else city
                                    if (displayName.isNotEmpty()) suggestions.add(displayName)
"""

content = re.sub(r'val encodedQuery = java\.net\.URLEncoder\.encode\(query, "UTF-8"\)\s*val url = java\.net\.URL\("https://nominatim.*?val shortName = .*?displayName', new_autocomplete, content, flags=re.DOTALL)
content = content.replace('suggestions.add(shortName)', '')

# 2. Fix getCoordinatesFromNominatim
new_get_coords = """    private fun getCoordinatesFromNominatim(query: String): Pair<Double, Double>? {
        try {
            val encodedQuery = java.net.URLEncoder.encode(query, "UTF-8")
            val url = java.net.URL("https://photon.komoot.io/api/?q=$encodedQuery&limit=1&bbox=68.1,6.7,97.4,35.5")
            val connection = url.openConnection() as java.net.HttpURLConnection
            connection.setRequestProperty("User-Agent", "SIH-IDR-App")
            if (connection.responseCode == 200) {
                val response = connection.inputStream.bufferedReader().readText()
                val jsonObject = org.json.JSONObject(response)
                val features = jsonObject.getJSONArray("features")
                if (features.length() > 0) {
                    val coords = features.getJSONObject(0).getJSONObject("geometry").getJSONArray("coordinates")
                    // Photon returns [lon, lat]
                    return Pair(coords.getDouble(1), coords.getDouble(0))
                }
            }"""

content = re.sub(r'private fun getCoordinatesFromNominatim.*?if \(jsonArray\.length\(\) > 0\) \{.*?return Pair\(obj\.getDouble\("lat"\), obj\.getDouble\("lon"\)\)\s*\}\s*\}', new_get_coords, content, flags=re.DOTALL)

# 3. Fix handleRouteRequest to show error
error_handler = """            if (startCoords != null && endCoords != null) {
                runOnUiThread {
                    tvStatus.text = "Fetching best route (Google Maps style)..."
                }

                // Online Route fetching
                routingManager.getRoute(startCoords.first, startCoords.second, endCoords.first, endCoords.second, object : RoutingManager.RouteCallback {
                    override fun onRouteFound(routeCoordinates: List<Pair<Double, Double>>, distanceMeters: Double) {
                        runOnUiThread {
                            drawRouteOnMap(routeCoordinates)
                            tvDistance.text = String.format("%.1f km", distanceMeters / 1000.0)
                            tvStatus.text = "Route Found. Online (GNSS)"
                            tvStatus.setTextColor(android.graphics.Color.parseColor("#555555"))
                            
                            // Initialize AI Engine Position to start of route
                            SensorService.navigationEngine.currentLat = startCoords.first
                            SensorService.navigationEngine.currentLon = startCoords.second
                        }
                    }
                    override fun onRouteFailed(error: String) {
                        runOnUiThread { tvStatus.text = "Routing failed: $error" }
                    }
                })
            } else {
                runOnUiThread {
                    tvStatus.text = "Location not found! Try being more specific."
                    tvStatus.setTextColor(android.graphics.Color.RED)
                }
            }"""

content = re.sub(r'if \(startCoords != null && endCoords != null\) \{.*?(?=\}\.start\(\))', error_handler + '\n            ', content, flags=re.DOTALL)

with open(r'app\src\main\java\com\sih\idr\MainActivity.kt', 'w', encoding='utf-8') as f:
    f.write(content)

print("Modifications done!")
