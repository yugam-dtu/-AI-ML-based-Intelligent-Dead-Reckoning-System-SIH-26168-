import re

with open(r'app\src\main\java\com\sih\idr\MainActivity.kt', 'r', encoding='utf-8') as f:
    content = f.read()

# Add isNavigating flag
if "private var isNavigating = false" not in content:
    content = content.replace('private var vehicleMarker: Marker? = null', 'private var vehicleMarker: Marker? = null\n    private var isNavigating = false')

# Update btnStartNavigation listener
new_listener = """        btnStartNavigation.setOnClickListener {
            isNavigating = true
            vehicleMarker?.let { marker ->
                mapView.controller.animateTo(marker.position)
                mapView.controller.setZoom(19.0)
                tvStatus.text = "Navigation Started! Following vehicle..."
            }
        }"""
content = re.sub(r'btnStartNavigation\.setOnClickListener \{.*?\}', new_listener, content, flags=re.DOTALL)

# Update updateVehicleLocationOnMap
new_update = """    private fun updateVehicleLocationOnMap(lat: Double, lon: Double, state: NavigationEngine.NavState) {
        if (lat == 0.0 && lon == 0.0) return // Ignore uninitialized coordinates
        
        val newPoint = GeoPoint(lat, lon)
        if (vehicleMarker == null) {
            vehicleMarker = Marker(mapView).apply {
                position = newPoint
                setAnchor(Marker.ANCHOR_CENTER, Marker.ANCHOR_BOTTOM)
                icon = resources.getDrawable(android.R.drawable.ic_menu_mylocation, null)
                title = "Vehicle"
                mapView.overlays.add(this)
            }
        } else {
            vehicleMarker?.position = newPoint
        }
        
        // Follow the vehicle if navigation started!
        if (isNavigating) {
            mapView.controller.animateTo(newPoint)
        }

        // Change UI based on whether we are online or offline AI/ML mode"""
        
content = re.sub(r'private fun updateVehicleLocationOnMap.*?// Change UI based on whether we are online or offline AI/ML mode', new_update, content, flags=re.DOTALL)

with open(r'app\src\main\java\com\sih\idr\MainActivity.kt', 'w', encoding='utf-8') as f:
    f.write(content)
print("Added camera tracking!")
