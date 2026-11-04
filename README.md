# Desktop AI

A local, browser-based desktop agent for Linux Mint X11 using NVIDIA NIM.

## Features
- Live chat interface; new instructions are queued into the current task.
- Screenshot-based vision.
- Tool-calling agent loop.
- Independent XInput master pointer (separate from the physical mouse).
- Stop button releases held inputs.
- Quick, smooth cursor movement by default, with instant teleport on explicit request.
- Keyboard shortcuts and text entry through the independent virtual keyboard.
- Fast application launching through installed Linux desktop entries, without arbitrary shell execution.
- Familiar Linux Mint desktop context, including common applications and shortcuts.
- Runs locally; NVIDIA NIM receives screenshots and conversation content.

## Requirements
Linux Mint Cinnamon on X11, Python 3, an NVIDIA NIM API key, and a vision-capable NIM model that supports tool calling and image input. The default is `nvidia/nemotron-3.5-super-vl-120b-a12b`.

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

Current limitation: the agent captures a fresh screenshot before each model decision. It does not upload a continuous video stream; screen observation happens in discrete snapshots throughout the task.
