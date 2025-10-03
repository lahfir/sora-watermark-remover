"""
Watermark processing module for applying adaptive blur to video regions.

This module handles frame-by-frame video processing, applying Gaussian blur
to watermark regions that change position dynamically throughout the video.
"""

import cv2
import numpy as np
import subprocess
import tempfile
import os
from typing import Optional, Callable
from pathlib import Path

from src.video_analyzer import VideoAnalyzer, VideoMetadata, WatermarkPosition


class WatermarkProcessor:
    """
    Processes video files to blur watermarks at dynamic positions.
    """

    def __init__(
        self,
        input_path: str,
        output_path: str,
        blur_intensity: int = 51,
        preview_duration: Optional[float] = None,
        wm_width: int = 139,
        wm_height: int = 51
    ):
        """
        Initialize the watermark processor.

        Args:
            input_path: Path to input video file
            output_path: Path to output video file
            blur_intensity: Kernel size for Gaussian blur (must be odd)
            preview_duration: If set, only process first N seconds
            wm_width: Watermark width in pixels
            wm_height: Watermark height in pixels

        Raises:
            ValueError: If blur_intensity is not a positive odd number
        """
        if blur_intensity <= 0 or blur_intensity % 2 == 0:
            raise ValueError("Blur intensity must be a positive odd number")

        self.input_path = input_path
        self.output_path = output_path
        self.blur_intensity = blur_intensity
        self.preview_duration = preview_duration
        self.wm_width = wm_width
        self.wm_height = wm_height

    def process(self, progress_callback: Optional[Callable[[int, int], None]] = None):
        """
        Process the video and apply blur to watermark regions.

        Preserves audio from the original video.

        Args:
            progress_callback: Optional callback function(current_frame, total_frames)

        Raises:
            RuntimeError: If video processing fails
        """
        temp_video = tempfile.mktemp(suffix='_video_only.mp4')

        try:
            with VideoAnalyzer(self.input_path) as analyzer:
                metadata = analyzer.analyze()
                positions = analyzer.get_watermark_positions(metadata, self.wm_width, self.wm_height)

                cap = cv2.VideoCapture(self.input_path)

                if not cap.isOpened():
                    raise RuntimeError(f"Failed to open video: {self.input_path}")

                fourcc = cv2.VideoWriter_fourcc(*'avc1')
                out = cv2.VideoWriter(
                    temp_video,
                    fourcc,
                    metadata.fps,
                    (metadata.width, metadata.height)
                )

                if not out.isOpened():
                    cap.release()
                    raise RuntimeError(f"Failed to create output video: {temp_video}")

                total_frames = metadata.total_frames
                if self.preview_duration:
                    total_frames = min(
                        total_frames,
                        int(self.preview_duration * metadata.fps)
                    )

                frame_number = 0

                try:
                    while frame_number < total_frames:
                        ret, frame = cap.read()

                        if not ret:
                            break

                        position_idx = analyzer.get_position_index_for_frame(
                            frame_number,
                            metadata.fps
                        )
                        current_position = positions[position_idx]

                        blurred_frame = self._apply_blur_to_region(
                            frame,
                            current_position
                        )

                        out.write(blurred_frame)

                        if progress_callback:
                            progress_callback(frame_number + 1, total_frames)

                        frame_number += 1

                finally:
                    cap.release()
                    out.release()

            self._merge_audio(temp_video, self.input_path, self.output_path)

        finally:
            if os.path.exists(temp_video):
                os.remove(temp_video)

    def _merge_audio(self, video_file: str, audio_source: str, output_file: str):
        """
        Merge audio from source video with processed video using FFmpeg.

        Uses high-quality H.264 encoding with CRF 18 for near-lossless quality.

        Args:
            video_file: Path to processed video (no audio)
            audio_source: Path to original video (with audio)
            output_file: Path to final output video
        """
        ffmpeg_cmd = [
            'ffmpeg', '-y',
            '-i', video_file,
            '-i', audio_source,
            '-map', '0:v:0',
            '-map', '1:a:0?',
            '-c:v', 'libx264',
            '-crf', '18',
            '-preset', 'slow',
            '-c:a', 'aac',
            '-b:a', '320k',
            '-shortest',
            output_file
        ]

        try:
            subprocess.run(ffmpeg_cmd, check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"FFmpeg audio merge failed: {e.stderr}")

    def _apply_blur_to_region(
        self,
        frame: np.ndarray,
        position: WatermarkPosition
    ) -> np.ndarray:
        """
        Apply Gaussian blur to a specific region of the frame.

        Uses a smooth transition at edges for better blending.

        Args:
            frame: Input video frame
            position: Watermark position defining the region to blur

        Returns:
            Frame with blurred watermark region
        """
        result = frame.copy()

        x, y = position.x, position.y
        w, h = position.width, position.height

        y_end = min(y + h, frame.shape[0])
        x_end = min(x + w, frame.shape[1])

        if y_end <= y or x_end <= x:
            return result

        roi = frame[y:y_end, x:x_end]

        blurred_roi = cv2.GaussianBlur(
            roi,
            (self.blur_intensity, self.blur_intensity),
            0
        )

        mask = self._create_feathered_mask(
            roi.shape[1],
            roi.shape[0],
            feather_size=10
        )

        for c in range(3):
            result[y:y_end, x:x_end, c] = (
                blurred_roi[:, :, c] * mask +
                roi[:, :, c] * (1 - mask)
            )

        return result

    def _create_feathered_mask(
        self,
        width: int,
        height: int,
        feather_size: int = 10
    ) -> np.ndarray:
        """
        Create a feathered mask for smooth blending at region edges.

        The mask has values from 0 (no blur) at edges to 1 (full blur) at center.

        Args:
            width: Mask width in pixels
            height: Mask height in pixels
            feather_size: Size of the feathering transition in pixels

        Returns:
            2D numpy array with values between 0 and 1
        """
        mask = np.ones((height, width), dtype=np.float32)

        for i in range(feather_size):
            alpha = i / feather_size

            if i < height and i < width:
                mask[i, :] *= alpha
                mask[-(i+1), :] *= alpha
                mask[:, i] *= alpha
                mask[:, -(i+1)] *= alpha

        return mask


class AdvancedWatermarkProcessor(WatermarkProcessor):
    """
    Advanced processor with edge-aware blur for better quality.

    Uses bilateral filtering to preserve edges while blurring watermarks.
    """

    def _apply_blur_to_region(
        self,
        frame: np.ndarray,
        position: WatermarkPosition
    ) -> np.ndarray:
        """
        Apply edge-aware bilateral blur to watermark region.

        Args:
            frame: Input video frame
            position: Watermark position defining the region to blur

        Returns:
            Frame with blurred watermark region
        """
        result = frame.copy()

        x, y = position.x, position.y
        w, h = position.width, position.height

        y_end = min(y + h, frame.shape[0])
        x_end = min(x + w, frame.shape[1])

        if y_end <= y or x_end <= x:
            return result

        roi = frame[y:y_end, x:x_end]

        blurred_roi = cv2.bilateralFilter(
            roi,
            d=9,
            sigmaColor=75,
            sigmaSpace=75
        )

        for _ in range(2):
            blurred_roi = cv2.GaussianBlur(
                blurred_roi,
                (self.blur_intensity, self.blur_intensity),
                0
            )

        mask = self._create_feathered_mask(
            roi.shape[1],
            roi.shape[0],
            feather_size=15
        )

        for c in range(3):
            result[y:y_end, x:x_end, c] = (
                blurred_roi[:, :, c] * mask +
                roi[:, :, c] * (1 - mask)
            )

        return result
