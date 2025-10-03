"""
Video analysis module for extracting metadata and calculating watermark positions.

This module provides functionality to analyze video files and determine properties
such as FPS, resolution, duration, and orientation. It also calculates the dynamic
watermark position timeline based on a 2.3-second interval pattern.
"""

from dataclasses import dataclass
from typing import Tuple, List
import cv2
import math


@dataclass
class VideoMetadata:
    """
    Container for video file metadata.

    Attributes:
        width: Video width in pixels
        height: Video height in pixels
        fps: Frames per second
        total_frames: Total number of frames in video
        duration: Video duration in seconds
        orientation: Video orientation ('landscape', 'portrait', or 'square')
        codec: Video codec identifier
    """

    width: int
    height: int
    fps: float
    total_frames: int
    duration: float
    orientation: str
    codec: str


@dataclass
class WatermarkPosition:
    """
    Defines a watermark region with coordinates and dimensions.

    Attributes:
        x: X-coordinate of top-left corner
        y: Y-coordinate of top-left corner
        width: Width of watermark region
        height: Height of watermark region
    """

    x: int
    y: int
    width: int
    height: int


class VideoAnalyzer:
    """
    Analyzes video files to extract metadata and calculate watermark positions.
    """

    POSITION_COUNT = 3
    CYCLE_FRAMES = 227

    def __init__(self, video_path: str):
        """
        Initialize analyzer with video file path.

        Args:
            video_path: Path to the video file to analyze

        Raises:
            ValueError: If video file cannot be opened
        """
        self.video_path = video_path
        self.cap = cv2.VideoCapture(video_path)

        if not self.cap.isOpened():
            raise ValueError(f"Cannot open video file: {video_path}")

    def analyze(self) -> VideoMetadata:
        """
        Extract complete metadata from the video file.

        Returns:
            VideoMetadata object containing all video properties
        """
        width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = self.cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = total_frames / fps if fps > 0 else 0
        codec = int(self.cap.get(cv2.CAP_PROP_FOURCC))

        orientation = self._determine_orientation(width, height)

        return VideoMetadata(
            width=width,
            height=height,
            fps=fps,
            total_frames=total_frames,
            duration=duration,
            orientation=orientation,
            codec=self._decode_fourcc(codec),
        )

    def get_watermark_positions(
        self, metadata: VideoMetadata, wm_width: int = 139, wm_height: int = 51
    ) -> List[WatermarkPosition]:
        """
        Calculate the three watermark positions with exact pixel coordinates.

        Positions:
        - Position 0: Top-left (x=20, y=75)
        - Position 1: Center-right (x=video_width-width-10, y=592)
        - Position 2: Bottom-left (x=32, y=video_height-195)

        Args:
            metadata: Video metadata containing width and height
            wm_width: Watermark width in pixels (default: 139)
            wm_height: Watermark height in pixels (default: 51)

        Returns:
            List of three WatermarkPosition objects
        """
        w, h = metadata.width, metadata.height
        left_margin_top = 20
        left_margin_bottom = 25
        right_margin = 10
        top_offset = 75
        center_y = 592
        bottom_offset = 260

        positions = [
            WatermarkPosition(
                x=left_margin_top, y=top_offset, width=wm_width, height=wm_height
            ),
            WatermarkPosition(
                x=w - wm_width - right_margin,
                y=center_y,
                width=wm_width,
                height=wm_height,
            ),
            WatermarkPosition(
                x=left_margin_bottom,
                y=h - bottom_offset,
                width=wm_width,
                height=wm_height,
            ),
        ]

        return positions

    def get_position_index_for_frame(self, frame_number: int, fps: float) -> int:
        """
        Determine which watermark position should be active for a given frame.

        Frame-based position pattern (227-frame cycle):
        - Position 0 (Top-left): Frames 0-65 (66 frames)
        - Position 1 (Center-right): Frames 66-145 (80 frames)
        - Position 2 (Bottom-left): Frames 146-226 (81 frames)

        Args:
            frame_number: Current frame number (0-indexed)
            fps: Frames per second (unused, kept for API compatibility)

        Returns:
            Position index (0, 1, or 2)
        """
        cycle_frame = frame_number % self.CYCLE_FRAMES

        if cycle_frame < 66:
            return 0
        elif cycle_frame < 146:
            return 1
        else:
            return 2

    def _determine_orientation(self, width: int, height: int) -> str:
        """
        Determine video orientation based on aspect ratio.

        Args:
            width: Video width in pixels
            height: Video height in pixels

        Returns:
            Orientation string: 'landscape', 'portrait', or 'square'
        """
        if width > height:
            return "landscape"
        elif height > width:
            return "portrait"
        else:
            return "square"

    def _decode_fourcc(self, fourcc: int) -> str:
        """
        Decode FOURCC code to human-readable codec string.

        Args:
            fourcc: FOURCC integer code

        Returns:
            Codec string (e.g., 'H264', 'VP9')
        """
        try:
            return "".join([chr((fourcc >> 8 * i) & 0xFF) for i in range(4)])
        except Exception:
            return "UNKNOWN"

    def release(self):
        """
        Release video capture resources.
        """
        if self.cap:
            self.cap.release()

    def __enter__(self):
        """
        Context manager entry.
        """
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Context manager exit with automatic resource cleanup.
        """
        self.release()
