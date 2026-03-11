import asyncio
import sys
from config import Config
from dashboard import Dashboard
from downloader import TelegramDownloader
from rich.live import Live

async def main():
    # 1. Valida configurações
    try:
        Config.validate()
    except ValueError as e:
        print(f"Erro de configuração: {e}")
        sys.exit(1)

    # 2. Inicializa o Dashboard
    # Nota: O nome do canal será atualizado após a conexão
    dashboard = Dashboard(Config.CHANNEL_LINK, Config.DOWNLOAD_DIR)
    
    # 3. Inicializa o Downloader
    downloader = TelegramDownloader(Config, dashboard)

    # 4. Inicia a interface Live e o Downloader
    try:
        with Live(dashboard.make_layout(), refresh_per_second=4, screen=True) as live:
            # Task para atualizar o layout periodicamente
            async def update_ui():
                while True:
                    live.update(dashboard.make_layout())
                    await asyncio.sleep(0.5)
            
            ui_task = asyncio.create_task(update_ui())
            
            # Executa o downloader
            await downloader.run()
            
            ui_task.cancel()
            
    except KeyboardInterrupt:
        print("\nInterrompido pelo usuário.")
    except Exception as e:
        print(f"\nOcorreu um erro: {e}")
    finally:
        await downloader.client.disconnect()
        print("\nDownload concluído ou interrompido. Verifique os logs em logs/download.log")

if __name__ == "__main__":
    asyncio.run(main())
