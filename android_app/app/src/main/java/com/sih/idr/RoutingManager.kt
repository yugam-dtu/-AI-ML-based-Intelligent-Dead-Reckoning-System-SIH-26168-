package com.sih.idr

import org.json.JSONObject
import java.io.BufferedReader
import java.io.InputStreamReader
import java.net.HttpURLConnection
import java.net.URL
import kotlin.concurrent.thread

/**
 * Handles online routing requests using the open OSRM API, similar to Google Maps Directions.
 */
class RoutingManager {

    interface RouteCallback {
        fun onRouteFound(routeCoordinates: List<Pair<Double, Double>>, distanceMeters: Double)
        fun onError(error: String)
    }

    /**
     * Fetches the best route between two coordinates.
     */
    fun getRoute(startLat: Double, startLon: Double, endLat: Double, endLon: Double, callback: RouteCallback) {
        thread {
            try {
                // OSRM API expects lon,lat format
                val urlString = "https://router.project-osrm.org/route/v1/driving/$startLon,$startLat;$endLon,$endLat?overview=full&geometries=geojson"
                val url = URL(urlString)
                val connection = url.openConnection() as HttpURLConnection
                connection.requestMethod = "GET"
                connection.setRequestProperty("User-Agent", "SIH-IDR-App")
                connection.connectTimeout = 5000
                connection.readTimeout = 5000

                if (connection.responseCode == 200) {
                    val reader = BufferedReader(InputStreamReader(connection.inputStream))
                    val response = reader.readText()
                    reader.close()

                    val json = JSONObject(response)
                    val routes = json.getJSONArray("routes")
                    if (routes.length() > 0) {
                        val route = routes.getJSONObject(0)
                        val distance = route.getDouble("distance")
                        
                        val geometry = route.getJSONObject("geometry")
                        val coordinates = geometry.getJSONArray("coordinates")
                        
                        val routePoints = mutableListOf<Pair<Double, Double>>()
                        for (i in 0 until coordinates.length()) {
                            val point = coordinates.getJSONArray(i)
                            val lon = point.getDouble(0)
                            val lat = point.getDouble(1)
                            routePoints.add(Pair(lat, lon))
                        }
                        
                        callback.onRouteFound(routePoints, distance)
                    } else {
                        callback.onError("No route found.")
                    }
                } else {
                    callback.onError("Routing API returned HTTP ${connection.responseCode}")
                }
            } catch (e: Exception) {
                callback.onError("Network error: ${e.message}")
            }
        }
    }
}
