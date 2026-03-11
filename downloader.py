import os
import asyncio
import logging
import threading
import queue
import time
import requests
from concurrent.futures import Future
from telethon import TelegramClient, utils
from database import AppDatabase

# Configuração de logging
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler("logs/download.log", encoding='utf-8')]
)

class AsyncManager:
    def __init__(self):
        self.loop = asyncio.new_event_loop()
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()

    def _run_loop(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    def run_coro(self, coro) -> Future:
        return asyncio.run_coroutine_threadsafe(coro, self.loop)

class TelegramDownloader:
    def __init__(self, config, update_queue, client):
        self.config = config
        self.update_queue = update_queue
        self.client = client
        self.semaphore = asyncio.Semaphore(config.MAX_PARALLEL)
        self.queue = asyncio.Queue()
        self.db = AppDatabase()
        self.stop_event = asyncio.Event()
        
        # Para cálculo de velocidade
        self.last_bytes = 0
        self.last_time = time.time()

    def _ui_update(self, msg_type, **kwargs):
        self.update_queue.put({"type": msg_type, **kwargs})

    def send_bot_alert(self, message):
        """Envia mensagem via Bot Token para o Chat ID configurado."""
        token = self.db.get_setting("bot_token")
        chat_id = self.db.get_setting("admin_chat_id")
        if token and chat_id:
            try:
                url = f"https://api.telegram.org/bot{token}/sendMessage"
                requests.post(url, data={"chat_id": chat_id, "text": f"🚨 [ALERTA GESTOR]\n{message}"}, timeout=5)
            except: pass

    async def ensure_connection(self):
        if not self.client.is_connected(): await self.client.connect()

    async def download_worker(self):
        while not self.stop_event.is_set():
            try:
                message = await asyncio.wait_for(self.queue.get(), timeout=1.0)
                async with self.semaphore:
                    await self.download_file(message)
                self.queue.task_done()
            except asyncio.TimeoutError: continue
            except Exception as e: logging.error(f"Worker error: {e}")

    async def download_file(self, message):
        file_name = f"arquivo_{message.id}{utils.get_extension(message.media)}"
        if hasattr(message.media, 'document'):
            for attr in message.media.document.attributes:
                if hasattr(attr, 'file_name'): file_name = attr.file_name
        
        file_path = os.path.join(self.config.DOWNLOAD_DIR, file_name)
        
        if self.db.is_downloaded(message.id) and os.path.exists(file_path) and os.path.getsize(file_path) > 0:
            self._ui_update("metrics", downloaded=1, bytes=0)
            return

        await self.ensure_connection()
        
        # Variáveis para cálculo de velocidade instantânea
        state = {"last_v": 0, "last_t": time.time()}

        def progress_callback(current, total):
            now = time.time()
            diff_t = now - state["last_t"]
            if diff_t >= 0.5:  # Atualiza a cada 500ms para estabilidade
                diff_v = current - state["last_v"]
                speed = diff_v / diff_t
                state["last_v"] = current
                state["last_t"] = now
                self._ui_update("progress", file_name=file_name, current=current, total=total, speed=speed)

        try:
            # download_media do Telethon já é razoavelmente otimizado, 
            # mas o segredo para 1GB é o paralelismo configurado no Slider.
            await self.client.download_media(message.media, file_path, progress_callback=progress_callback)
            size = os.path.getsize(file_path)
            self.db.save_history(message.id, file_name, size)
            self._ui_update("metrics", downloaded=1, bytes=size, file_name=file_name)
        except Exception as e: logging.error(f"Erro download {file_name}: {e}")

    async def run(self):
        workers = [asyncio.create_task(self.download_worker()) for _ in range(self.config.MAX_PARALLEL)]
        try:
            await self.ensure_connection()
            count = 0
            async for message in self.client.iter_messages(self.config.CHANNEL_LINK):
                if self.stop_event.is_set(): break
                if message.media:
                    count += 1
                    self._ui_update("total", count=count)
                    await self.queue.put(message)
            await self.queue.join()
            self.send_bot_alert(f"✅ Download em Massa Concluído!\nCanal: {self.config.CHANNEL_LINK}\nTotal de arquivos: {count}")
        finally:
            self.stop_event.set()
            for w in workers: w.cancel()

class TelegramUploader:
    def __init__(self, config, update_queue, client):
        self.config = config
        self.update_queue = update_queue
        self.client = client
        self.stop_event = asyncio.Event()
        self.semaphore = asyncio.Semaphore(config.MAX_PARALLEL)
        self.db = AppDatabase()

    def _ui_update(self, msg_type, **kwargs):
        self.update_queue.put({"type": msg_type, **kwargs})

    def send_bot_alert(self, message):
        token = self.db.get_setting("bot_token")
        chat_id = self.db.get_setting("admin_chat_id")
        if token and chat_id:
            try:
                url = f"https://api.telegram.org/bot{token}/sendMessage"
                requests.post(url, data={"chat_id": chat_id, "text": f"📤 [ALERTA UPLOAD]\n{message}"}, timeout=5)
            except: pass

    async def upload_worker(self, file_path):
        async with self.semaphore:
            if self.stop_event.is_set(): return
            file_name = os.path.basename(file_path)
            start_t = time.time()
            try:
                await self.client.send_file(
                    self.config.DEST_CHANNEL, 
                    file_path,
                    caption=f"✅ Enviado via Media Manager Pro",
                    progress_callback=lambda c, t: self._ui_update("progress", 
                        file_name=file_name, current=c, total=t, speed=c/(time.time()-start_t) if (time.time()-start_t)>0 else 0)
                )
                self._ui_update("metrics", uploaded=1, bytes=os.path.getsize(file_path), file_name=file_name)
            except Exception as e: logging.error(f"Erro upload {file_name}: {e}")

    async def run(self):
        files = [os.path.join(self.config.SOURCE_DIR, f) for f in os.listdir(self.config.SOURCE_DIR) 
                 if os.path.isfile(os.path.join(self.config.SOURCE_DIR, f))]
        
        self._ui_update("total", count=len(files))
        tasks = [asyncio.create_task(self.upload_worker(f)) for f in files]
        await asyncio.gather(*tasks)
        self.send_bot_alert(f"✅ Upload em Massa Finalizado!\nDestino: {self.config.DEST_CHANNEL}\nArquivos: {len(files)}")
