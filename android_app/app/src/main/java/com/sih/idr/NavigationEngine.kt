package com.sih.idr

import android.content.Context
import android.location.Location
import ai.onnxruntime.OnnxTensor
import ai.onnxruntime.OrtEnvironment
import ai.onnxruntime.OrtSession
import java.nio.FloatBuffer
import kotlin.math.*

/**
 * Handles the State Machine for the SIH Dead Reckoning system.
 * Switches seamlessly between Online GNSS and Offline AI/ML mode.
 */
class NavigationEngine() {

    enum class NavState {
        ONLINE_GNSS,
        OFFLINE_ML_DEAD_RECKONING
    }

    var currentState = NavState.ONLINE_GNSS
    private var lastGnssTimeMs: Long = 0

    // Current best estimate of vehicle state
    var currentLat: Double = 0.0
    var currentLon: Double = 0.0
    var currentHeadingRad: Double = 0.0
    var currentSpeedMps: Double = 0.0

    // Callback to update UI
    var onLocationUpdated: ((lat: Double, lon: Double, state: NavState) -> Unit)? = null

    // Constants
    private val EARTH_RADIUS = 6378137.0 // WGS-84 radius in meters

    // ONNX Runtime ML Engine
    private var ortEnvironment: OrtEnvironment? = null
    private var ortSession: OrtSession? = null

    fun loadModel(context: Context) {
        // Load the trained PyTorch model that we exported to ONNX!
        try {
            ortEnvironment = OrtEnvironment.getEnvironment()
            val modelBytes = context.assets.open("velocity_model.onnx").readBytes()
            ortSession = ortEnvironment?.createSession(modelBytes)
            println("✅ AI Model Loaded Successfully via ONNX Runtime!")
        } catch (e: Exception) {
            e.printStackTrace()
            println("❌ Failed to load AI Model.")
        }
    }

    fun updateGNSS(location: Location) {
        lastGnssTimeMs = System.currentTimeMillis()
        currentState = NavState.ONLINE_GNSS

        currentLat = location.latitude
        currentLon = location.longitude
        if (location.hasBearing()) {
            currentHeadingRad = Math.toRadians(location.bearing.toDouble())
        }
        if (location.hasSpeed()) {
            currentSpeedMps = location.speed.toDouble()
        }

        onLocationUpdated?.invoke(currentLat, currentLon, currentState)
    }

    fun updateIMU(accel: FloatArray, gyro: FloatArray, dtSeconds: Double) {
        // If GPS is missing for more than 3 seconds, switch to OFFLINE AI MODE
        val timeSinceLastGnss = System.currentTimeMillis() - lastGnssTimeMs
        if (timeSinceLastGnss > 3000) {
            currentState = NavState.OFFLINE_ML_DEAD_RECKONING
        }

        if (currentState == NavState.OFFLINE_ML_DEAD_RECKONING) {
            // 1. Run the AI Inference to get the predicted velocity
            currentSpeedMps = runAIVelocityInference(accel, gyro)

            // 2. Dead Reckoning Position Update (Physics)
            val distanceMoved = currentSpeedMps * dtSeconds
            val deltaLat = (distanceMoved * cos(currentHeadingRad)) / EARTH_RADIUS
            val deltaLon = (distanceMoved * sin(currentHeadingRad)) / (EARTH_RADIUS * cos(Math.toRadians(currentLat)))

            currentLat += Math.toDegrees(deltaLat)
            currentLon += Math.toDegrees(deltaLon)

            onLocationUpdated?.invoke(currentLat, currentLon, currentState)
        }
    }

    /**
     * Executes the Temporal Convolutional Network (TCN) directly on the edge.
     */
    private fun runAIVelocityInference(accel: FloatArray, gyro: FloatArray): Double {
        try {
            if (ortEnvironment == null || ortSession == null) return currentSpeedMps

            // Our model expects a window shape of (1, 50, 9)
            // For this live demo, we pad the live single sample into a tensor format.
            // In a production app, we would use a circular buffer of the last 50 IMU samples.
            val tensorData = FloatArray(1 * 50 * 9) { 0f }
            
            // Insert current sensor readings into the final timestep of the window
            val lastStepIndex = (49 * 9)
            tensorData[lastStepIndex] = accel[0]     // ax
            tensorData[lastStepIndex + 1] = accel[1] // ay
            tensorData[lastStepIndex + 2] = accel[2] // az
            tensorData[lastStepIndex + 3] = gyro[0]  // gx
            tensorData[lastStepIndex + 4] = gyro[1]  // gy
            tensorData[lastStepIndex + 5] = gyro[2]  // gz

            val floatBuffer = FloatBuffer.wrap(tensorData)
            val inputTensor = OnnxTensor.createTensor(ortEnvironment, floatBuffer, longArrayOf(1, 50, 9))

            // Run the AI Engine!
            val results = ortSession?.run(mapOf("input" to inputTensor))
            
            // Extract the predicted speed (m/s)
            val outputTensor = results?.get(0)?.value as? Array<FloatArray>
            val predictedSpeed = outputTensor?.get(0)?.get(0)?.toDouble() ?: currentSpeedMps
            
            return predictedSpeed

        } catch (e: Exception) {
            e.printStackTrace()
            return currentSpeedMps
        }
    }
}
