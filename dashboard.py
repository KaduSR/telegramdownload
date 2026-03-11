import time
from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.progress import Progress, TextColumn, BarColumn, DownloadColumn, TransferSpeedColumn, TimeRemainingColumn
from rich.table import Table
from rich.live import Live

class Dashboard:
    def __init__(self, channel_name, download_dir):
        self.console = Console()
        self.channel_name = channel_name
        self.download_dir = download_dir
        self.total_files = 0
        self.downloaded_count = 0
        self.total_size_bytes = 0
        self.downloaded_size_bytes = 0
        self.start_time = time.time()
        
        # Gerenciador de barras de progresso
        self.progress = Progress(
            TextColumn("[bold blue]{task.description}", justify="left"),
            BarColumn(bar_width=None),
            "[progress.percentage]{task.percentage:>3.1f}%",
            "•",
            DownloadColumn(),
            "•",
            TransferSpeedColumn(),
            "•",
            TimeRemainingColumn(),
        )
        
        # Tarefa principal de progresso global (opcional ou pode ser apenas métricas)
        self.overall_task = None

    def make_layout(self) -> Layout:
        layout = Layout()
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="main"),
            Layout(name="progress", size=10),
        )
        
        # Header Panel
        header_text = f"[bold green]Telegram Downloader Dashboard[/bold green]\n" \
                      f"Canal: {self.channel_name} | Diretório: {self.download_dir}"
        layout["header"].update(Panel(header_text, style="white on blue"))
        
        # Main Metrics Panel
        metrics_table = Table.grid(expand=True)
        metrics_table.add_column(justify="left", ratio=1)
        metrics_table.add_column(justify="left", ratio=1)
        
        elapsed = time.time() - self.start_time
        avg_speed = self.downloaded_size_bytes / elapsed if elapsed > 0 else 0
        remaining_files = self.total_files - self.downloaded_count
        
        # Formata métricas
        metrics_table.add_row(
            f"Arquivos Totais: [bold yellow]{self.total_files}[/bold yellow]",
            f"Velocidade Média: [bold cyan]{self.format_size(avg_speed)}/s[/bold cyan]"
        )
        metrics_table.add_row(
            f"Baixados: [bold green]{self.downloaded_count}[/bold green]",
            f"Tamanho Baixado: [bold cyan]{self.format_size(self.downloaded_size_bytes)}[/bold cyan]"
        )
        metrics_table.add_row(
            f"Restantes: [bold red]{remaining_files}[/bold red]",
            f"Tempo Decorrido: [bold white]{self.format_time(elapsed)}[/bold white]"
        )
        
        layout["main"].update(Panel(metrics_table, title="Métricas", border_style="bright_blue"))
        
        # Progress Bars Panel
        layout["progress"].update(Panel(self.progress, title="Downloads em Execução", border_style="bright_blue"))
        
        return layout

    @staticmethod
    def format_size(size_bytes):
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} PB"

    @staticmethod
    def format_time(seconds):
        mins, secs = divmod(int(seconds), 60)
        hours, mins = divmod(mins, 60)
        if hours > 0:
            return f"{hours}h {mins}m {secs}s"
        return f"{mins}m {secs}s"

    def update_metrics(self, downloaded_increment=0, bytes_increment=0):
        self.downloaded_count += downloaded_increment
        self.downloaded_size_bytes += bytes_increment
