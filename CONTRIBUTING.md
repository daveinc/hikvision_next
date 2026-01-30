# Contributing to Hikvision Next (Enhanced Fork)

Thanks for your interest in contributing! 🎉

This is a community-maintained fork of the original [maciej-or/hikvision_next](https://github.com/maciej-or/hikvision_next) repository, created to provide bug fixes and improvements while the original repository appears unmaintained.

---

## 🐛 Reporting Bugs

1. Check [existing issues](https://github.com/YOUR_USERNAME/hikvision_next/issues) first
2. Include:
   - Your Hikvision device model
   - Firmware version
   - Home Assistant version
   - Full error logs from Home Assistant
   - Steps to reproduce

## 💡 Suggesting Features

Open an issue with:
- Clear description of the feature
- Why it would be useful
- Example use case
- Whether this feature exists in the original integration or is new

---

## 🔧 Code Contributions

### Pull Request Guidelines

- Pull requests should be created against the **main** branch (or **dev** branch if you maintain one)
- Code must follow [Home Assistant code style guidelines](https://developers.home-assistant.io/docs/development_guidelines)
- Line length limit must be 120 characters
- Install Ruff extension and select ruff as default formatter in VS Code settings

### Testing Checklist

Before submitting a PR, verify:
- [ ] No errors in Home Assistant logs
- [ ] Binary sensors respond instantly
- [ ] Camera entities still work (if applicable)
- [ ] Integration loads after Home Assistant restart
- [ ] Multiple cameras work correctly
- [ ] Other event types (line crossing, field detection) still function
- [ ] Unit tests pass (see Testing section below)

### Code Style

- Follow the existing code style
- Add comments for complex logic
- Update CHANGELOG.md with your changes
- Add unit tests for new functionality if possible

---

## 🧪 Development Environment

### Option 1: DevContainer (Recommended)

1. Set up devcontainer using guide at https://developers.home-assistant.io/docs/development_environment/
2. Mount the integration repo in `.devcontainer/devcontainer.json`:
```json
{
  "mounts": [
    "source=/path/on/your/disk/hikvision_next/custom_components/hikvision_next,
    target=${containerWorkspaceFolder}/config/custom_components/hikvision_next,
    type=bind"
  ]
}
```
3. Run / Start Debugging

**NOTE:** The first container build and Home Assistant launch may take longer.

### Option 2: Manual Setup

1. Clone your fork locally
2. Edit files in `custom_components/hikvision_next/`
3. Copy to your Home Assistant `config/custom_components/` directory
4. Restart Home Assistant
5. Test your changes

---

## 🧪 Test Environment

### Setup

Install Python 3.12 or later and project dependencies:
```bash
pip install -r requirements.test.txt
```

Run tests:
```bash
pytest
```

For running tests in debug mode, VS Code is recommended.

### Test Types

#### 1. ISAPI Communication Tests
These test specific ISAPI requests and use data from `tests/fixtures/ISAPI`. They focus on data processing. The folder structure corresponds to ISAPI endpoints, and the XML files contain device responses.

#### 2. Device Behavior Tests
These initialize the entire device in the Home Assistant environment and use data from `tests/fixtures/devices`. Each JSON file contains all the responses to GET requests sent by the given device.

**Creating Fixtures:**
Fixtures can be recorded for any device in the Device Info window by clicking **DOWNLOAD DIAGNOSTICS** button. All sensitive data such as MAC addresses, IPs, and serial numbers are anonymized so they can be safely made public.

This approach makes it easier to develop this integration for a greater number of devices without physical access to the device.

---

## 🪟 Testing on Windows

If you develop on Windows, there are some limitations with `pytest-homeassistant-custom-component` when running unit tests.

See this [issue](https://github.com/MatthewFlamm/pytest-homeassistant-custom-component/issues/154) for more details.

### Run Tests on Windows (Using Docker)

If you just want to run the tests, the simplest way is to use Docker:

1. Install [Docker Desktop](https://docs.docker.com/desktop/setup/install/windows-install/)

2. In a command window, run:
```cmd
REM Navigate to your hikvision_next directory. Example:
cd C:\Users\john\Documents\github\hikvision_next

REM Build a docker container
docker build -f run_test.dockerfile -t mine/pytest-homeassistant-custom-component:latest .

REM Clear console and run tests in your container
cls && docker run --rm -v .:/app mine/pytest-homeassistant-custom-component:latest
```

### Debug Tests in VS Code on Windows

If you want to debug the tests in Visual Studio Code:

1. Install [Docker Desktop](https://docs.docker.com/desktop/setup/install/windows-install/)

2. Configure VS Code tasks (in `.vscode/tasks.json`):
```json
{
    "tasks": [
        {
          "label": "docker-build phcc",
          "type": "docker-build",
          "platform": "python",
          "dockerBuild": {
            "context": "${workspaceFolder}",
            "dockerfile": "${workspaceFolder}/run_test.dockerfile",
            "tag": "minevs/pytest-homeassistant-custom-component:latest"
          }
        },
        {
            "label": "docker-run: debug",
            "type": "docker-run",
            "dependsOn": ["docker-build phcc"],
            "python": {
              "args": ["."],
              "module": "pytest"
            },
            "dockerRun": {
                "image": "minevs/pytest-homeassistant-custom-component:latest",
                "volumes": [{
                    "localPath": "${workspaceFolder}",
                    "containerPath": "/app"
                }]
            }
        }
    ]
}
```

3. Configure VS Code launcher (in `.vscode/launch.json`):
```json
{
    "version": "0.2.0",
    "configurations": [
        {
          "name": "Docker: Python tests debug",
          "type": "docker",
          "request": "launch",
          "preLaunchTask": "docker-run: debug",
          "python": {
            "pathMappings": [
              {
                "localRoot": "${workspaceFolder}",
                "remoteRoot": "/app"
              }
            ]
          }
        }
    ]
}
```

4. Add a breakpoint in your test file
5. Run the **"Docker: Python tests debug"** job in VS Code

---

## 📝 Documentation

Improvements to README, documentation, or code comments are always welcome!

### What to Document
- New features or fixes
- Configuration examples
- Troubleshooting steps
- Device compatibility information

---

## 🤝 Relationship with Original Repository

This fork maintains compatibility with the original repository's structure and conventions where possible. If the original repository becomes active again, we aim to merge improvements back upstream.

---

## ❓ Questions

Not sure about something? Open an issue and ask! No question is too simple.

---

## 🙏 Thank You

Thank you for helping improve this integration! Your contributions help the entire Home Assistant community.

**Special thanks to:**
- **maciej-or** - Original integration author
- All contributors to this fork
- The Home Assistant community
