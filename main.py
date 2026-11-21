import copy
import re
import flet as ft


CLIP_COLORS = {
    "None": "#333338",
    "Orange": "#E67E22",
    "Teal": "#1ABC9C",
    "Purple": "#9B59B6",
    "Lime": "#2ECC71",
    "Blue": "#3498DB",
    "Pink": "#E84393",
}

COLOR_LOOKS = {
    "Default": {"lift": 0.0, "gamma": 1.0, "gain": 1.0, "sat": 1.0},
    "Warm": {"lift": 0.03, "gamma": 1.05, "gain": 1.08, "sat": 1.2},
    "Cool": {"lift": -0.02, "gamma": 1.02, "gain": 0.98, "sat": 0.9},
    "Anime Pop": {"lift": 0.02, "gamma": 1.12, "gain": 1.15, "sat": 1.45},
    "Dramatic": {"lift": -0.06, "gamma": 1.3, "gain": 1.1, "sat": 0.85},
    "B&W": {"lift": 0.0, "gamma": 1.25, "gain": 1.1, "sat": 0.0},
}

# Every DaVinci Resolve 2D, 3D, Puppet Pin, Color & Custom AI Node (100% Free)
FUSION_NODE_CATALOG = [
    {"type": "4K UltraSmooth AI", "category": "Custom AI", "color": "#D32F2F", "desc": "Upscales to 3840x2160 4K + 60fps Optical Flow smoothing"},
    {"type": "PuppetPin3D", "category": "3D Mesh", "color": "#AD1457", "desc": "3D mesh warp pins to bend & animate limbs/objects in X/Y/Z"},
    {"type": "Camera3D", "category": "3D", "color": "#00838F", "desc": "3D virtual camera with FOV, Z-depth & perspective control"},
    {"type": "ImagePlane3D", "category": "3D", "color": "#00695C", "desc": "Places 2D video clip into full 3D X/Y/Z space"},
    {"type": "Shape3D", "category": "3D", "color": "#0277BD", "desc": "3D cube, sphere, cylinder & plane geometry generator"},
    {"type": "Merge3D", "category": "3D", "color": "#00897B", "desc": "Combines multiple 3D cameras, lights & objects into one scene"},
    {"type": "PointLight3D", "category": "3D", "color": "#F57F17", "desc": "3D scene lighting with shadow & intensity control"},
    {"type": "Renderer3D", "category": "3D", "color": "#283593", "desc": "Renders 3D scene camera view back into 2D 4K output"},
    {"type": "Transform", "category": "2D", "color": "#2980B9", "desc": "2D Position, Zoom, Rotation, Anchor & Flip"},
    {"type": "ColorCorrector", "category": "Color", "color": "#8E44AD", "desc": "Node-based Hue, Saturation, Contrast & Gain"},
    {"type": "OpticalFlow", "category": "Retime", "color": "#16A085", "desc": "Motion-estimated frame interpolation for silky smooth motion"},
    {"type": "Merge", "category": "Composite", "color": "#D35400", "desc": "Combines Foreground over Background with blend modes"},
    {"type": "Blur / Glow", "category": "Filter", "color": "#2C3E50", "desc": "Gaussian blur and cinematic highlight bloom"},
    {"type": "DeltaKeyer", "category": "Matte", "color": "#27AE60", "desc": "Clean green/blue screen chroma key extraction"},
    {"type": "Text+", "category": "Generator", "color": "#C0392B", "desc": "3D extruded vector title & anime caption typography"},
    {"type": "Tracker", "category": "Tracking", "color": "#546E7A", "desc": "Point & planar motion tracking for callouts"},
]

DEFAULT_STATE = {
    "media_pool": [],
    "active_clip": None,
    "cursor_tool": "select",  # "select", "razor", "trim"
    "selected_item": "None",
    "playhead_sec": 0.0,
    "is_playing": False,
    "trim_start": 0.0,
    "trim_end": 15.0,
    "bpm": 128,
    "speed_pct": 100.0,
    "markers": [],
    "timeline_cuts": [],
    # Fusion Node Pipeline (Remembers every node & effect)
    "fusion_nodes": [
        {"id": 1, "type": "MediaIn1", "category": "I/O", "color": "#3A3A40", "enabled": True, "desc": "Source Timeline Clip Input"},
        {"id": 2, "type": "ImagePlane3D", "category": "3D", "color": "#00695C", "enabled": True, "desc": "Maps clip onto 3D X/Y/Z plane"},
        {"id": 3, "type": "PuppetPin3D", "category": "3D Mesh", "color": "#AD1457", "enabled": True, "desc": "3D Mesh Puppet Pin Deformation"},
        {"id": 4, "type": "Renderer3D", "category": "3D", "color": "#283593", "enabled": True, "desc": "Renders 3D space through Camera3D"},
        {"id": 5, "type": "4K UltraSmooth AI", "category": "Custom AI", "color": "#D32F2F", "enabled": True, "desc": "3840x2160 4K Upscale + 60fps Optical Flow Smooth"},
        {"id": 6, "type": "MediaOut1", "category": "I/O", "color": "#3A3A40", "enabled": True, "desc": "Final Timeline Output"},
    ],
    "selected_node_id": 3,
    "ultra_4k_enabled": True,
    "smooth_60fps_enabled": True,
    # 3D Puppet Pins State
    "puppet_pins": [
        {"id": 1, "name": "Pin 1 (Head)", "x": 0.0, "y": 25.0, "z": 10.0},
        {"id": 2, "name": "Pin 2 (Core)", "x": 0.0, "y": 0.0, "z": 0.0},
    ],
    "selected_pin_id": 1,
    # 3D Transform State
    "pos_x": 0.0,
    "pos_y": 0.0,
    "pos_z": 0.0,
    "rot_x": 0.0,
    "rot_y": 0.0,
    "rot_z": 0.0,
    # Color Page
    "lift": 0.0,
    "gamma": 1.0,
    "gain": 1.0,
    "sat": 1.0,
    # Fairlight Audio Page
    "volume": 100,
    "voice_isolation": False,
    "dialogue_leveler": False,
    "normalize_audio": True,
    # Deliver Page
    "export_res": "3840x2160 (4K UltraSmooth 60fps)",
    "export_codec": "H.265 (HEVC 10-bit)",
}


def main(page: ft.Page):
    # Tuned for ZTE Blade A36 smooth touch response & low RAM usage
    page.title = "Resolve Studio 3D Mobile"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = "#161618"
    page.padding = 0
    page.spacing = 0

    # --- LOAD SAVED PROJECT STATE (REMEMBERS EVERY NODE, PIN & EFFECT) ---
    state = copy.deepcopy(DEFAULT_STATE)
    try:
        saved = page.client_storage.get("resolve_project_v2")
        if isinstance(saved, dict):
            for k, v in saved.items():
                if k in state:
                    state[k] = v
            state["is_playing"] = False
    except Exception:
        pass

    def persist_state():
        try:
            page.client_storage.set("resolve_project_v2", state)
        except Exception:
            pass

    def safe_float(val, default=0.0):
        try:
            return max(0.0, float(val))
        except (ValueError, TypeError):
            return default

    def safe_int(val, default=120):
        try:
            return max(40, min(260, int(float(val))))
        except (ValueError, TypeError):
            return default

    def format_tc(seconds: float) -> str:
        total_frames = int(round(seconds * 60))
        ff = total_frames % 60
        total_sec = total_frames // 60
        ss = total_sec % 60
        mm = (total_sec // 60) % 60
        hh = total_sec // 3600
        return f"{hh:02d}:{mm:02d}:{ss:02d}:{ff:02d}"

    def notify(msg: str, color: str = "#2E7D32"):
        snack = ft.SnackBar(ft.Text(msg, color="#FFFFFF", size=12), bgcolor=color, duration=2000)
        page.overlay.append(snack)
        snack.open = True
        page.update()

    # --- AUTO BEAT MARKER GENERATOR (EDIT PAGE) ---
    def generate_auto_beat_markers():
        bpm = safe_int(state.get("bpm", 128), 128)
        beat_interval = 60.0 / bpm
        start_t = state["trim_start"]
        end_t = max(start_t + 1.0, state["trim_end"])

        new_markers = [m for m in state["markers"] if not m.get("is_beat")]
        t = start_t
        beat_idx = 1
        while t <= end_t and beat_idx <= 64:
            new_markers.append({
                "time": round(t, 2),
                "label": f"B{beat_idx}",
                "is_beat": True,
            })
            t += beat_interval
            beat_idx += 1

        state["markers"] = new_markers
        persist_state()
        refresh_current_page()
        notify(f"Auto-Added {beat_idx - 1} Beat Markers at {bpm} BPM!", "#00897B")

    # --- AI COMMAND PARSER (CUT, TRIM, 3D & 4K) ---
    def execute_ai_command(prompt_text: str):
        text = (prompt_text or "").strip().lower()
        if not text:
            notify("Type a command like: 'cut from 3 to 12' or 'auto beat 140'", "#D32F2F")
            return

        time_tokens = re.findall(r"\d+:\d+|\d+(?:\.\d+)?", text)
        parsed_secs = []
        for tok in time_tokens:
            if ":" in tok:
                parts = tok.split(":")
                parsed_secs.append(int(parts[0]) * 60 + float(parts[1]))
            else:
                parsed_secs.append(float(tok))

        if "beat" in text or "bpm" in text:
            if parsed_secs:
                state["bpm"] = safe_int(parsed_secs[0], 128)
            generate_auto_beat_markers()
            return

        if "3d" in text or "rotate" in text or "tilt" in text:
            angle = parsed_secs[0] if parsed_secs else 15.0
            state["rot_y"] = angle
            state["rot_x"] = round(angle / 2, 1)
            persist_state()
            update_monitor_display()
            refresh_current_page()
            notify(f"AI Applied 3D Rotation (Yaw {angle}°, Pitch {state['rot_x']}°)", "#00838F")
            return

        if "4k" in text or "smooth" in text or "upscale" in text:
            state["ultra_4k_enabled"] = True
            state["smooth_60fps_enabled"] = True
            state["export_res"] = "3840x2160 (4K UltraSmooth 60fps)"
            if not any(n["type"] == "4K UltraSmooth AI" for n in state["fusion_nodes"]):
                new_id = max(n["id"] for n in state["fusion_nodes"]) + 1
                state["fusion_nodes"].insert(
                    -1,
                    {
                        "id": new_id,
                        "type": "4K UltraSmooth AI",
                        "category": "Custom AI",
                        "color": "#D32F2F",
                        "enabled": True,
                        "desc": "3840x2160 4K Upscale + 60fps Optical Flow Smooth",
                    },
                )
            persist_state()
            update_monitor_display()
            refresh_current_page()
            notify("AI Activated: 4K UltraSmooth 60fps Node!", "#6A1B9A")
            return

        if len(parsed_secs) >= 2:
            t1, t2 = sorted([parsed_secs[0], parsed_secs[1]])
            if t2 <= t1:
                t2 = t1 + 1.0
            state["trim_start"] = t1
            state["trim_end"] = t2
            state["playhead_sec"] = t1
