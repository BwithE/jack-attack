from flask import Flask, render_template, request
import time
import os

app = Flask(__name__)

# HID key map
KEYS = {
    'a': (0x00, 0x04), 'A': (0x02, 0x04),
    'b': (0x00, 0x05), 'B': (0x02, 0x05),
    'c': (0x00, 0x06), 'C': (0x02, 0x06),
    'd': (0x00, 0x07), 'D': (0x02, 0x07),
    'e': (0x00, 0x08), 'E': (0x02, 0x08),
    'f': (0x00, 0x09), 'F': (0x02, 0x09),
    'g': (0x00, 0x0A), 'G': (0x02, 0x0A),
    'h': (0x00, 0x0B), 'H': (0x02, 0x0B),
    'i': (0x00, 0x0C), 'I': (0x02, 0x0C),
    'j': (0x00, 0x0D), 'J': (0x02, 0x0D),
    'k': (0x00, 0x0E), 'K': (0x02, 0x0E),
    'l': (0x00, 0x0F), 'L': (0x02, 0x0F),
    'm': (0x00, 0x10), 'M': (0x02, 0x10),
    'n': (0x00, 0x11), 'N': (0x02, 0x11),
    'o': (0x00, 0x12), 'O': (0x02, 0x12),
    'p': (0x00, 0x13), 'P': (0x02, 0x13),
    'q': (0x00, 0x14), 'Q': (0x02, 0x14),
    'r': (0x00, 0x15), 'R': (0x02, 0x15),
    's': (0x00, 0x16), 'S': (0x02, 0x16),
    't': (0x00, 0x17), 'T': (0x02, 0x17),
    'u': (0x00, 0x18), 'U': (0x02, 0x18),
    'v': (0x00, 0x19), 'V': (0x02, 0x19),
    'w': (0x00, 0x1A), 'W': (0x02, 0x1A),
    'x': (0x00, 0x1B), 'X': (0x02, 0x1B),
    'y': (0x00, 0x1C), 'Y': (0x02, 0x1C),
    'z': (0x00, 0x1D), 'Z': (0x02, 0x1D),
    '1': (0x00, 0x1E), '!': (0x02, 0x1E),
    '2': (0x00, 0x1F), '@': (0x02, 0x1F),
    '3': (0x00, 0x20), '#': (0x02, 0x20),
    '4': (0x00, 0x21), '$': (0x02, 0x21),
    '5': (0x00, 0x22), '%': (0x02, 0x22),
    '6': (0x00, 0x23), '^': (0x02, 0x23),
    '7': (0x00, 0x24), '&': (0x02, 0x24),
    '8': (0x00, 0x25), '*': (0x02, 0x25),
    '9': (0x00, 0x26), '(': (0x02, 0x26),
    '0': (0x00, 0x27), ')': (0x02, 0x27),
    'ENTER': (0x00, 0x28), 'ESC': (0x00, 0x29),
    'BACKSPACE': (0x00, 0x2A), 'TAB': (0x00, 0x2B),
    'SPACE': (0x00, 0x2C),
    ' ': (0x00, 0x2C),
    '-': (0x00, 0x2D), '_': (0x02, 0x2D),
    '=': (0x00, 0x2E), '+': (0x02, 0x2E),
    '[': (0x00, 0x2F), '{': (0x02, 0x2F),
    ']': (0x00, 0x30), '}': (0x02, 0x30),
    '\\': (0x00, 0x31), '|': (0x02, 0x31),
    ';': (0x00, 0x33), ':': (0x02, 0x33),
    "'": (0x00, 0x34), '"': (0x02, 0x34),
    '`': (0x00, 0x35), '~': (0x02, 0x35),
    ',': (0x00, 0x36), '<': (0x02, 0x36),
    '.': (0x00, 0x37), '>': (0x02, 0x37),
    '/': (0x00, 0x38), '?': (0x02, 0x38),
    'CAPSLOCK': (0x00, 0x39),
    'F1': (0x00, 0x3A), 'F2': (0x00, 0x3B),
    'F3': (0x00, 0x3C), 'F4': (0x00, 0x3D),
    'F5': (0x00, 0x3E), 'F6': (0x00, 0x3F),
    'F7': (0x00, 0x40), 'F8': (0x00, 0x41),
    'F9': (0x00, 0x42), 'F10': (0x00, 0x43),
    'F11': (0x00, 0x44), 'F12': (0x00, 0x45),
    'CTRL': (0x01, 0x00), 'SHIFT': (0x02, 0x00),
    'ALT': (0x04, 0x00), 'GUI': (0x08, 0x00),
}

def send_key(mod, key):
    report = bytes([mod, 0x00, key, 0x00, 0x00, 0x00, 0x00, 0x00])
    release = bytes(8)

    try:
        with open("/dev/hidg0", "wb") as f:
            f.write(report)   # key press
            time.sleep(0.05)
            f.write(release)  # key release
            time.sleep(0.05)
    except Exception as e:
        print(f"[ERROR] Failed to send HID report: {e}")

def parse_input(raw: str) -> None:
    for line in raw.strip().splitlines():
        line = line.strip()
        if not line:
            continue

        # ── Handle DELAY X ──────────────────────────────
        if line.upper().startswith('DELAY'):
            parts = line.split()
            if len(parts) == 2:
                try:
                    seconds = float(parts[1])
                    print(f"[INFO] Delaying for {seconds} seconds…")
                    time.sleep(seconds)
                    continue  # Go to next line
                except ValueError:
                    print(f"[WARN] Invalid DELAY value: {line}")
            else:
                print(f"[WARN] Invalid DELAY format: {line}")
            continue

        # ── Process line as keystroke(s) ─────────────────
        tokens = line.split()
        for idx, token in enumerate(tokens):
            token_upper = token.upper()

            if '+' in token:
                mods = 0x00
                keycode = 0x00
                for part in token_upper.split('+'):
                    mod, code = KEYS.get(part, (None, None))
                    if mod is None:
                        print(f"[WARN] Unknown combo part: {part}")
                        continue
                    mods |= mod
                    if code:
                        keycode = code
                if keycode:
                    send_key(mods, keycode)

            elif token_upper in KEYS:
                mod, code = KEYS[token_upper]
                send_key(mod, code)

            else:
                for ch in token:
                    if ch in KEYS:
                        mod, code = KEYS[ch]
                        send_key(mod, code)
                    else:
                        print(f"[WARN] Unknown character: {ch}")

            # Add space unless next token is DELAY or SPACE
            if idx != len(tokens) - 1 and token_upper not in ['SPACE', 'DELAY']:
                mod, code = KEYS['SPACE']
                send_key(mod, code)


@app.route('/')
def home():
    return render_template('home.html', title='Home - JackAttack')



@app.route('/keystrokes', methods=['GET', 'POST'])
def keystrokes():
    preload_dir = '/opt/jackattack/scripts'
    scripts = {}

    if os.path.isdir(preload_dir):
        for root, dirs, files in os.walk(preload_dir):
            for filename in files:
                filepath = os.path.join(root, filename)
                rel_path = os.path.relpath(filepath, preload_dir)  # Show relative path in dropdown
                try:
                    with open(filepath, 'r') as f:
                        scripts[rel_path] = f.read()
                except Exception as e:
                    print(f"[ERROR] Could not read {filepath}: {e}")

    sent_text = None
    if request.method == 'POST':
        text = request.form.get('input', '')
        parse_input(text)
        sent_text = text

    return render_template('keystrokes.html', title='Keystrokes - JackAttack',
                           sent_text=sent_text, scripts=scripts)



@app.route('/usage')
def ap():
    return render_template('usage.html', title='Usage - JackAttack')


@app.route('/about')
def about():
    return render_template('about.html', title='About - JackAttack')


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80)
