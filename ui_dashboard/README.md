# Security Dashboard UI

A PyQt5-based desktop application for monitoring and controlling your Raspberry Pi security system.

## Features

- **Live Video Stream**: Display MJPEG video feed from the Pi camera
- **Motion Detection**: Real-time motion detection indicator
- **Environmental Monitoring**: Temperature and humidity readings
- **Camera Control**: Start/stop the camera remotely
- **Connection Management**: Configure server URL and API key
- **Status Display**: Real-time connection and system status
- **Responsive UI**: Background threading ensures smooth user experience

## Requirements

- Python 3.7+
- PyQt5
- requests
- Pillow
- python-dotenv

## Installation

1. Clone or download this package to your workspace:
   ```bash
   cd d:\projects\python\security
   ```

2. Install dependencies:
   ```bash
   pip install -r ui_dashboard/requirements.txt
   ```

3. Configure connection settings (choose one method):

   **Option A: Environment Variables**
   ```bash
   set SECURITY_SERVER_URL=http://192.168.1.100:5000
   set SECURITY_API_KEY=your_api_key_here
   ```

   **Option B: .env File**
   ```bash
   cp ui_dashboard/.env.example ~/.security_dashboard/.env
   # Edit ~/.security_dashboard/.env with your settings
   ```

   **Option C: Settings Dialog**
   - Run the application and configure through the Settings panel

## Usage

### Running the Application

From the workspace root:
```bash
python -m ui_dashboard.main
```

Or from the ui_dashboard directory:
```bash
python main.py
```

### First Run

1. Application will prompt for server connection if not configured
2. Enter your Pi Server URL (e.g., `http://192.168.1.100:5000`)
3. Enter your API key (from pi_server config)
4. Click "Connect & Save"

### Dashboard Interface

- **Video Display**: Shows live MJPEG stream from the Pi camera
- **Motion Indicator**: 
  - Green: No motion detected
  - Red: Motion detected
  - Gray: Disconnected
- **Camera Control Button**: 
  - Click "Start Camera" to enable camera streaming
  - Click "Stop Camera" to disable camera
- **Status Panel**: Shows temperature, humidity, and connection status
- **Settings Button**: Reconfigure server connection
- **Refresh Button**: Force refresh of all status data

## Configuration

### Server URL Format
```
http://192.168.1.100:5000
https://security.example.com
http://localhost:5000
```

### API Key
- Must match the `PI_SERVER_API_KEY` environment variable on your pi_server
- Can be found in `pi_server/config.py`

### Storage Location
Configuration is stored in:
- Linux/Mac: `~/.security_dashboard/.env`
- Windows: `C:\Users\<username>\.security_dashboard\.env`

## Architecture

### Components

1. **api_client.py**: REST API client for communicating with pi_server
   - Handles authentication via X-API-KEY header
   - Implements retry logic with exponential backoff
   - Manages MJPEG stream parsing

2. **config.py**: Configuration management
   - Load/save settings from .env
   - Environment variable fallback
   - Configuration validation

3. **ui/main_window.py**: Main application window
   - Layout and widget management
   - Background thread orchestration
   - Event handling

4. **ui/widgets.py**: Reusable UI components
   - VideoStreamWidget: MJPEG frame display
   - MotionIndicatorWidget: Motion status indicator
   - TemperatureHumidityWidget: Environmental data display
   - StatusLabel: Connection status and update time
   - CameraControlButton: Camera on/off control

5. **ui/styles.py**: PyQt5 stylesheets and styling utilities

### Threading Model

- **Status Poller Thread**: Polls `/status` endpoint every 2 seconds
- **Video Stream Thread**: Continuously fetches and decodes MJPEG frames
- **Main Thread**: PyQt5 event loop and UI updates (safe via Qt signals)

### API Endpoints Used

- `GET /status` → Full system status (temperature, humidity, motion, camera_enabled)
- `GET /video_feed` → MJPEG video stream
- `POST /camera/start` → Enable camera
- `POST /camera/stop` → Disable camera
- `GET /health` → Connection health check

## Troubleshooting

### "Unable to connect to server"
- Verify server URL is correct (no trailing slash)
- Check that pi_server is running
- Verify API key matches pi_server configuration
- Check firewall/network connectivity

### Video stream not displaying
- Ensure camera is enabled via "Start Camera" button
- Check that `/video_feed` endpoint is accessible
- Verify camera hardware on Pi is working

### High CPU usage
- UI may display every frame (640x480, 24 FPS = high bandwidth)
- Consider reducing camera FPS on pi_server: `CAMERA_FPS` environment variable
- Or resize the video widget to display lower resolution

### Motion indicator not updating
- Check that motion sensor is connected to Pi (GPIO pin configured in pi_server)
- Verify `PIR_PIN` in pi_server config matches your hardware

## Development

### Project Structure
```
ui_dashboard/
├── __init__.py
├── main.py                  # Entry point
├── api_client.py            # REST API client
├── config.py                # Configuration management
├── requirements.txt
├── README.md
├── .env.example
└── ui/
    ├── __init__.py
    ├── main_window.py       # Main window
    ├── widgets.py           # Reusable components
    └── styles.py            # Styling
```

### Adding New Features

1. **New Status Fields**: Update `api_client.py` and dashboard widgets
2. **New Endpoints**: Add methods to `SecurityAppClient` class
3. **UI Changes**: Modify `ui/main_window.py` and widgets
4. **Styling**: Update `ui/styles.py` stylesheets

## Future Enhancements

- [ ] Motion detection event history log
- [ ] Customizable update intervals
- [ ] Snapshot/recording functionality
- [ ] Push notifications for motion alerts
- [ ] Multi-camera support
- [ ] Dark mode theme
- [ ] System tray integration

## License

[Your License Here]

## Support

For issues or questions, check pi_server README and configuration documentation.
