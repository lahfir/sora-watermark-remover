# Sora Watermark Remover

A powerful CLI tool to remove or blur dynamic watermarks from videos. Handles watermarks that alternate between multiple positions throughout the video.

## Features

- **Dynamic Position Tracking**: Automatically handles watermarks that change position every 2.3 seconds
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

Or using the package:
```bash
pip install -e .
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

### Combined Options

```bash
python main.py input.mp4 output.mp4 -b 65 -a -p 15
```

## Options

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--blur-intensity` | `-b` | Blur kernel size (must be odd) | 51 |
| `--advanced` | `-a` | Use edge-aware blur | False |
| `--preview` | `-p` | Process only first N seconds | None |
| `--info` | `-i` | Show video info and exit | False |

## How It Works

1. **Video Analysis**: Extracts metadata (FPS, resolution, duration, orientation)
2. **Position Calculation**: Determines watermark position for each frame based on 2.3s interval
3. **Blur Application**: Applies Gaussian or bilateral blur to watermark regions
4. **Feathered Blending**: Uses smooth edge transitions for natural appearance
5. **Video Encoding**: Outputs processed video with original quality settings

## Watermark Positions

The tool automatically calculates three positions based on your video dimensions:

- **Position 0** (0.0-2.3s): Top-left corner
- **Position 1** (2.3-4.6s): Center-right
- **Position 2** (4.6-6.9s): Bottom-left
- *Repeats...*

Each position is sized at approximately 15% of video width and 8% of video height.

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
├── pyproject.toml
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
