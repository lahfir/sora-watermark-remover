"""
Command-line interface for the watermark removal tool.

Provides a user-friendly CLI with progress tracking and validation.
"""

import click
from pathlib import Path
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeElapsedColumn
from rich.panel import Panel
from rich.table import Table

from src.video_analyzer import VideoAnalyzer
from src.watermark_processor import WatermarkProcessor, AdvancedWatermarkProcessor


console = Console()


@click.command()
@click.argument('input_video', type=click.Path(exists=True, path_type=Path))
@click.argument('output_video', type=click.Path(path_type=Path))
@click.option(
    '--blur-intensity',
    '-b',
    type=int,
    default=51,
    help='Blur kernel size (must be odd, default: 51)'
)
@click.option(
    '--preview',
    '-p',
    type=float,
    default=None,
    help='Preview mode: process only first N seconds'
)
@click.option(
    '--advanced',
    '-a',
    is_flag=True,
    help='Use advanced edge-aware blur (slower but better quality)'
)
@click.option(
    '--info',
    '-i',
    is_flag=True,
    help='Show video information and exit'
)
def remove_watermark(
    input_video: Path,
    output_video: Path,
    blur_intensity: int,
    preview: float,
    advanced: bool,
    info: bool
):
    """
    Remove or blur watermarks from videos with dynamic positioning.

    Handles watermarks that alternate between three positions:
    - Top-left
    - Center-right
    - Bottom-left

    The watermark position changes every 2.3 seconds.

    Examples:
        watermark-remove input.mp4 output.mp4
        watermark-remove input.mp4 output.mp4 -b 75 --advanced
        watermark-remove input.mp4 output.mp4 -p 10
        watermark-remove input.mp4 output.mp4 --info
    """
    try:
        if blur_intensity % 2 == 0 or blur_intensity < 1:
            console.print("[red]Error: Blur intensity must be a positive odd number[/red]")
            raise click.Abort()

        with VideoAnalyzer(str(input_video)) as analyzer:
            metadata = analyzer.analyze()

            if info:
                _display_video_info(metadata, str(input_video))
                return

            _display_processing_info(
                input_video,
                output_video,
                metadata,
                blur_intensity,
                advanced,
                preview
            )

            processor_class = AdvancedWatermarkProcessor if advanced else WatermarkProcessor

            processor = processor_class(
                input_path=str(input_video),
                output_path=str(output_video),
                blur_intensity=blur_intensity,
                preview_duration=preview
            )

            total_frames = metadata.total_frames
            if preview:
                total_frames = min(total_frames, int(preview * metadata.fps))

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                TimeElapsedColumn(),
                console=console
            ) as progress:
                task = progress.add_task(
                    "[cyan]Processing video...",
                    total=total_frames
                )

                def update_progress(current: int, total: int):
                    progress.update(task, completed=current)

                processor.process(progress_callback=update_progress)

            console.print(f"\n[green]✓[/green] Video processed successfully!")
            console.print(f"[dim]Output saved to: {output_video}[/dim]")

    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise click.Abort()
    except RuntimeError as e:
        console.print(f"[red]Processing error: {e}[/red]")
        raise click.Abort()
    except Exception as e:
        console.print(f"[red]Unexpected error: {e}[/red]")
        raise click.Abort()


def _display_video_info(metadata, video_path: str):
    """
    Display detailed video information in a formatted table.

    Args:
        metadata: VideoMetadata object
        video_path: Path to the video file
    """
    table = Table(title=f"Video Information: {Path(video_path).name}")

    table.add_column("Property", style="cyan", no_wrap=True)
    table.add_column("Value", style="magenta")

    table.add_row("Resolution", f"{metadata.width}x{metadata.height}")
    table.add_row("Orientation", metadata.orientation.capitalize())
    table.add_row("FPS", f"{metadata.fps:.2f}")
    table.add_row("Duration", f"{metadata.duration:.2f}s ({metadata.total_frames} frames)")
    table.add_row("Codec", metadata.codec)

    positions_text = "Top-left → Center-right → Bottom-left (every 2.3s)"
    table.add_row("Watermark Pattern", positions_text)

    console.print(table)


def _display_processing_info(
    input_path: Path,
    output_path: Path,
    metadata,
    blur_intensity: int,
    advanced: bool,
    preview: float
):
    """
    Display processing configuration before starting.

    Args:
        input_path: Input video path
        output_path: Output video path
        metadata: VideoMetadata object
        blur_intensity: Blur kernel size
        advanced: Whether advanced mode is enabled
        preview: Preview duration in seconds
    """
    info_lines = [
        f"[cyan]Input:[/cyan] {input_path.name}",
        f"[cyan]Output:[/cyan] {output_path.name}",
        f"[cyan]Resolution:[/cyan] {metadata.width}x{metadata.height}",
        f"[cyan]Duration:[/cyan] {metadata.duration:.1f}s",
        f"[cyan]Mode:[/cyan] {'Advanced (Edge-aware)' if advanced else 'Standard'}",
        f"[cyan]Blur:[/cyan] {blur_intensity}",
    ]

    if preview:
        info_lines.append(f"[yellow]Preview:[/yellow] First {preview}s only")

    console.print(Panel("\n".join(info_lines), title="Processing Configuration", expand=False))
