package com.securityapp

import android.content.Context
import android.graphics.BitmapFactory
import android.os.Bundle
import android.util.Log
import android.view.View
import android.widget.ImageView
import android.widget.TextView
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.datastore.core.DataStore
import androidx.datastore.preferences.core.Preferences
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.core.stringPreferencesKey
import androidx.datastore.preferences.preferencesDataStore
import androidx.lifecycle.lifecycleScope
import com.example.securityapp.R
import com.google.android.material.button.MaterialButton
import com.google.android.material.textfield.TextInputEditText
import com.google.android.material.textfield.TextInputLayout
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.launch
import okhttp3.*
import okhttp3.RequestBody.Companion.toRequestBody
import okio.ByteString
import java.io.IOException
import java.util.concurrent.TimeUnit

private val Context.dataStore: DataStore<Preferences> by preferencesDataStore(name = "settings")
private val PI_HOST = stringPreferencesKey("pi_host")
private val API_KEY = stringPreferencesKey("api_key")

class MainActivity : AppCompatActivity() {
    private lateinit var inputLayoutPiHost: TextInputLayout
    private lateinit var inputLayoutApiKey: TextInputLayout
    private lateinit var editPiHost: TextInputEditText
    private lateinit var editApiKey: TextInputEditText
    private lateinit var buttonConnect: MaterialButton
    private lateinit var buttonDisconnect: MaterialButton
    private lateinit var buttonToggleCamera: MaterialButton
    private lateinit var textTemperature: TextView
    private lateinit var textMotion: TextView
    private lateinit var imageVideo: ImageView

    private val client = OkHttpClient.Builder()
        .readTimeout(30, TimeUnit.SECONDS)
        .build()

    private var apiKey: String = ""
    private var piHost: String = ""
    private var isCameraOn: Boolean = true
    private var isStreaming: Boolean = false

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        inputLayoutPiHost = findViewById(R.id.inputLayoutPiHost)
        inputLayoutApiKey = findViewById(R.id.inputLayoutApiKey)
        editPiHost = findViewById(R.id.editPiHost)
        editApiKey = findViewById(R.id.editApiKey)
        buttonConnect = findViewById(R.id.buttonConnect)
        buttonDisconnect = findViewById(R.id.buttonDisconnect)
        buttonToggleCamera = findViewById(R.id.buttonToggleCamera)
        textTemperature = findViewById(R.id.textTemperature)
        textMotion = findViewById(R.id.textMotion)
        imageVideo = findViewById(R.id.imageVideo)

        // Load saved credentials
        lifecycleScope.launch {
            val preferences = dataStore.data.first()
            editPiHost.setText(preferences[PI_HOST] ?: "")
            editApiKey.setText(preferences[API_KEY] ?: "")
        }

        buttonConnect.setOnClickListener {
            piHost = editPiHost.text.toString().trim()
            apiKey = editApiKey.text.toString().trim()
            if (piHost.isNotEmpty() && apiKey.isNotEmpty()) {
                // Save credentials to DataStore
                lifecycleScope.launch {
                    dataStore.edit { settings ->
                        settings[PI_HOST] = piHost
                        settings[API_KEY] = apiKey
                    }
                }
                fetchTemperature()
                fetchMotion()
                startVideoStream()
            }
        }

        buttonDisconnect.setOnClickListener {
            disconnect()
        }

        buttonToggleCamera.setOnClickListener {
            toggleCamera()
        }
    }

    private fun disconnect() {
        isStreaming = false
        runOnUiThread {
            inputLayoutPiHost.visibility = View.VISIBLE
            inputLayoutApiKey.visibility = View.VISIBLE
            buttonConnect.visibility = View.VISIBLE
            buttonDisconnect.visibility = View.GONE
            buttonToggleCamera.visibility = View.GONE
            imageVideo.setImageBitmap(null)
            textTemperature.text = getString(R.string.temperature_format, "--", "--")
            textMotion.text = getString(R.string.motion_format, "unknown")
        }
    }

    private fun toggleCamera() {
        val action = if (isCameraOn) "stop" else "start"
        val url = "http://$piHost:5000/camera/$action"

        val request = Request.Builder()
            .url(url)
            .post(ByteArray(0).toRequestBody(null))
            .addHeader("X-API-KEY", apiKey)
            .build()

        client.newCall(request).enqueue(object : Callback {
            override fun onFailure(call: Call, e: IOException) {
                Log.e("MainActivity", "Camera $action request failed", e)
            }

            override fun onResponse(call: Call, response: Response) {
                if (response.isSuccessful) {
                    isCameraOn = !isCameraOn
                    runOnUiThread {
                        buttonToggleCamera.text = if (isCameraOn) getString(R.string.camera_on) else getString(R.string.camera_off)
                    }
                }
                response.close()
            }
        })
        if(!isCameraOn) {
            startVideoStream()
        }
    }

    private fun fetchTemperature() {
        val url = "http://$piHost:5000/temperature"
        val request = Request.Builder()
            .url(url)
            .addHeader("X-API-KEY", apiKey)
            .build()

        client.newCall(request).enqueue(object : Callback {
            override fun onFailure(call: Call, e: IOException) {
                Log.e("MainActivity", "Temperature request failed", e)
                runOnUiThread {
                    Toast.makeText(this@MainActivity, "Connection failed: ${e.message}", Toast.LENGTH_SHORT).show()
                }
            }

            override fun onResponse(call: Call, response: Response) {
                if (response.isSuccessful) {
                    response.body?.string()?.let { body ->
                        val temperature = JsonUtils.getValueFromJson(body, "temperature_f")
                        val humidity = JsonUtils.getValueFromJson(body, "humidity")
                        runOnUiThread {
                            textTemperature.text = getString(R.string.temperature_format, temperature, humidity)
                            // Hide connection UI on success
                            inputLayoutPiHost.visibility = View.GONE
                            inputLayoutApiKey.visibility = View.GONE
                            buttonConnect.visibility = View.GONE
                            buttonDisconnect.visibility = View.VISIBLE
                            buttonToggleCamera.visibility = View.VISIBLE
                        }
                    }
                } else {
                    runOnUiThread {
                        Toast.makeText(this@MainActivity, "Connection failed: ${response.code}", Toast.LENGTH_SHORT).show()
                    }
                }
                response.close()
            }
        })
    }

    private fun fetchMotion() {
        val url = "http://$piHost:5000/motion"
        val request = Request.Builder()
            .url(url)
            .addHeader("X-API-KEY", apiKey)
            .build()

        client.newCall(request).enqueue(object : Callback {
            override fun onFailure(call: Call, e: IOException) {
                Log.e("MainActivity", "Motion request failed", e)
            }

            override fun onResponse(call: Call, response: Response) {
                if (response.isSuccessful) {
                    response.body?.string()?.let { body ->
                        val motionDetect = JsonUtils.getValueFromJson(body, "motion_detected")
                        runOnUiThread {
                            textMotion.text = getString(R.string.motion_format, motionDetect)
                        }
                    }
                }
                response.close()
            }
        })
    }

    private fun startVideoStream() {
        isStreaming = true
        val url = "http://$piHost:5000/video_feed"
        val request = Request.Builder()
            .url(url)
            .addHeader("X-API-KEY", apiKey)
            .build()

        client.newCall(request).enqueue(object : Callback {
            override fun onFailure(call: Call, e: IOException) {
                Log.e("MainActivity", "Video stream failed", e)
            }

            override fun onResponse(call: Call, response: Response) {
                if (!response.isSuccessful) {
                    response.close()
                    return
                }
                val source = response.body?.source() ?: return

                // JPEG Magic bytes: Start of Image (SOI) and End of Image (EOI)
                val soi = ByteString.of(0xFF.toByte(), 0xD8.toByte())
                val eoi = ByteString.of(0xFF.toByte(), 0xD9.toByte())

                try {
                    while (isStreaming && !source.exhausted()) {
                        // 1. Skip any text headers (Content-Type, Content-Length) and find the JPEG start
                        val soiIndex = source.indexOf(soi)
                        if (soiIndex == -1L) break // Stream ended or no more frames
                        source.skip(soiIndex) // Jump directly to the start of the JPEG image

                        // 2. Find where this JPEG ends
                        val eoiIndex = source.indexOf(eoi)
                        if (eoiIndex == -1L) break // Incomplete frame at the end of the stream

                        // The length of the frame is the distance to EOI plus the 2 bytes of the EOI marker itself
                        val frameLength = eoiIndex + 2

                        // 3. Read the exact frame bytes safely into a byte array
                        val jpegBytes = source.readByteArray(frameLength)

                        // 4. Decode the raw bytes (this will now succeed!)
                        val bitmap = BitmapFactory.decodeByteArray(jpegBytes, 0, jpegBytes.size)

                        if (bitmap != null) {
                            runOnUiThread {
                                imageVideo.setImageBitmap(bitmap)
                            }
                        }
                    }
                } catch (e: Exception) {
                    Log.e("MainActivity", "Video parsing failed", e)
                } finally {
                    response.close()
                }
            }

        })
    }
}
