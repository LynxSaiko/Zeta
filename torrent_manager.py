import os
import subprocess
import threading
import re
import signal
import time

def setup(app):
    # === AMBIL KEY DARI CONFIG ===
    key_start  = app.config.key("plugin_torrent")          # mulai download
    key_pause  = app.config.key("plugin_torrent_pause")   # pause
    key_resume = app.config.key("plugin_torrent_resume")  # resume
    key_stop   = app.config.key("plugin_torrent_stop")    # stop

    # === STORAGE PROSES TORRENT ===
    if not hasattr(app, "_torrent_procs"):
        app._torrent_procs = {}

    if not hasattr(app, "bg_paused"):
        app.bg_paused = False

    # ==============================
    # UTIL INTERNAL
    # ==============================

    def _make_id(path):
        try:
            st = os.stat(path)
            return f"{os.path.basename(path)}:{st.st_ino}"
        except Exception:
            return os.path.basename(path)

    def _register_proc(tid, proc):
        app._torrent_procs[tid] = proc

    def _unregister_proc(tid):
        try:
            del app._torrent_procs[tid]
        except KeyError:
            pass

    def _kill_proc(proc):
        try:
            os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
        except Exception:
            try:
                proc.kill()
            except Exception:
                pass

    # ==============================
    # START DOWNLOAD
    # ==============================

    def start_download():
        sel = app.current_panel.get_selected()
        if not sel:
            app.show_message("No file selected", 2)
            return True

        full_path = os.path.join(app.current_panel.path, sel)
        if not full_path.endswith(".torrent"):
            app.show_message("Select a .torrent file", 2)
            return True

        tid = _make_id(full_path)
        if tid in app._torrent_procs:
            app.show_message("Already downloading", 2)
            return True

        save_dir = app.current_panel.path

        # === SETUP UI BACKGROUND ===
        app.bg_task = "Torrent"
        app.bg_progress = 0
        app.bg_current = sel
        app.bg_done = False
        app.bg_paused = False

        cmd = [
            "aria2c",
            "--seed-time=0",
            "--summary-interval=1",
            "-d", save_dir,
            full_path
        ]

        try:
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                preexec_fn=os.setsid
            )
        except FileNotFoundError:
            app.show_message("aria2c not found. Install aria2.", 4)
            app.bg_task = None
            return True
        except Exception as e:
            app.show_message(f"Start error: {e}", 4)
            app.bg_task = None
            return True

        _register_proc(tid, proc)
        app.show_message("Starting torrent...", 2)

        # ==============================
        # THREAD PEMBACA OUTPUT ARIA2
        # ==============================

        def reader():
            speed = ""
            try:
                for line in proc.stdout:

                    # === JIKA DI-STOP DARI UI ===
                    if app.bg_done:
                        _kill_proc(proc)
                        break

                    # === JIKA PAUSED ===
                    if app.bg_paused:
                        time.sleep(0.5)
                        continue

                    # Contoh output:
                    # [#abcd  3.2MiB/1.0GiB(4%) CN:5 DL:1.2MiB ETA:01:23]

                    m = re.search(r'\((\d+)%\)', line)
                    if m:
                        try:
                            app.bg_progress = int(m.group(1))
                        except:
                            pass

                    m2 = re.search(r'DL:([^\s]+)', line)
                    if m2:
                        speed = m2.group(1)

                    m3 = re.search(r'ETA:([0-9:]+)', line)
                    if m3:
                        eta = m3.group(1)
                        app.bg_current = f"{sel} | {speed}/s ETA:{eta}"
                    else:
                        app.bg_current = f"{sel} | {speed}/s"

                proc.wait()

                # === SELESAI NORMAL ===
                if not app.bg_done:
                    app.bg_progress = 100
                    app.bg_done = True
                    app.show_message("Torrent complete", 4)
                    try:
                        app.current_panel.refresh_files()
                    except:
                        pass

                _unregister_proc(tid)

            except Exception as e:
                app.bg_done = True
                app.show_message(f"Torrent reader error: {e}", 4)
                _unregister_proc(tid)

            finally:
                if not app._torrent_procs:
                    app.bg_task = None
                    app.bg_paused = False

        threading.Thread(target=reader, daemon=True).start()
        return True

    # ==============================
    # PAUSE
    # ==============================

    def pause_all():
        if not app._torrent_procs:
            app.show_message("No torrent running", 2)
            return True

        for proc in app._torrent_procs.values():
            try:
                os.killpg(os.getpgid(proc.pid), signal.SIGSTOP)
            except Exception:
                pass

        app.bg_paused = True
        app.show_message("Torrent(s) paused", 2)
        return True

    # ==============================
    # RESUME
    # ==============================

    def resume_all():
        if not app._torrent_procs:
            app.show_message("No torrent running", 2)
            return True

        for proc in app._torrent_procs.values():
            try:
                os.killpg(os.getpgid(proc.pid), signal.SIGCONT)
            except Exception:
                pass

        app.bg_paused = False
        app.show_message("Torrent(s) resumed", 2)
        return True

    # ==============================
    # STOP
    # ==============================

    def stop_all():
        if not app._torrent_procs:
            app.show_message("No torrent running", 2)
            return True

        for tid, proc in list(app._torrent_procs.items()):
            _kill_proc(proc)
            _unregister_proc(tid)

        app.bg_done = True
        app.bg_paused = False
        app.bg_task = None
        app.bg_progress = 0
        app.bg_current = ""

        app.show_message("Torrent(s) stopped", 2)

        try:
            app.current_panel.refresh_files()
        except:
            pass

        return True

    # ==============================
    # REGISTER KE ZETA
    # ==============================

    if key_start:
        app.register_plugin_key(key_start, start_download)
    if key_pause:
        app.register_plugin_key(key_pause, pause_all)
    if key_resume:
        app.register_plugin_key(key_resume, resume_all)
    if key_stop:
        app.register_plugin_key(key_stop, stop_all)
