# Desktop AI

A local, browser-based desktop agent for Linux Mint X11 using NVIDIA NIM.

## Features
- Live chat interface; new instructions are queued into the current task.
- Screenshot-based vision.
- Tool-calling agent loop.
- Independent XInput master pointer (separate from the physical mouse).
- Stop button releases held inputs.
- Runs locally; NVIDIA NIM receives screenshots and conversation content.

## Requirements
Linux Mint Cinnamon on X11, Python 3, an NVIDIA NIM API key, and a vision-capable NIM model that supports tool calling and image input.

## Install
```bash
git clone https://github.com/elithenpc/desktop-ai.git ~/desktop-ai
cd ~/desktop-ai
bash install.sh
```

Edit `~/.config/desktop-ai/env`, add your API key, then run:
```bash
~/desktop-ai/run.sh
```
Open http://127.0.0.1:8766.

## Important
This is an early implementation. Verify that the model configured in NVIDIA NIM supports both image inputs and tool calling. Screen captures are sent to NVIDIA's API. The app binds only to localhost. Do not use it to enter credentials or perform sensitive actions. Stop the agent before using the computer normally.

Current limitation: the agent sends a fresh screenshot when it calls `see_screen`; it does not continuously stream video frames to the model. Continuous observation is implemented as repeated screen inspection during the agent's action loop, not a constant video upload.
