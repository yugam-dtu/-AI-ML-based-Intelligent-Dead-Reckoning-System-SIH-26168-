package com.sih.idr

import android.app.Service
import android.content.Intent
import android.hardware.Sensor
import android.hardware.SensorEvent
import android.hardware.SensorEventListener
import android.hardware.SensorManager
import android.location.Location
import android.location.LocationListener
import android.location.LocationManager
import android.os.IBinder
import android.util.Log
import android.app.NotificationChannel
import android.app.NotificationManager
import android.os.Build
import androidx.core.app.NotificationCompat
import android.content.pm.ServiceInfo

/**
 * Foreground Service to continuously collect IMU and GPS data.
 * 
 * To compile: Ensure you have set up a standard Android Studio project.
 * Request runtime permissions for location before starting this service.
 */
class SensorService : Service(), SensorEventListener, LocationListener {

    private lateinit var sensorManager: SensorManager
    private lateinit var locationManager: LocationManager
    
    private val accelBuffer = FloatArray(3)
    private val gyroBuffer = FloatArray(3)

    companion object {
        val navigationEngine = NavigationEngine()
    }

    override fun onCreate() {
        super.onCreate()
        navigationEngine.loadModel(this)
        sensorManager = getSystemService(SENSOR_SERVICE) as SensorManager
        locationManager = getSystemService(LOCATION_SERVICE) as LocationManager
        
        // Register sensors (Accelerometer, Gyroscope, Magnetic Field)
        // Note: For 10Hz, SENSOR_DELAY_NORMAL is ~5Hz, SENSOR_DELAY_UI is ~15Hz, SENSOR_DELAY_GAME is ~50Hz.
        // In practice, request a specific microsecond delay if needed: 100000 us = 10Hz
        val samplingPeriodUs = 100000
        
        sensorManager.getDefaultSensor(Sensor.TYPE_ACCELEROMETER)?.let {
            sensorManager.registerListener(this, it, samplingPeriodUs)
        }
        sensorManager.getDefaultSensor(Sensor.TYPE_GYROSCOPE)?.let {
            sensorManager.registerListener(this, it, samplingPeriodUs)
        }
        sensorManager.getDefaultSensor(Sensor.TYPE_MAGNETIC_FIELD)?.let {
            sensorManager.registerListener(this, it, samplingPeriodUs)
        }

        // Register GPS updates (Requires permissions handled in Activity)
        try {
            if (locationManager.isProviderEnabled(LocationManager.GPS_PROVIDER)) {
                locationManager.requestLocationUpdates(LocationManager.GPS_PROVIDER, 1000L, 0f, this)
            }
            if (locationManager.isProviderEnabled(LocationManager.NETWORK_PROVIDER)) {
                locationManager.requestLocationUpdates(LocationManager.NETWORK_PROVIDER, 1000L, 0f, this)
            }
        } catch (e: SecurityException) {
            Log.e("SensorService", "Location permission not granted", e)
        }
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        createNotificationChannel()
        val notification = androidx.core.app.NotificationCompat.Builder(this, "sensor_service_channel")
            .setContentTitle("Dead Reckoning Active")
            .setContentText("Monitoring sensors and GPS...")
            .setSmallIcon(android.R.drawable.ic_menu_mylocation)
            .build()
        
        if (android.os.Build.VERSION.SDK_INT >= android.os.Build.VERSION_CODES.Q) {
            startForeground(1, notification, ServiceInfo.FOREGROUND_SERVICE_TYPE_LOCATION)
        } else {
            startForeground(1, notification)
        }
        return START_STICKY
    }

    private fun createNotificationChannel() {
        val serviceChannel = android.app.NotificationChannel(
            "sensor_service_channel",
            "Sensor Service Channel",
            android.app.NotificationManager.IMPORTANCE_DEFAULT
        )
        val manager = getSystemService(android.app.NotificationManager::class.java)
        manager.createNotificationChannel(serviceChannel)
    }

    override fun onBind(intent: Intent?): IBinder? {
        return null // Replace with Binder if Activity needs to bind directly
    }

    override fun onDestroy() {
        super.onDestroy()
        sensorManager.unregisterListener(this)
        locationManager.removeUpdates(this)
    }

    override fun onSensorChanged(event: SensorEvent?) {
        event ?: return
        
        when (event.sensor.type) {
            Sensor.TYPE_ACCELEROMETER -> {
                System.arraycopy(event.values, 0, accelBuffer, 0, 3)
            }
            Sensor.TYPE_GYROSCOPE -> {
                System.arraycopy(event.values, 0, gyroBuffer, 0, 3)
            }
        }
        
        // In a real app, we'd use a sliding window. For this skeleton, we update at every sensor event
        // or a fixed rate. Here we just pass the latest values.
        navigationEngine.updateIMU(accelBuffer, gyroBuffer, 0.1)
    }

    override fun onAccuracyChanged(sensor: Sensor?, accuracy: Int) {}

    override fun onLocationChanged(location: android.location.Location) {
        navigationEngine.updateGNSS(location)
    }
}
