# Sora Watermark Remover

A powerful CLI tool to remove or blur dynamic watermarks from videos. Handles watermarks that alternate between multiple positions throughout the video.

## Features

- **Frame-Based Position Tracking**: Automatically handles watermarks that change position based on frame numbers (227-frame cycle)
- **Three Position Support**: Top-left → Center-right → Bottom-left
- **Customizable Dimensions**: Adjust watermark width and height via CLI
- **Smart Blur**: Gaussian blur with feathered edges for seamless blending
- **Advanced Mode**: Edge-aware bilateral filtering for better quality
- **Preview Mode**: Test on first N seconds before processing full video
- **Shimmer Progress UI**: Animated progress bar and text with white shimmer effects
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

### Custom Watermark Dimensions

```bash
python main.py input.mp4 output.mp4 -w 180 -h 65
```

### Strong Blur for Larger Watermarks

```bash
python main.py input.mp4 output.mp4 -w 180 -h 65 -b 101
```

### Combined Options (Advanced Mode + Preview)

```bash
python main.py input.mp4 output.mp4 -b 75 -a -p 15
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
2. **Frame-Based Position Calculation**: Determines watermark position for each frame based on 227-frame cycle
3. **Dynamic Positioning**: Calculates exact pixel coordinates for three alternating positions
4. **Blur Application**: Applies Gaussian or bilateral blur to watermark regions
5. **Feathered Blending**: Uses smooth edge transitions for natural appearance
6. **Audio Preservation**: Merges original audio back into processed video using FFmpeg

## Watermark Positions

The tool uses precise pixel coordinates and frame-based timing for watermark detection:

### Frame-Based Timing Pattern (227-frame cycle)

- **Position 0** (Frames 0-65): Top-left at x=20, y=75 — 66 frames
- **Position 1** (Frames 66-145): Center-right at x=(width-149), y=592 — 80 frames
- **Position 2** (Frames 146-226): Bottom-left at x=25, y=(height-260) — 81 frames
- _Cycle repeats from frame 227..._

### Pixel Coordinates

Default watermark dimensions are **139×51 pixels** (customizable via `--width` and `--height`):

- **Top-left position**: 20px from left, 75px from top
- **Center-right position**: 10px from right, 592px from top
- **Bottom-left position**: 25px from left, 260px from bottom (y=820 for 1080p)
- All positions dynamically adapt to video resolution

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

## Visual Features

### Shimmer Progress Effects

The tool features a beautiful animated progress display with **dual shimmer effects**:

- **Text Shimmer**: White gradient sweeps through "Processing video..." text at high speed
- **Bar Shimmer**: White scanning effect moves across the progress bar
- **Smooth Animation**: Both effects run at 10 FPS for fluid motion

### Example Output

```
⠋ Processing video... ━━━━━━━━━━━━━━━━━━━━━━━━━━━ 45% 0:01:23
```

The shimmer creates a professional, polished look while processing videos.

## Examples

### Quick Test (5 Second Preview)

```bash
python main.py sample.mp4 test.mp4 -p 5
```

### Production Quality (Large Watermark + Strong Blur)

```bash
python main.py input.mp4 output.mp4 -w 200 -h 80 -b 101 --advanced
```

### Check Video Info First

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
- Increase blur intensity for stronger effect (use odd numbers: 75, 101, 151)
- Increase watermark dimensions if it's larger: `-w 200 -h 80`
- Use preview mode to test settings before full processing: `-p 10`

**Watermark not being blurred**

- Verify watermark positions match your video
- Increase watermark width/height: `-w 180 -h 65`
- Check timing: watermarks follow a 227-frame cycle pattern
- Use `--info` to verify video dimensions

## Performance

- **Standard Mode**: ~30-60 FPS processing speed
- **Advanced Mode**: ~15-30 FPS (slower but better quality)
- **Shimmer Effects**: 10 FPS animation refresh (minimal performance impact)
- Preview mode recommended for testing settings before full processing

## Technical Details

### Watermark Detection Algorithm

The tool uses a frame-based position calculator:

```python
cycle_frame = frame_number % 227
if cycle_frame < 66:
    return 0  # Top-left
elif cycle_frame < 146:
    return 1  # Center-right
else:
    return 2  # Bottom-left
```

This ensures watermarks are detected at the correct position for each frame.

### Position Formulas (Dynamic)

- **Top-left**: `x=20, y=75`
- **Center-right**: `x=width-width_wm-10, y=592`
- **Bottom-left**: `x=25, y=height-260`

These formulas adapt to any video resolution while maintaining precise positioning.

For 1920×1080 video with 139×51px watermarks:
- **Top-left**: (20, 75) - top edge
- **Center-right**: (1771, 592) - top edge
- **Bottom-left**: (25, 820) - top edge, bottom edge at 871

## License

MIT License - Feel free to use and modify

## Contributing

Issues and pull requests welcome!
