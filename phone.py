#!/usr/bin/env python3
"""
CHIA SẺ MÀN HÌNH QUA WI-FI: máy chủ web nhỏ do main.py chạy trên Mac.

    Mac (main.py)  --Wi-Fi: http://<ip Mac>:8000/<mã>/-->  máy Dell (remote.py) / trình duyệt / điện thoại

- /<mã>/screen.jpg : ảnh màn hình Mac (2 camera + lệnh + XONG). App remote.py trên máy Dell lấy ảnh này, còn phím thì Dell gửi qua Bluetooth.
- /<mã>/           : trang web dự phòng (điện thoại / trình duyệt, Android lẫn iPhone): lệnh, XONG, góc servo, ảnh camera và nút bấm phím.
                     Nút trên trang đi qua Wi-Fi vào hàng đợi, vòng lặp chính của main.py gửi xuống Arduino qua USB như phím bàn phím.
- /<mã>/state      : trạng thái dạng JSON cho trang web.

- Hai máy cùng mạng Wi-Fi (hoặc cùng bắt điểm phát Wi-Fi của điện thoại) là đủ.
- Ở xa (khác mạng) thì chạy thêm `ngrok http 8000` rồi mở đường dẫn ngrok + /<mã>/.
- Mã 6 số ngẫu nhiên trong đường dẫn: người khác cùng mạng không đoán được để điều khiển cánh tay.
Chỉ dùng thư viện chuẩn của Python (http.server), không thêm gói mới.
"""

import json
import queue
import secrets
import socket
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import cv2

PHONE_KEYS = "adwsikjlhxzr"  # Phím được gửi qua Wi-Fi: các phím servo của firmware + R (chốt đích, Mac tự xử lý)
JPEG_QUALITY = 70


def stored_pin(path):
    """Mã 6 số giữ nguyên giữa các lần chạy: đọc từ tệp `path`, chưa có (hoặc hỏng) thì tạo mã ngẫu nhiên và ghi vào. Xóa tệp để đổi mã."""
    try:
        with open(path, encoding="utf-8") as f:
            pin = f.read().strip()
        if len(pin) == 6 and pin.isdigit():
            return pin
    except OSError:
        pass
    pin = f"{secrets.randbelow(10 ** 6):06d}"
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(pin + "\n")
    except OSError:
        pass  # Không ghi được thì mã chỉ dùng cho lần chạy này
    return pin


def lan_ip():
    """Địa chỉ IP của laptop trong mạng Wi-Fi (kết nối UDP không gửi gói nào, chỉ để hỏi hệ điều hành dùng card mạng nào)."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        s.close()


def status_of(plan, result):
    """Gói trạng thái gửi cho trang điện thoại, lấy từ Plan (control.py) và Result (success.py)."""
    nxt = result.next_move
    return {
        "state": result.state,              # done | moving | no_target | unreachable | relaxed
        "done": bool(result.done),
        "key": nxt.key if (nxt is not None and result.state == "moving") else None,
        "steps": nxt.steps if nxt is not None else 0,
        "degrees": nxt.degrees if nxt is not None else 0,
        "remaining": result.remaining,
        "count": result.count,
        "closer_mm": round(plan.move_closer_mm),
        "servo": [{"joint": m.joint, "now": m.now, "goal": m.goal, "ok": bool(ok)} for m, ok in zip(plan.moves, result.joints_ok)],
        "grip": plan.now[3] if len(plan.now) > 3 else None,
        "usb": bool(plan.usb_ok),
        "banner": plan.banner,
    }


def qr_text(text):
    """Mã QR của `text` để in ra Terminal (ô trắng / đen bằng màu nền ANSI, quét được cả trên Terminal nền tối lẫn nền sáng)."""
    try:
        matrix = cv2.QRCodeEncoder.create().encode(text)
    except Exception:
        return ""
    white, black, reset = "\x1b[47m  ", "\x1b[40m  ", "\x1b[0m"
    pad = 2
    n = matrix.shape[1]
    rows = [white * (n + 2 * pad) + reset] * pad
    for row in matrix:
        rows.append(white * pad + "".join(black if v < 128 else white for v in row) + white * pad + reset)
    rows += [white * (n + 2 * pad) + reset] * pad
    return "\n".join(rows)


class PhoneServer:
    """Máy chủ web chạy nền. main.py gọi update() mỗi khung hình và pop_keys() để lấy phím người dùng bấm trên điện thoại."""

    def __init__(self, port=8000, host="0.0.0.0", pin=None):
        self.pin = pin or f"{secrets.randbelow(10 ** 6):06d}"
        self.keys = queue.Queue()
        self.lock = threading.Lock()
        self.status = {}
        self.screen = None  # Ảnh màn hình laptop mới nhất (BGR), chỉ nén JPEG khi điện thoại xin
        self.httpd = ThreadingHTTPServer((host, port), self._handler())
        self.httpd.daemon_threads = True
        self.port = self.httpd.server_address[1]
        threading.Thread(target=self.httpd.serve_forever, daemon=True).start()

    def url(self, host=None):
        return f"http://{host or lan_ip()}:{self.port}/{self.pin}/"

    def update(self, status, screen=None):
        with self.lock:
            self.status = status
            if screen is not None:
                self.screen = screen

    def pop_keys(self):
        """Các phím điện thoại đã bấm từ lần gọi trước, đúng thứ tự."""
        out = []
        while True:
            try:
                out.append(self.keys.get_nowait())
            except queue.Empty:
                return out

    def close(self):
        self.httpd.shutdown()
        self.httpd.server_close()

    # ------------------------------------------------------------------ HTTP
    def _handler(self):
        server = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):  # Không in mỗi yêu cầu ra Terminal
                pass

            def _route(self):
                """Phần đường dẫn sau /<mã>/, None nếu sai mã."""
                parts = self.path.split("?")[0].split("/", 2)
                if len(parts) < 2 or not secrets.compare_digest(parts[1], server.pin):
                    return None
                return parts[2] if len(parts) > 2 else ""

            def _send(self, code, body=b"", ctype="text/plain; charset=utf-8"):
                self.send_response(code)
                self.send_header("Content-Type", ctype)
                self.send_header("Content-Length", str(len(body)))
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                self.wfile.write(body)

            def do_GET(self):
                route = self._route()
                if route is None:
                    return self._send(404, b"Sai duong dan: mo dung link main.py in ra")
                if route == "":
                    return self._send(200, PAGE.encode("utf-8"), "text/html; charset=utf-8")
                if route == "state":
                    with server.lock:
                        body = json.dumps(server.status).encode("utf-8")
                    return self._send(200, body, "application/json")
                if route == "screen.jpg":
                    with server.lock:
                        screen = server.screen
                    if screen is None:
                        return self._send(503, b"Chua co anh")
                    ok, jpg = cv2.imencode(".jpg", screen, [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY])
                    return self._send(200, jpg.tobytes() if ok else b"", "image/jpeg")
                return self._send(404, b"Khong co trang nay")

            def do_POST(self):
                route = self._route()
                key = route[4:] if route and route.startswith("key/") else ""
                if len(key) != 1 or key not in PHONE_KEYS:
                    return self._send(404, b"Phim khong hop le")
                server.keys.put(key)
                return self._send(204)

        return Handler


# ==============================================================================
# Trang web (một tệp, không tải gì từ internet)
# ==============================================================================
PAGE = """<!doctype html>
<html lang="vi">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>Cánh tay robot</title>
<style>
  :root { --bg:#191b1e; --card:#272a2e; --edge:#464c52; --ink:#f5f5f5; --muted:#a0a5aa;
          --amber:#ffb928; --amber-dk:#62401c; --green:#5ad76e; --green-dk:#2a5832; --red:#f55555; }
  * { box-sizing:border-box; -webkit-tap-highlight-color:transparent; }
  body { margin:0; background:var(--bg); color:var(--ink); font:16px/1.35 -apple-system, system-ui, "Segoe UI", Roboto, sans-serif;
         padding:12px 16px calc(16px + env(safe-area-inset-bottom)); }
  header { display:flex; align-items:center; justify-content:space-between; margin-bottom:10px; }
  h1 { font-size:18px; margin:0; }
  .dot { font-size:13px; color:var(--muted); display:flex; align-items:center; gap:6px; }
  .dot i { width:9px; height:9px; border-radius:50%; background:var(--amber); display:inline-block; }
  .dot.ok i { background:var(--green); } .dot.lost i { background:var(--red); }
  .card { background:var(--card); border:2px solid var(--edge); border-radius:14px; padding:12px 14px; }
  #cmd { display:flex; align-items:center; gap:14px; border-color:var(--amber); background:var(--amber-dk); min-height:92px; }
  #cmd.done { border-color:var(--green); background:var(--green-dk); }
  #cmd.bad { border-color:var(--red); background:#4a2222; }
  #cmd .key { flex:none; width:64px; height:64px; border-radius:12px; background:var(--amber); color:#1e1b19;
              font:700 38px/64px system-ui, sans-serif; text-align:center; }
  #cmd.done .key { background:var(--green); }
  #cmd .key:empty { display:none; }
  #cmd .big { font-size:24px; font-weight:700; }
  #cmd .sub { color:var(--amber); font-size:17px; font-weight:600; }
  #cmd.done .sub { color:var(--green); }
  #result { margin:10px 0; display:flex; justify-content:space-between; align-items:baseline; gap:8px; }
  #result b { font-size:20px; white-space:nowrap; } #result span { text-align:right; } #result.done b { color:var(--green); } #result span { color:var(--muted); font-size:14px; }
  .servos { display:grid; grid-template-columns:repeat(4, 1fr); gap:6px; }
  .servo { text-align:center; padding:8px 4px; }
  .servo.ok { border-color:var(--green); }
  .servo small { color:var(--muted); display:block; font-size:12px; }
  .servo b { font-size:18px; }
  .servo em { font-style:normal; display:block; font-size:12px; color:var(--muted); }
  .servo.ok em { color:var(--green); }
  #cam { margin:10px 0; padding:0; overflow:hidden; }
  #cam summary { padding:10px 14px; color:var(--muted); cursor:pointer; }
  #cam img { display:block; width:100%; }
  .pad { display:grid; grid-template-columns:auto 1fr 1fr; gap:8px; align-items:center; margin-top:10px; }
  .pad .lbl { color:var(--muted); font-size:14px; padding-right:4px; }
  button { appearance:none; border:2px solid var(--edge); background:var(--card); color:var(--ink); border-radius:12px;
           padding:10px 6px; min-height:58px; font:600 15px/1.2 system-ui, sans-serif; touch-action:manipulation; }
  button b { display:block; font-size:22px; }
  button.next { border-color:var(--amber); background:var(--amber-dk); box-shadow:0 0 0 3px rgba(255,185,40,.35); }
  button:active, button.hit { background:#3a3f45; transform:scale(.97); }
  .tools { display:grid; grid-template-columns:repeat(3, 1fr); gap:8px; margin-top:8px; }
  #banner { color:var(--amber); font-weight:600; margin-top:10px; }
  #banner:empty { display:none; }
  /* Máy tính (màn rộng): ảnh camera to bên trái, lệnh + nút bên phải */
  @media (min-width: 900px) {
    body { display:grid; grid-template-columns:minmax(0, 1fr) 420px; grid-template-rows:auto 1fr; gap:0 20px; max-width:1500px; margin:0 auto; }
    header { grid-column:1 / -1; }
    #cam { grid-column:1; grid-row:2; margin:0; align-self:start; }
    #side { grid-column:2; grid-row:2; }
  }
</style>
</head>
<body>
<header><h1>Cánh tay robot</h1><span id="link" class="dot"><i></i><span>Đang kết nối…</span></span></header>

<details id="cam" class="card"><summary>Ảnh 2 camera (chạm để mở)</summary><img id="camImg" alt="Màn hình laptop: 2 camera và lệnh"></details>

<div id="side">
<div id="cmd" class="card"><div class="key" id="cmdKey"></div><div><div class="big" id="cmdBig">…</div><div class="sub" id="cmdSub"></div></div></div>
<div id="result"><b id="resBig"></b><span id="resSub"></span></div>
<div class="servos" id="servos"></div>

<div class="pad">
  <span class="lbl">Đế</span><button data-k="a"><b>A</b>Sang phải</button><button data-k="d"><b>D</b>Sang trái</button>
  <span class="lbl">Vai</span><button data-k="w"><b>W</b>Nâng lên</button><button data-k="s"><b>S</b>Hạ xuống</button>
  <span class="lbl">Khuỷu</span><button data-k="i"><b>I</b>Lên</button><button data-k="k"><b>K</b>Xuống</button>
  <span class="lbl">Kẹp</span><button data-k="j"><b>J</b>Mở</button><button data-k="l"><b>L</b>Khép</button>
</div>
<div class="tools">
  <button data-k="h" data-ask="Đưa cả cánh tay về Home (90/90/90)?"><b>H</b>Về Home</button>
  <button data-k="x"><b>X</b>Kẹp nghỉ</button>
  <button data-k="z" data-ask="Ngắt xung cả 4 servo? Cánh tay sẽ tự sụp xuống."><b>Z</b>Nghỉ hết</button>
</div>
<div id="banner"></div>
</div>

<script>
const base = location.pathname.endsWith("/") ? location.pathname : location.pathname + "/";
const HDR = { "ngrok-skip-browser-warning": "1" };
const NAMES = { base: "Đế", shoulder: "Vai", elbow: "Khuỷu" };
const WORDS = { a: "Sang phải", d: "Sang trái", w: "Nâng lên", s: "Hạ xuống", i: "Khuỷu lên", k: "Khuỷu xuống" };
const STATES = {
  done: ["Không cần bấm thêm", "Cả 3 servo đã đúng góc"],
  no_target: ["Chưa thấy vật", "Đặt vật có màu lên tờ giấy A4"],
  relaxed: ["Tay đang nghỉ", "Bấm W A S D I K H để cấp xung lại"],
  unreachable: ["Vật ngoài tầm với", ""],
};
const $ = (id) => document.getElementById(id);

function show(st) {
  const cmd = $("cmd");
  cmd.className = "card" + (st.done ? " done" : st.state === "unreachable" ? " bad" : "");
  if (st.state === "moving") {
    $("cmdKey").textContent = st.key.toUpperCase();
    $("cmdBig").textContent = "Bấm " + st.key.toUpperCase() + " × " + st.steps;
    $("cmdSub").textContent = WORDS[st.key] + " " + st.degrees + "°" + (st.key === "a" || st.key === "d" ? " (nhìn theo cam ngang)" : "");
  } else {
    const [big, sub] = STATES[st.state] || ["…", ""];
    $("cmdKey").textContent = st.done ? "✓" : "";
    $("cmdBig").textContent = big;
    $("cmdSub").textContent = st.state === "unreachable" ? "Đặt vật gần đế thêm " + st.closer_mm + " mm" : sub;
  }
  $("result").className = st.done ? "done" : "";
  $("resBig").textContent = st.done ? "XONG!" : "CHƯA XONG";
  $("resSub").textContent = (st.state === "moving" ? "còn " + st.remaining + " lần bấm · " : "") + "thành công " + st.count + " lần";
  $("servos").innerHTML = st.servo.map((s) =>
    `<div class="card servo${s.ok ? " ok" : ""}"><small>${NAMES[s.joint]}</small><b>${s.now}°</b><em>${s.ok ? "✓ đúng" : "→ " + s.goal + "°"}</em></div>`
  ).join("") + `<div class="card servo"><small>Kẹp</small><b>${st.grip ?? "–"}°</b><em>không tính</em></div>`;
  document.querySelectorAll("button[data-k]").forEach((b) => b.classList.toggle("next", b.dataset.k === st.key));
  const link = $("link");
  link.className = "dot" + (st.usb ? " ok" : "");
  link.lastChild.textContent = st.usb ? "Arduino đã nối" : "Mô phỏng (chưa cắm Arduino)";
  $("banner").textContent = st.banner || "";
}

async function poll() {
  try {
    const r = await fetch(base + "state", { headers: HDR, cache: "no-store" });
    if (!r.ok) throw new Error(r.status);
    show(await r.json());
  } catch (e) {
    $("link").className = "dot lost";
    $("link").lastChild.textContent = "Mất kết nối laptop";
  }
  setTimeout(poll, 300);
}

async function press(btn) {
  if (btn.dataset.ask && !confirm(btn.dataset.ask)) return;
  btn.classList.add("hit");
  setTimeout(() => btn.classList.remove("hit"), 150);
  if (navigator.vibrate) navigator.vibrate(12);
  try { await fetch(base + "key/" + btn.dataset.k, { method: "POST", headers: HDR }); } catch (e) {}
}
document.querySelectorAll("button[data-k]").forEach((b) => b.addEventListener("click", () => press(b)));

const cam = $("cam"), img = $("camImg");
if (matchMedia("(min-width: 900px)").matches) cam.open = true;  // Màn rộng (máy tính): mở sẵn ảnh camera
function nextFrame() { if (cam.open) img.src = base + "screen.jpg?t=" + Date.now(); }
img.addEventListener("load", () => setTimeout(nextFrame, 250));
img.addEventListener("error", () => setTimeout(nextFrame, 1000));
cam.addEventListener("toggle", nextFrame);
poll();
</script>
</body>
</html>
"""
