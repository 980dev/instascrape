import os, json, time, threading, shutil, uvicorn, httpx, random, re, sys, webbrowser, ctypes
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
from fastapi import FastAPI, Request, Response
from fastapi.responses import HTMLResponse, FileResponse
import instaloader
from selenium import webdriver
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.chrome.options import Options as ChromeOptions

app = FastAPI()

def resource_path(relative_path):
    """ Gestisce i percorsi per PyInstaller """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class ScraperState:
    def __init__(self):
        self.loader = instaloader.Instaloader()
        self.current_user = None
        self.current_user_avatar = ""
        self.is_running = False
        self.stop_requested = False
        self.logs = []
        self.log_counter = 0
        self.post_count = 0
        self.target_info = {"name": "", "avatar": "", "bio": ""}
        self.session_dir = ".sessions"
        self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        self.app_id = "936619743392459"
        self.driver = None 
        if not os.path.exists(self.session_dir): os.makedirs(self.session_dir)

state = ScraperState()

def apply_secure_headers(context):
    csrf = context._session.cookies.get('csrftoken', domain='.instagram.com')
    mid = context._session.cookies.get('mid', domain='.instagram.com')
    ds_user_id = context._session.cookies.get('ds_user_id', domain='.instagram.com')
    context._session.headers.update({
        'X-IG-App-ID': state.app_id,
        'X-IG-WWW-Claim': '0',
        'X-Requested-With': 'XMLHttpRequest',
        'X-ASBD-ID': '129477',
        'X-CSRFToken': str(csrf) if csrf else '',
        'X-IG-Device-ID': str(ds_user_id) if ds_user_id else '',
        'Referer': 'https://www.instagram.com/',
        'User-Agent': state.user_agent
    })

def log(msg, type="info"):
    if not hasattr(state, 'log_counter'): state.log_counter = 0
    state.log_counter += 1
    t = time.strftime("%H:%M:%S")
    # Pulisce i log vecchi se necessario
    if len(state.logs) > 5000: state.logs.pop(0)
    state.logs.append({"id": state.log_counter, "time": t, "msg": msg, "type": type})

def try_auto_login():
    if not os.path.exists(state.session_dir): return
    files = [f for f in os.listdir(state.session_dir) if f.startswith("session_")]
    if not files: return
    username = files[0].replace("session_", "")
    try:
        state.loader.load_session_from_file(username, os.path.join(state.session_dir, files[0]))
        apply_secure_headers(state.loader.context)
        state.current_user = username
        log("Software Online", "success")
    except: pass

def start_unified_browser():
    update_loader(80, "Sincronizzazione Browser...")
    time.sleep(2)
    url = "http://127.0.0.1:8000"
    
    # Loop di tentativo per browser protetto
    success = False
    for browser in ["edge", "chrome"]:
        try:
            if browser == "edge":
                o = EdgeOptions(); o.add_argument("--start-maximized"); o.add_argument("--log-level=3")
                o.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
                state.driver = webdriver.Edge(options=o)
            else:
                o = ChromeOptions(); o.add_argument("--start-maximized"); o.add_argument("--log-level=3")
                o.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
                state.driver = webdriver.Chrome(options=o)
            
            state.user_agent = state.driver.execute_script("return navigator.userAgent")
            update_loader(100, "Dashboard Operativa")
            state.driver.get(url)
            success = True
            break
        except: continue
        
    if not success:
        update_loader(100, "Errore: Browser non trovato!")
        time.sleep(2)
        shutdown_app()

# --- CONTROL PANEL GUI ---
loader_root = None
progress_bar = None
status_label = None
btn_frame = None

def shutdown_app():
    if state.driver:
        try: state.driver.quit()
        except: pass
    os._exit(0)

def manual_open():
    if state.driver:
        try: state.driver.get("http://127.0.0.1:8000")
        except: pass

def minimize_app():
    # Comando Windows diretto per ridurre a icona
    hwnd = ctypes.windll.user32.GetParent(loader_root.winfo_id())
    ctypes.windll.user32.ShowWindow(hwnd, 6) # 6 = SW_MINIMIZE

def create_loader():
    global loader_root, progress_bar, status_label, btn_frame
    
    loader_root = tk.Tk()
    loader_root.title("980 CONTROL CENTER")
    loader_root.overrideredirect(True)
    loader_root.attributes('-topmost', True)
    loader_root.configure(bg='#0a0a0f')

    # --- FORZA VISIBILITA' TASKBAR ---
    GWL_EXSTYLE = -20
    WS_EX_APPWINDOW = 0x00040000
    WS_EX_TOOLWINDOW = 0x00000080
    
    def set_appwindow():
        hwnd = ctypes.windll.user32.GetParent(loader_root.winfo_id())
        style = ctypes.windll.user32.GetWindowLongPtrW(hwnd, GWL_EXSTYLE)
        style = style & ~WS_EX_TOOLWINDOW
        style = style | WS_EX_APPWINDOW
        ctypes.windll.user32.SetWindowLongPtrW(hwnd, GWL_EXSTYLE, style)
        loader_root.withdraw()
        loader_root.after(10, loader_root.deiconify)

    loader_root.after(100, set_appwindow)

    # Icona
    try:
        icon_path = resource_path("logo.png")
        icon_img = ImageTk.PhotoImage(Image.open(icon_path))
        loader_root.iconphoto(False, icon_img)
    except: pass

    # Dimensioni e Posizione
    w, h = 400, 320
    sw, sh = loader_root.winfo_screenwidth(), loader_root.winfo_screenheight()
    loader_root.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

    # --- CUSTOM TITLE BAR ---
    title_bar = tk.Frame(loader_root, bg='#16161e', height=30)
    title_bar.pack(fill='x', side='top')
    
    def start_move(event): loader_root.x, loader_root.y = event.x, event.y
    def on_move(event):
        x = loader_root.winfo_x() + (event.x - loader_root.x)
        y = loader_root.winfo_y() + (event.y - loader_root.y)
        loader_root.geometry(f"+{x}+{y}")

    title_bar.bind('<Button-1>', start_move)
    title_bar.bind('<B1-Motion>', on_move)
    
    tk.Label(title_bar, text=" 980 COMMAND CENTER", fg="#9CA3AF", bg='#16161e', font=("Outfit", 7, "bold")).pack(side='left', padx=10)
    
    # Tasto Riduci
    tk.Button(title_bar, text="—", command=minimize_app, bg='#16161e', fg='white', relief='flat', font=("Arial", 8), bd=0, padx=10).pack(side='right')

    # Logo Centrale
    try:
        img_path = resource_path("logo.png")
        img = Image.open(img_path).resize((70, 70), Image.LANCZOS)
        logo_img = ImageTk.PhotoImage(img)
        tk.Label(loader_root, image=logo_img, bg='#0a0a0f').pack(pady=(20, 5))
        loader_root.logo_img = logo_img 
    except: pass

    tk.Label(loader_root, text="980 INSTASCRAPE PRO", fg="white", bg='#0a0a0f', font=("Outfit", 12, "bold")).pack()
    
    status_label = tk.Label(loader_root, text="Inizializzazione Core...", fg="#9CA3AF", bg='#0a0a0f', font=("Outfit", 9))
    status_label.pack(pady=(15, 5))

    style = ttk.Style()
    style.theme_use('default')
    style.configure("TProgressbar", thickness=4, troughcolor='#1f1f2e', background='#7C3AED', bordercolor='#0a0a0f', lightcolor='#7C3AED', darkcolor='#7C3AED')
    
    progress_bar = ttk.Progressbar(loader_root, style="TProgressbar", orient="horizontal", length=300, mode="determinate")
    progress_bar.pack(pady=10)
    
    btn_frame = tk.Frame(loader_root, bg='#0a0a0f')
    
    tk.Button(btn_frame, text="APRI DASHBOARD", command=manual_open, bg='#7C3AED', fg='white', font=("Outfit", 8, "bold"), relief='flat', padx=15, pady=8).pack(side='left', padx=10)
    tk.Button(btn_frame, text="SHUTDOWN", command=shutdown_app, bg='#1f1f2e', fg='#EF4444', font=("Outfit", 8, "bold"), relief='flat', padx=15, pady=8, highlightbackground='#EF4444', highlightthickness=1).pack(side='left', padx=10)

    loader_root.mainloop()

def update_loader(val, text):
    if loader_root and progress_bar and status_label:
        progress_bar['value'] = val
        status_label.config(text=text)
        if val >= 100 and btn_frame:
            btn_frame.pack(pady=20) # Mostra i tasti solo alla fine
        loader_root.update()

def close_loader():
    if loader_root: loader_root.destroy()

@app.get("/")
async def get_index():
    path = resource_path("index.html")
    with open(path, "r", encoding="utf-8") as f: return HTMLResponse(f.read())

@app.get("/logo.png")
async def get_logo():
    path = resource_path("logo.png")
    if os.path.exists(path): return FileResponse(path)
    return Response(status_code=404)

@app.get("/api/proxy_image")
def proxy_image(url: str):
    try:
        # Tunnel sincronizzato con header completi
        headers = {
            "User-Agent": state.user_agent,
            "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
            "Accept-Language": "it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7",
            "Sec-Fetch-Dest": "image",
            "Sec-Fetch-Mode": "no-cors",
            "Sec-Fetch-Site": "cross-site"
        }
        resp = state.loader.context._session.get(url, timeout=15.0, headers=headers)
        if resp.status_code == 200:
            return Response(content=resp.content, media_type=resp.headers.get("content-type"))
    except Exception as e:
        print(f"Errore Proxy Immagine: {e}")
    return Response(status_code=404)

@app.get("/api/status")
async def get_status():
    return {"user": state.current_user, "avatar": state.current_user_avatar, "is_running": state.is_running, "logs": state.logs, "post_count": state.post_count, "target": state.target_info}

@app.post("/api/login")
async def api_login():
    threading.Thread(target=run_browser_login, daemon=True).start()
    return {"status": "started"}

@app.post("/api/logout")
async def api_logout():
    if state.loader:
        try: state.loader.context._session.close()
        except: pass
        state.loader = instaloader.Instaloader()
    state.current_user = None
    state.target_info = None
    state.logs = []
    for f in os.listdir(state.session_dir): os.remove(os.path.join(state.session_dir, f))
    return {"status": "logged_out"}

def run_browser_login():
    if not state.driver: return
    try:
        log("Avvio autenticazione sicura...", "info")
        state.driver.get("https://www.instagram.com/accounts/login/")
        cookies = None; start = time.time()
        while time.time() - start < 300:
            try:
                cks = state.driver.get_cookies()
                if any(c['name'] == 'sessionid' for c in cks):
                    cookies = cks; break
            except: break
            time.sleep(1)
        if not cookies:
            state.driver.get("http://127.0.0.1:8000"); return
        state.loader = instaloader.Instaloader(user_agent=state.user_agent)
        user_id = ""
        for c in cookies:
            state.loader.context._session.cookies.set(c['name'], c['value'], domain=c.get('domain', '.instagram.com'), path=c.get('path', '/'))
            if c['name'] == 'ds_user_id': user_id = c['value']
        apply_secure_headers(state.loader.context)
        try:
            p = instaloader.Profile.from_id(state.loader.context, int(user_id))
            state.current_user = p.username
            state.current_user_avatar = p.profile_pic_url
        except: state.current_user = "Utente"
        state.loader.save_session_to_file(os.path.join(state.session_dir, f"session_{state.current_user}"))
        log("Software Online", "success")
        state.driver.get("http://127.0.0.1:8000")
    except: state.driver.get("http://127.0.0.1:8000")

@app.post("/api/set_target")
async def set_target(req: Request):
    data = await req.json()
    t = data.get("username")
    log(f"Analisi @{t}...")
    try:
        apply_secure_headers(state.loader.context)
        p = instaloader.Profile.from_username(state.loader.context, t)
        state.target_info = {"name": p.username, "avatar": p.profile_pic_url, "bio": p.biography[:100], "id": p.userid, "count": p.mediacount}
        log(f"@{t} pronto.", "success")
        return {"status": "ok", "target": state.target_info}
    except Exception as e:
        log(f"Errore: {str(e)}", "error")
        return {"status": "error"}

@app.post("/api/start")
async def start_scrape(req: Request):
    data = await req.json()
    state.is_running = True; state.stop_requested = False
    threading.Thread(target=worker_v1, args=(data,), daemon=True).start()
    return {"status": "started"}

@app.post("/api/stop")
async def stop_scrape():
    state.stop_requested = True
    return {"status": "stopping"}

def session_download(url, path):
    try:
        resp = state.loader.context._session.get(url, timeout=30.0)
        with open(path, "wb") as f: f.write(resp.content)
        return True
    except: return False

def worker_v1(options):
    try:
        t = state.target_info["name"]; tid = state.target_info["id"]; total_goal = state.target_info["count"]
        user_root = os.path.join("downloads", t); os.makedirs(user_root, exist_ok=True)
        dirs = {"foto": os.path.join(user_root, "foto"), "video": os.path.join(user_root, "video"), "stories": os.path.join(user_root, "stories"), "highlights": os.path.join(user_root, "highlights")}
        state.post_count = 0
        if options.get("stories"):
            log("Ricerca Stories attive...")
            apply_secure_headers(state.loader.context)
            try:
                url = f"https://www.instagram.com/api/v1/feed/reels_media/?reel_ids={tid}"
                resp = state.loader.context._session.get(url).json()
                items = resp.get("reels", {}).get(str(tid), {}).get("items", [])
                if items:
                    os.makedirs(dirs["stories"], exist_ok=True)
                    for item in items:
                        code = item.get("code"); m_type = item.get("media_type")
                        if m_type == 1: session_download(item["image_versions2"]["candidates"][0]["url"], os.path.join(dirs["stories"], f"story_{code}.jpg"))
                        elif m_type == 2: session_download(item["video_versions"][0]["url"], os.path.join(dirs["stories"], f"story_{code}.mp4"))
                        state.post_count += 1
                    log(f"Scaricate {len(items)} storie.")
            except: pass
        if options.get("highlights"):
            log("Ricerca Highlights...")
            apply_secure_headers(state.loader.context)
            try:
                url = f"https://www.instagram.com/api/v1/highlights/{tid}/highlights_tray/"
                resp = state.loader.context._session.get(url).json()
                trays = resp.get("tray", [])
                if trays:
                    os.makedirs(dirs["highlights"], exist_ok=True)
                    for tray in trays:
                        tray_title = tray.get("title", "unnamed"); tray_id = tray.get("id")
                        log(f"Estrazione Highlight: {tray_title}...")
                        m_url = f"https://www.instagram.com/api/v1/feed/reels_media/?reel_ids={tray_id}"
                        m_items = state.loader.context._session.get(m_url).json().get("reels", {}).get(tray_id, {}).get("items", [])
                        for item in m_items:
                            code = item.get("code"); m_type = item.get("media_type")
                            if m_type == 1: session_download(item["image_versions2"]["candidates"][0]["url"], os.path.join(dirs["highlights"], f"{tray_title}_{code}.jpg"))
                            elif m_type == 2: session_download(item["video_versions"][0]["url"], os.path.join(dirs["highlights"], f"{tray_title}_{code}.mp4"))
                            state.post_count += 1
                    log(f"Highlights completati.")
            except: log("Errore durante l'accesso agli Highlights.", "info")
        if options.get("posts") or options.get("videos"):
            log(f"Inizio estrazione di {total_goal} post..."); next_max_id = ""
            while True:
                if state.stop_requested: break
                apply_secure_headers(state.loader.context)
                url = f"https://www.instagram.com/api/v1/feed/user/{tid}/"
                resp = state.loader.context._session.get(url, params={"count": 33, "max_id": next_max_id}).json()
                items = resp.get("items", [])
                for item in items:
                    if state.stop_requested: break
                    m_type = item.get("media_type"); code = item.get("code"); date = time.strftime("%Y-%m-%d_%H-%M-%S", time.gmtime(item.get("taken_at")))
                    if m_type == 1 and options.get("posts"):
                        os.makedirs(dirs["foto"], exist_ok=True)
                        session_download(item["image_versions2"]["candidates"][0]["url"], os.path.join(dirs["foto"], f"{date}_{code}.jpg"))
                    elif m_type == 2 and options.get("videos"):
                        os.makedirs(dirs["video"], exist_ok=True)
                        session_download(item["video_versions"][0]["url"], os.path.join(dirs["video"], f"{date}_{code}.mp4"))
                    elif m_type == 8:
                        for idx, sub in enumerate(item.get("carousel_media", [])):
                            sub_type = sub.get("media_type")
                            if sub_type == 1 and options.get("posts"):
                                os.makedirs(dirs["foto"], exist_ok=True)
                                session_download(sub["image_versions2"]["candidates"][0]["url"], os.path.join(dirs["foto"], f"{date}_{code}_{idx}.jpg"))
                            elif sub_type == 2 and options.get("videos"):
                                os.makedirs(dirs["video"], exist_ok=True)
                                session_download(sub["video_versions"][0]["url"], os.path.join(dirs["video"], f"{date}_{code}_{idx}.mp4"))
                    state.post_count += 1
                    log(f"[{state.post_count}/{total_goal}] Elaborazione {code}...", "info")
                    time.sleep(random.uniform(0.6, 1.8))
                next_max_id = resp.get("next_max_id")
                if not next_max_id or not items: break
                time.sleep(2)
        log("Operazione conclusa.", "success")
    except Exception as e: log(f"Errore: {str(e)}", "error")
    finally: state.is_running = False

if __name__ == "__main__":
    if not os.path.exists("downloads"): os.makedirs("downloads")
    if sys.stdout is None: sys.stdout = open(os.devnull, "w")
    if sys.stderr is None: sys.stderr = open(os.devnull, "w")
    
    # Avvio server in thread separato
    def run_server():
        uvicorn.run(app, host="127.0.0.1", port=8000, log_config=None)
    
    threading.Thread(target=run_server, daemon=True).start()
    
    # Logica di avvio browser
    threading.Thread(target=start_unified_browser, daemon=True).start()
    
    # Avvio Loader GUI (Main Thread)
    create_loader()
