# Mobile Outlook Agent

Automated Outlook account creation using LangGraph agents and Appium mobile automation.

## 🎯 Features

- **LangGraph Agent**: Orchestrates the complete Outlook creation workflow
- **Generic Tools**: Reusable UI automation tools for mobile apps
- **Bulletproof Patterns**: Based on proven automation techniques from comp.py
- **Special Handling**: CAPTCHA long press, authentication wait, year field edge cases
- **FastAPI Backend**: REST API for testing and integration
- **SQLite Database**: Stores created accounts and process logs

## 🏗️ Architecture

```
Mobile Outlook Agent
├── 🤖 LangGraph Agent (Workflow Orchestration)
├── 🔧 Generic UI Tools (Reusable Across Apps)  
├── 📱 Appium Driver (Mobile Automation)
├── 🌐 FastAPI Backend (REST API)
└── 🗄️ SQLite Database (Data Storage)
```

## 📋 Prerequisites

1. **Appium Server**
   ```bash
   npm install -g appium
   appium driver install uiautomator2
   appium  # Start server on localhost:4723
   ```

2. **Android Device/Emulator**
   - USB debugging enabled
   - Outlook app installed
   - Connected via ADB: `adb devices`

3. **Python 3.8+**
   ```bash
   pip install -r requirements.txt
   ```

## 🚀 Quick Start

### 1. Test Connection
```bash
python main.py --mode test
```

### 2. Run Demo Automation
```bash
python main.py --mode demo
```

### 3. Start API Server
```bash
python main.py --mode server
# Server runs on http://localhost:8000
```

### 4. Manual Automation
```bash
python main.py --mode manual \
  --first-name "John" \
  --last-name "Smith" \
  --date-of-birth "1995-05-15"
```

## 🌐 API Endpoints

### Create Outlook Account
```bash
POST /outlook/create
{
  "first_name": "John",
  "last_name": "Smith", 
  "date_of_birth": "1995-05-15",
  "curp_id": "OPTIONAL123456"
}
```

### Demo Automation
```bash
POST /outlook/demo
{
  "count": 1
}
```

### Check Status
```bash
GET /outlook/status/{process_id}
```

### Get All Accounts
```bash
GET /outlook/accounts
```

### View Logs
```bash
GET /outlook/logs
```

## 🔧 Workflow Steps

1. **Welcome** - Tap "CREATE NEW ACCOUNT" 
2. **Email** - Type generated username
3. **Password** - Type secure password
4. **Details** - Select day/month, type year (special backspace handling)
5. **Name** - Type first and last name
6. **CAPTCHA** - 15-second long press with native gesture + ADB fallback
7. **Auth Wait** - Monitor progress bars until authentication completes  
8. **Post-Auth** - Fast navigation through setup pages to inbox
9. **Verify** - Confirm inbox is visible

## 🛠️ Generic Tools

### UI Automation (`tools/mobile_ui.py`)
- `ui_find_elements()` - Bulletproof element finding with stale element handling
- `ui_click()` - Robust clicking with retries and fresh element lookup
- `ui_type_text()` - Smart text input with field-type awareness (year field uses backspace)
- `ui_select_dropdown()` - Dropdown selection with option handling
- `ui_wait_element()` - Element presence/visibility waiting

### Gestures (`tools/gestures.py`)  
- `ui_long_press()` - Native gesture + ADB fallback for CAPTCHA (15s hold)
- `ui_swipe()` - Screen swiping and scrolling
- `ui_scroll_up/down()` - Directional scrolling

### Authentication (`tools/auth_wait.py`)
- `ui_wait_progress_gone()` - Monitor progress bars during authentication
- `ui_wait_loading_gone()` - Wait for various loading indicators
- `ui_wait_text_present/gone()` - Text-based waiting

### Post-Auth Navigation (`tools/post_auth.py`)
- `post_auth_fast_path()` - Time-bounded navigation through setup pages
- `navigate_to_inbox_simple()` - Fallback navigation method

## 📊 Error Handling

- **Retry Logic**: 3 attempts per step with exponential backoff
- **Checkpoint System**: State restoration on step failures  
- **ADB Fallbacks**: Alternative input methods when Appium fails
- **Coordinate Fallbacks**: Screen coordinate taps when element selection fails
- **Graceful Degradation**: Continue workflow even if non-critical steps fail

## 🧪 Testing

### End-to-End Test
```bash
# Run complete workflow test
python main.py --mode demo

# Test specific components
python main.py --mode test
```

### Custom Test Data
```bash
python main.py --mode manual \
  --first-name "TestUser" \
  --last-name "Demo" \
  --date-of-birth "1990-01-01" \
  --curp-id "TEST123456HDEMO01"
```

## 📁 Project Structure

```
outlook-mobile-agent/
├── tools/                    # Generic UI automation tools
│   ├── mobile_ui.py         # Core UI interactions
│   ├── gestures.py          # Long press, swipe, tap
│   ├── auth_wait.py         # Authentication waiting
│   ├── post_auth.py         # Post-auth navigation
│   └── selectors.py         # Outlook element selectors
│
├── agent/                    # LangGraph agent
│   ├── graph.py             # Agent workflow definition
│   └── state.py             # Agent state management
│
├── drivers/                  # Appium driver setup
│   └── appium_client.py     # Driver lifecycle management
│
├── backend/                  # FastAPI backend
│   └── main.py              # REST API endpoints
│
├── data/                     # Constants and test data
│   └── constants.py         # Names, dates, sample data
│
├── main.py                   # Main runner script
├── requirements.txt          # Python dependencies
└── README.md                # This file
```

## 🔍 Troubleshooting

### Appium Connection Issues
```bash
# Check device connection
adb devices

# Restart ADB server  
adb kill-server && adb start-server

# Check Appium server
curl http://localhost:4723/status
```

### Element Not Found
- Check if app UI has changed
- Update selectors in `tools/selectors.py`
- Use coordinate fallbacks for unstable elements

### Year Field Issues
- Year field uses backspace clearing to avoid ACTION_SET_PROGRESS errors
- If typing fails, fallback methods include ADB input and direct element manipulation

### CAPTCHA Problems
- Ensure 15-second long press duration is sufficient
- Check native gesture support on device
- ADB fallback should handle most gesture failures

## 🎯 Next Steps

This Mobile Outlook Agent provides the foundation for:

1. **IMSS Integration** - Same tools can automate IMSS app forms
2. **Web Expansion** - Platform-aware tools support browser automation
3. **Multi-App Workflows** - Chain Outlook → IMSS → Email monitoring
4. **Scaling** - Deploy multiple agents with load balancing

The generic tools and patterns established here are reusable across any mobile app automation needs.

## 🤝 Contributing

1. Keep tools generic and reusable
2. Add comprehensive error handling  
3. Include fallback strategies for reliability
4. Document selector strategies for new apps
5. Test on multiple devices and Android versions

## 📄 License

This project is for educational and automation purposes.
