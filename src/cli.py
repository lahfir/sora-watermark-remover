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
from rich.style import Style
from rich.progress_bar import ProgressBar
from rich.text import Text

from src.video_analyzer import VideoAnalyzer
from src.watermark_processor import WatermarkProcessor, AdvancedWatermarkProcessor


console = Console()


class ShimmerTextColumn(TextColumn):
    """
    Custom text column with shimmer effect that shines through the text.
    """

    def render(self, task):
        """
        Render text with animated shimmer effect.
        """
        import time

        text = task.description
        shimmer_pos = (time.time() * 4) % (len(text) + 6)

        result_parts = []
        for i, char in enumerate(text):
            distance = abs(i - shimmer_pos)

            if distance < 1.5:
                result_parts.append(f'[bold white]{char}[/bold white]')
            elif distance < 3:
                result_parts.append(f'[white]{char}[/white]')
            elif distance < 4.5:
                result_parts.append(f'[bright_cyan]{char}[/bright_cyan]')
            else:
                result_parts.append(f'[bold cyan]{char}[/bold cyan]')

        return Text.from_markup(''.join(result_parts))


class ShimmerBarColumn(BarColumn):
    """
    Custom progress bar with white shimmer effect.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bar_width = kwargs.get('bar_width', 40)

    def render(self, task):
        """
        Render progress bar with shimmer gradient effect.
        """
        import time

        completed = task.completed
        total = task.total
        percentage = (completed / total * 100) if total else 0

        bar_width = self.bar_width or 40
        filled_width = int(bar_width * completed / total) if total else 0

        shimmer_pos = int((time.time() * 3) % bar_width)

        bar_parts = []
        for i in range(bar_width):
            if i < filled_width:
                distance = abs(i - shimmer_pos)
                if distance < 3:
                    if distance == 0:
                        bar_parts.append('[bold white]━[/bold white]')
                    elif distance == 1:
                        bar_parts.append('[white]━[/white]')
                    else:
                        bar_parts.append('[bright_cyan]━[/bright_cyan]')
                else:
                    bar_parts.append('[cyan]━[/cyan]')
            else:
                bar_parts.append('[dim white]━[/dim white]')

        from rich.text import Text
        return Text.from_markup(''.join(bar_parts))


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
@click.option(
    '--width',
    '-w',
    type=int,
    default=139,
    help='Watermark width in pixels (default: 139)'
)
@click.option(
    '--height',
    '-h',
    type=int,
    default=51,
    help='Watermark height in pixels (default: 51)'
)
def remove_watermark(
    input_video: Path,
    output_video: Path,
    blur_intensity: int,
    preview: float,
    advanced: bool,
    info: bool,
    width: int,
    height: int
):
    """
    Remove or blur watermarks from videos with dynamic positioning.

    Handles watermarks that alternate between three positions:
    - Top-left
    - Center-right
    - Bottom-left

    The watermark position changes every 2.5 seconds.

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
                preview_duration=preview,
                wm_width=width,
                wm_height=height
            )

            total_frames = metadata.total_frames
            if preview:
                total_frames = min(total_frames, int(preview * metadata.fps))

            with Progress(
                SpinnerColumn(),
                ShimmerTextColumn(),
                ShimmerBarColumn(bar_width=50),
                TextColumn("[bold white]{task.percentage:>3.0f}%"),
                TimeElapsedColumn(),
                console=console,
                refresh_per_second=10
            ) as progress:
                task = progress.add_task(
                    "Processing video...",
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

    positions_text = "Top-left → Center-right → Bottom-left (every 2.5s)"
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
