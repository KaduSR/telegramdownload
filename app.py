import streamlit as st
import asyncio
import os
import threading
import queue
import time
from downloader import TelegramDownloader, TelegramUploader, AsyncManager
from database import AppDatabase
from telethon import TelegramClient
from datetime import datetime

# Configuração Visual
st.set_page_config(page_title="Media Manager Pro Bot", layout="wide", page_icon="🤖")

# CSS Premium com alertas
st.markdown("""
    <style>
    .stMetric { 
        background-color: #1e2130; 
        padding: 15px; 
        border-radius: 10px; 
        box-shadow: 0 4px 6px rgba(0,0,0,0.3); 
        border: 1px solid #464855; 
    }
    [data-testid="stMetricValue"] { color: #ffffff !important; }
    [data-testid="stMetricLabel"] { color: #a3a8b8 !important; }
    .warning-box { background-color: #2e2a1a; color: #ffd966; padding: 15px; border-radius: 10px; border: 1px solid #5e532d; margin-bottom: 20px; }
    .security-tip { font-size: 0.8em; color: #ff4b4b; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# --- SINGLETONS ---
@st.cache_resource
def get_async_mgr(): return AsyncManager()
@st.cache_resource
def get_db(): return AppDatabase()
@st.cache_resource
def get_client(api_id, api_hash, phone):
    mgr = get_async_mgr()
    session_name = f"session_{phone.replace('+', '')}"
    async def init():
        try:
            client = TelegramClient(session_name, int(api_id), api_hash, loop=mgr.loop)
            await client.connect()
            return client
        except: return None
    return mgr.run_coro(init()).result()

# --- ESTADO ---
if "logs" not in st.session_state: st.session_state.logs = []
if "is_running" not in st.session_state: st.session_state.is_running = False
if "metrics" not in st.session_state: st.session_state.metrics = {"total": 0, "count": 0, "size": 0, "current": "", "speed": 0}
if "active_speeds" not in st.session_state: st.session_state.active_speeds = {}
if "active_bytes" not in st.session_state: st.session_state.active_bytes = {}

def add_log(msg):
    st.session_state.logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")
    if len(st.session_state.logs) > 50: st.session_state.logs.pop(0)

# --- UI ---
db = get_db()
st.title("🤖 Telegram Media Pro Manager + Bot")

with st.sidebar:
    st.header("🔑 Acesso e Segurança")
    st.markdown('<p class="security-tip">⚠️ Nunca compartilhe seu API ID/HASH!</p>', unsafe_allow_html=True)
    
    api_id = st.text_input("Telegram API ID", value=db.get_setting("api_id"), type="password")
    api_hash = st.text_input("Telegram API HASH", value=db.get_setting("api_hash"), type="password")
    phone = st.text_input("Seu Telefone (+55...)", value=db.get_setting("phone"))
    
    st.divider()
    st.header("🔔 Bot de Alertas (Telegram)")
    st.caption("Crie um bot no @BotFather e pegue o Token")
    bot_token = st.text_input("Bot Token", value=db.get_setting("bot_token"), type="password")
    admin_id = st.text_input("Seu Chat ID (Pegue no @userinfobot)", value=db.get_setting("admin_chat_id"))
    
    st.divider()
    st.header("🚀 Performance")
    parallel = st.slider("Processos Simultâneos", 1, 30, int(db.get_setting("parallel", 3)))
    
    if st.button("💾 Salvar Configurações", use_container_width=True):
        db.save_setting("api_id", api_id)
        db.save_setting("api_hash", api_hash)
        db.save_setting("phone", phone)
        db.save_setting("bot_token", bot_token)
        db.save_setting("admin_chat_id", admin_id)
        db.save_setting("parallel", parallel)
        st.success("Configurações persistidas no SQLite!")

# Alerta de Espaço em Disco
st.markdown("""
<div class="warning-box">
    <strong>⚠️ Requisito de Sistema:</strong> Certifique-se de ter pelo menos <strong>35 GB</strong> livres no seu computador antes de iniciar grandes downloads.
</div>
""", unsafe_allow_html=True)

tab_dl, tab_up, tab_history, tab_logs = st.tabs(["📥 Central de Download", "📤 Central de Upload", "📊 Estatísticas", "📋 Logs"])

# --- ABA DOWNLOAD ---
with tab_dl:
    if api_id and api_hash and phone:
        client = get_client(api_id, api_hash, phone)
        if client:
            mgr = get_async_mgr()
            if mgr.run_coro(client.is_user_authorized()).result():
                st.subheader("Configurar Tarefa de Download")
                col_ch, col_dir = st.columns([2, 1])
                channel = col_ch.text_input("Link do Canal de Origem", value=db.get_setting("dl_channel"), placeholder="https://t.me/...")
                dir_dl = col_dir.text_input("Pasta Local de Destino", value=db.get_setting("dl_dir", "./downloads"))
                
                if not st.session_state.is_running:
                    if st.button("🚀 INICIAR DOWNLOAD", use_container_width=True, type="primary"):
                        db.save_setting("dl_channel", channel)
                        db.save_setting("dl_dir", dir_dl)
                        st.session_state.is_running = True
                        st.session_state.update_queue = queue.Queue()
                        st.session_state.metrics = {"total": 0, "count": 0, "size": 0, "current": "", "speed": 0}
                        st.session_state.active_speeds = {}
                        st.session_state.active_bytes = {}
                        
                        class Cfg:
                            CHANNEL_LINK, DOWNLOAD_DIR, MAX_PARALLEL = channel, dir_dl, parallel
                        
                        st.session_state.active_job = TelegramDownloader(Cfg(), st.session_state.update_queue, client)
                        st.session_state.future = mgr.run_coro(st.session_state.active_job.run())
                        st.rerun()
                else:
                    if st.button("🛑 PARAR AGORA", use_container_width=True):
                        mgr.loop.call_soon_threadsafe(st.session_state.active_job.stop_event.set)

                    # Monitoramento Real-time
                    q = st.session_state.update_queue
                    while not q.empty():
                        msg = q.get()
                        if msg["type"] == "total": st.session_state.metrics["total"] = msg["count"]
                        elif msg["type"] == "metrics":
                            st.session_state.metrics["count"] += msg.get("downloaded", 0)
                            st.session_state.metrics["size"] += msg.get("bytes", 0)
                            if "file_name" in msg:
                                st.session_state.active_speeds.pop(msg["file_name"], None)
                                st.session_state.active_bytes.pop(msg["file_name"], None)
                        elif msg["type"] == "progress":
                            st.session_state.metrics["current"] = f"📥 {msg['file_name'][:40]}"
                            st.session_state.active_speeds[msg["file_name"]] = msg.get("speed", 0)
                            st.session_state.active_bytes[msg["file_name"]] = msg.get("current", 0)
                            st.session_state.metrics["speed"] = sum(st.session_state.active_speeds.values())
                    
                    total = st.session_state.metrics["total"]
                    concluidos = st.session_state.metrics["count"]
                    restantes = max(0, total - concluidos)
                    bytes_reais = st.session_state.metrics["size"] + sum(st.session_state.active_bytes.values())
                    
                    m1, m2, m3, m4 = st.columns(4)
                    m1.metric("Na Fila", total)
                    m2.metric("Concluídos", concluidos)
                    m3.metric("Faltam", restantes)
                    m4.metric("Velocidade", f"{st.session_state.metrics['speed']/(1024*1024):.2f} MB/s")
                    
                    if total > 0:
                        progresso_percent = min(1.0, concluidos / total)
                        st.progress(progresso_percent, text=f"Progresso: {concluidos}/{total} arquivos ({progresso_percent*100:.1f}%)")
                    
                    st.metric("Total Baixado", f"{bytes_reais/(1024*1024):.2f} MB")
                    
                    if st.session_state.metrics["current"]: 
                        st.info(f"**Ativo:** {st.session_state.metrics['current']}")
                    
                    if st.session_state.future.done():
                        st.session_state.is_running = False
                        st.rerun()
                    else: time.sleep(0.5); st.rerun()
            else: st.warning("Autenticação necessária na barra lateral.")

# --- ABA UPLOAD ---
with tab_up:
    if api_id and api_hash and phone:
        client = get_client(api_id, api_hash, phone)
        if client:
            mgr = get_async_mgr()
            if mgr.run_coro(client.is_user_authorized()).result():
                st.subheader("Configurar Tarefa de Upload")
                col_up1, col_up2 = st.columns([2, 1])
                dest_channel = col_up1.text_input("Link do Grupo/Canal de Destino", value=db.get_setting("up_channel"))
                source_dir = col_up2.text_input("Pasta Local dos Arquivos", value=db.get_setting("up_dir", "./downloads"))
                
                if not st.session_state.is_running:
                    if st.button("📤 INICIAR UPLOAD EM MASSA", use_container_width=True, type="primary"):
                        db.save_setting("up_channel", dest_channel)
                        db.save_setting("up_dir", source_dir)
                        st.session_state.is_running = True
                        st.session_state.update_queue = queue.Queue()
                        st.session_state.metrics = {"total": 0, "count": 0, "size": 0, "current": "", "speed": 0}
                        st.session_state.active_speeds = {}
                        st.session_state.active_bytes = {}
                        class CfgUp:
                            DEST_CHANNEL, SOURCE_DIR, MAX_PARALLEL = dest_channel, source_dir, parallel
                        
                        st.session_state.active_job = TelegramUploader(CfgUp(), st.session_state.update_queue, client)
                        st.session_state.future = mgr.run_coro(st.session_state.active_job.run())
                        st.rerun()
                else:
                    q = st.session_state.update_queue
                    while not q.empty():
                        msg = q.get()
                        if msg["type"] == "total": st.session_state.metrics["total"] = msg["count"]
                        elif msg["type"] == "metrics":
                            st.session_state.metrics["count"] += msg.get("uploaded", 0)
                            st.session_state.metrics["size"] += msg.get("bytes", 0)
                            if "file_name" in msg:
                                st.session_state.active_speeds.pop(msg["file_name"], None)
                                st.session_state.active_bytes.pop(msg["file_name"], None)
                        elif msg["type"] == "progress":
                            st.session_state.metrics["current"] = f"📤 Enviando: {msg['file_name'][:40]}"
                            st.session_state.active_speeds[msg["file_name"]] = msg.get("speed", 0)
                            st.session_state.active_bytes[msg["file_name"]] = msg.get("current", 0)
                            st.session_state.metrics["speed"] = sum(st.session_state.active_speeds.values())
                    
                    total_up = st.session_state.metrics["total"]
                    enviados = st.session_state.metrics["count"]
                    restantes_up = max(0, total_up - enviados)
                    bytes_reais_up = st.session_state.metrics["size"] + sum(st.session_state.active_bytes.values())
                    
                    m1, m2, m3, m4 = st.columns(4)
                    m1.metric("Na Pasta", total_up)
                    m2.metric("Enviados", enviados)
                    m3.metric("Faltam", restantes_up)
                    m4.metric("Velocidade", f"{st.session_state.metrics['speed']/(1024*1024):.2f} MB/s")
                    
                    if total_up > 0:
                        progresso_up = min(1.0, enviados / total_up)
                        st.progress(progresso_up, text=f"Progresso: {enviados}/{total_up} arquivos ({progresso_up*100:.1f}%)")
                    
                    st.metric("Volume Total Enviado", f"{bytes_reais_up/(1024*1024):.2f} MB")
                    
                    if st.session_state.metrics["current"]: 
                        st.info(f"**Ativo:** {st.session_state.metrics['current']}")
                    if st.session_state.future.done():
                        st.session_state.is_running = False
                        st.rerun()
                    else: time.sleep(0.5); st.rerun()

with tab_history:
    st.metric("Volume Total Processado (Histórico)", f"{db.get_total_downloaded_size()/(1024**3):.2f} GB")

with tab_logs:
    st.text_area("Live Log Console", value="\n".join(st.session_state.logs[::-1]), height=400)
