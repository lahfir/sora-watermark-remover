# Sora Watermark Remover

A powerful CLI tool to remove or blur dynamic watermarks from videos. Handles watermarks that alternate between multiple positions throughout the video.

## Features

- **Dynamic Position Tracking**: Automatically handles watermarks that change position every 2.5 seconds
- **Three Position Support**: Top-left → Center-right → Bottom-left
- **Smart Blur**: Gaussian blur with feathered edges for seamless blending
- **Advanced Mode**: Edge-aware bilateral filtering for better quality
- **Preview Mode**: Test on first N seconds before processing full video
- **Progress Tracking**: Real-time progress bar with elapsed time
- **Video Analysis**: Get detailed video metadata before processing

## Installation

### Prerequisites

- Python 3.10 or higher
- FFmpeg (must be installed on your system)

### Install FFmpeg

**macOS:**

```bash
brew install ffmpeg
```

**Ubuntu/Debian:**

```bash
sudo apt update
sudo apt install ffmpeg
```

**Windows:**
Download from [ffmpeg.org](https://ffmpeg.org/download.html)

### Install the Tool

```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage

```bash
python main.py input.mp4 output.mp4
```

### With Custom Blur Intensity

```bash
python main.py input.mp4 output.mp4 --blur-intensity 75
```

### Advanced Mode (Better Quality)

```bash
python main.py input.mp4 output.mp4 --advanced
```

### Preview Mode (First 10 Seconds)

```bash
python main.py input.mp4 output.mp4 --preview 10
```

### Show Video Information

```bash
python main.py input.mp4 output.mp4 --info
```

### Custom Dimensions and Blur

```bash
python main.py input.mp4 output.mp4 -w 180 -h 65 -b 75
```

### Combined Options

```bash
python main.py input.mp4 output.mp4 -b 65 -a -p 15
```

## Options

| Option             | Short | Description                    | Default |
| ------------------ | ----- | ------------------------------ | ------- |
| `--blur-intensity` | `-b`  | Blur kernel size (must be odd) | 51      |
| `--width`          | `-w`  | Watermark width in pixels      | 139     |
| `--height`         | `-h`  | Watermark height in pixels     | 51      |
| `--advanced`       | `-a`  | Use edge-aware blur            | False   |
| `--preview`        | `-p`  | Process only first N seconds   | None    |
| `--info`           | `-i`  | Show video info and exit       | False   |

## How It Works

1. **Video Analysis**: Extracts metadata (FPS, resolution, duration, orientation)
2. **Position Calculation**: Determines watermark position for each frame based on 2.5s interval
3. **Blur Application**: Applies Gaussian or bilateral blur to watermark regions
4. **Feathered Blending**: Uses smooth edge transitions for natural appearance
5. **Video Encoding**: Outputs processed video with original quality settings

## Watermark Positions

The tool uses precise pixel coordinates for watermark detection:

- **Position 0** (0.0-2.5s): Top-left at x=32, y=85
- **Position 1** (2.5-5.0s): Center-right at x=(width-171), y=602
- **Position 2** (5.0-7.5s): Bottom-left at x=32, y=(height-193)
- _Repeats every 7.5 seconds..._

Default watermark dimensions are **139×51 pixels** (customizable via `--width` and `--height`):

- **Left positions**: 32px from left edge
- **Top position**: 85px from top
- **Bottom position**: 193px from bottom
- **Right position**: 32px from right edge, 602px from top

## Architecture

```
sora-watermark-remover/
├── src/
│   ├── __init__.py
│   ├── video_analyzer.py      # Video metadata extraction
│   ├── watermark_processor.py # Blur application logic
│   └── cli.py                 # Command-line interface
├── main.py                    # Entry point
├── requirements.txt
└── README.md
```

## Examples

### Quick Test

```bash
python main.py sample.mp4 test.mp4 -p 5
```

### High Quality Processing

```bash
python main.py input.mp4 output.mp4 -b 75 --advanced
```

### Check Video First

```bash
python main.py input.mp4 output.mp4 --info
```

## Troubleshooting

**Error: "Blur intensity must be a positive odd number"**

- Use odd numbers only: 51, 75, 101, etc.

**Error: "Cannot open video file"**

- Check if FFmpeg is installed: `ffmpeg -version`
- Verify file exists and is a valid video format

**Output quality is poor**

- Try `--advanced` mode for better edge preservation
- Increase blur intensity for stronger effect
- Decrease blur intensity for more subtle effect

## Performance

- **Standard Mode**: ~30-60 FPS processing speed
- **Advanced Mode**: ~15-30 FPS (slower but better quality)
- Preview mode recommended for testing settings

## License

MIT License - Feel free to use and modify

## Contributing

Issues and pull requests welcome!
