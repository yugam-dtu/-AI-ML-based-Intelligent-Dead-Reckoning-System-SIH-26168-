with open(r'app\src\main\java\com\sih\idr\MainActivity.kt', 'r', encoding='utf-8') as f:
    content = f.read()

bad_block = """        btnStartNavigation.setOnClickListener {
            isNavigating = true
            vehicleMarker?.let { marker ->
                mapView.controller.animateTo(marker.position)
                mapView.controller.setZoom(19.0)
                tvStatus.text = "Navigation Started! Following vehicle..."
            }
        }
        }"""
        
good_block = """        btnStartNavigation.setOnClickListener {
            isNavigating = true
            vehicleMarker?.let { marker ->
                mapView.controller.animateTo(marker.position)
                mapView.controller.setZoom(19.0)
                tvStatus.text = "Navigation Started! Following vehicle..."
            }
        }"""

content = content.replace(bad_block, good_block)

with open(r'app\src\main\java\com\sih\idr\MainActivity.kt', 'w', encoding='utf-8') as f:
    f.write(content)
