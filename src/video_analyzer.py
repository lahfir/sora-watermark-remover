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

    WATERMARK_INTERVAL = 2.5
    POSITION_COUNT = 3

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
            codec=self._decode_fourcc(codec)
        )

    def get_watermark_positions(
        self,
        metadata: VideoMetadata,
        wm_width: int = 139,
        wm_height: int = 51
    ) -> List[WatermarkPosition]:
        """
        Calculate the three watermark positions with exact pixel coordinates.

        Positions:
        - Position 0: Top-left (x=32, y=85)
        - Position 1: Center-right (x=video_width-width-32, y=602)
        - Position 2: Bottom-left (x=32, y=video_height-193)

        Args:
            metadata: Video metadata containing width and height
            wm_width: Watermark width in pixels (default: 139)
            wm_height: Watermark height in pixels (default: 51)

        Returns:
            List of three WatermarkPosition objects
        """
        w, h = metadata.width, metadata.height
        left_margin = 32
        right_margin = 32
        top_offset = 85
        center_y = 602
        bottom_offset = 193

        positions = [
            WatermarkPosition(
                x=left_margin,
                y=top_offset,
                width=wm_width,
                height=wm_height
            ),
            WatermarkPosition(
                x=w - wm_width - right_margin,
                y=center_y,
                width=wm_width,
                height=wm_height
            ),
            WatermarkPosition(
                x=left_margin,
                y=h - bottom_offset,
                width=wm_width,
                height=wm_height
            )
        ]

        return positions

    def get_position_index_for_frame(self, frame_number: int, fps: float) -> int:
        """
        Determine which watermark position should be active for a given frame.

        Args:
            frame_number: Current frame number (0-indexed)
            fps: Frames per second of the video

        Returns:
            Position index (0, 1, or 2)
        """
        timestamp = frame_number / fps
        position_cycle = math.floor(timestamp / self.WATERMARK_INTERVAL)
        return position_cycle % self.POSITION_COUNT

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
