import os
if os.path.exists('.env'):
    with open('.env') as _f:
        for _l in _f:
            if '=' in _l and not _l.startswith('#'):
                _k, _v = _l.strip().split('=', 1)
                os.environ.setdefault(_k, _v)

import paramiko
import os
import json
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(os.environ.get('PROXMOX_HOST', '192.168.1.100'), username='root', password=os.environ.get('PROXMOX_PASSWORD', ''))

def create_pwa_icon(size, is_maskable=False):
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Background gradient or circle/squircle
    margin = 0 if is_maskable else int(size * 0.05)
    
    # Draw rounded rect / squircle
    radius = int(size * 0.22) if not is_maskable else int(size * 0.1)
    
    # Gradient background simulation
    steps = 100
    for i in range(steps):
        ratio = i / steps
        r = int(99 + (236 - 99) * ratio)
        g = int(102 + (72 - 102) * ratio)
        b = int(241 + (153 - 241) * ratio)
        draw.rounded_rectangle([margin, margin, size - margin, size - margin], radius=radius, fill=(r, g, b, 255))
        break
        
    # Draw icon graphic (sparkles / AI motif)
    cx, cy = size // 2, size // 2
    sparkle_color = (255, 255, 255, 245)
    
    # 4-point star in center
    star_radius = int(size * 0.28)
    inner_radius = int(size * 0.08)
    
    points = [
        (cx, cy - star_radius),
        (cx + inner_radius, cy - inner_radius),
        (cx + star_radius, cy),
        (cx + inner_radius, cy + inner_radius),
        (cx, cy + star_radius),
        (cx - inner_radius, cy + inner_radius),
        (cx - star_radius, cy),
        (cx - inner_radius, cy - inner_radius),
    ]
    draw.polygon(points, fill=sparkle_color)
    
    # Secondary smaller star top-right
    s2_cx = cx + int(size * 0.22)
    s2_cy = cy - int(size * 0.22)
    s2_r = int(size * 0.1)
    s2_ir = int(size * 0.03)
    p2 = [
        (s2_cx, s2_cy - s2_r),
        (s2_cx + s2_ir, s2_cy - s2_ir),
        (s2_cx + s2_r, s2_cy),
        (s2_cx + s2_ir, s2_cy + s2_ir),
        (s2_cx, s2_cy + s2_r),
        (s2_cx - s2_ir, s2_cy + s2_ir),
        (s2_cx - s2_r, s2_cy),
        (s2_cx - s2_ir, s2_cy - s2_ir),
    ]
    draw.polygon(p2, fill=(255, 255, 255, 220))
    
    return img

# Generate icons
icon_192 = create_pwa_icon(192)
icon_512 = create_pwa_icon(512)
icon_maskable = create_pwa_icon(512, is_maskable=True)

# Push icons to server
sftp = ssh.open_sftp()

b192 = BytesIO()
icon_192.save(b192, format="PNG")
with sftp.file('/tmp/icon-192.png', 'wb') as f:
    f.write(b192.getvalue())

b512 = BytesIO()
icon_512.save(b512, format="PNG")
with sftp.file('/tmp/icon-512.png', 'wb') as f:
    f.write(b512.getvalue())

bmask = BytesIO()
icon_maskable.save(bmask, format="PNG")
with sftp.file('/tmp/icon-maskable-512.png', 'wb') as f:
    f.write(bmask.getvalue())

# Generate manifest.json
manifest_data = {
    "name": "AI Studio Marcel",
    "short_name": "AI Studio",
    "description": "Studio d'Intelligence Artificielle Dédié - Images, Voix, Vidéos & Téléchargements",
    "start_url": "/",
    "scope": "/",
    "display": "standalone",
    "orientation": "any",
    "background_color": "#08090d",
    "theme_color": "#08090d",
    "icons": [
        {
            "src": "/icon-192.png",
            "sizes": "192x192",
            "type": "image/png",
            "purpose": "any"
        },
        {
            "src": "/icon-512.png",
            "sizes": "512x512",
            "type": "image/png",
            "purpose": "any"
        },
        {
            "src": "/icon-maskable-512.png",
            "sizes": "512x512",
            "type": "image/png",
            "purpose": "maskable"
        }
    ]
}

with sftp.file('/tmp/manifest.json', 'w') as f:
    json.dump(manifest_data, f, indent=2)

# Generate sw.js (Service Worker)
sw_content = """// AI Studio Marcel Service Worker
const CACHE_NAME = 'aistudio-shell-v1';
const ASSETS_TO_CACHE = [
    '/',
    '/index.html',
    '/manifest.json',
    '/icon-192.png',
    '/icon-512.png'
];

self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) => {
            return cache.addAll(ASSETS_TO_CACHE);
        })
    );
    self.skipWaiting();
});

self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys().then((keys) => {
            return Promise.all(
                keys.map((key) => {
                    if (key !== CACHE_NAME) {
                        return caches.delete(key);
                    }
                })
            );
        })
    );
    self.clients.claim();
});

self.addEventListener('fetch', (event) => {
    // Only cache GET requests and non-API / non-proxy calls
    const url = new URL(event.request.url);
    if (event.request.method !== 'GET' || 
        url.pathname.startsWith('/api/') || 
        url.pathname.startsWith('/fooocus/') || 
        url.pathname.startsWith('/tts/') || 
        url.pathname.startsWith('/comfy/')) {
        return;
    }

    event.respondWith(
        fetch(event.request).catch(() => {
            return caches.match(event.request);
        })
    );
});
"""

with sftp.file('/tmp/sw.js', 'w') as f:
    f.write(sw_content)

sftp.close()

# Move files to LXC 100 /var/www/html/
cmds = [
    "pct push 100 /tmp/icon-192.png /var/www/html/icon-192.png",
    "pct push 100 /tmp/icon-512.png /var/www/html/icon-512.png",
    "pct push 100 /tmp/icon-maskable-512.png /var/www/html/icon-maskable-512.png",
    "pct push 100 /tmp/manifest.json /var/www/html/manifest.json",
    "pct push 100 /tmp/sw.js /var/www/html/sw.js",
    "pct exec 100 -- chmod 644 /var/www/html/icon* /var/www/html/manifest.json /var/www/html/sw.js"
]

for cmd in cmds:
    print(f"Exec: {cmd}")
    stdin, stdout, stderr = ssh.exec_command(cmd)
    print(stdout.read().decode())

ssh.close()
print("PWA base assets deployed!")
