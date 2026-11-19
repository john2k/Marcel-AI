import os
if os.path.exists('.env'):
    with open('.env') as _f:
        for _l in _f:
            if '=' in _l and not _l.startswith('#'):
                _k, _v = _l.strip().split('=', 1)
                os.environ.setdefault(_k, _v)

import os
import sys
import time
import paramiko

sys.stdout.reconfigure(encoding='utf-8', errors='backslashreplace')
sys.stderr.reconfigure(encoding='utf-8', errors='backslashreplace')

HOST = os.environ.get('PROXMOX_HOST', '192.168.1.100')
PORT = 22
USER = "root"
PASS = os.environ.get('PROXMOX_PASSWORD', '')

LOCAL_ISO = r"%USERPROFILE%\Project\Proxmox-2700x\TrueNAS-SCALE-25.10.7-HexOS.iso"
REMOTE_ISO_DIR = "/var/lib/vz/template/iso"
REMOTE_ISO = f"{REMOTE_ISO_DIR}/TrueNAS-SCALE-25.10.7-HexOS.iso"

def upload_progress(transferred, total):
    percent = (transferred / total) * 100
    mb_transferred = transferred / (1024 * 1024)
    mb_total = total / (1024 * 1024)
    sys.stdout.write(f"\r[UPLOAD] {mb_transferred:.1f}/{mb_total:.1f} MB ({percent:.1f}%)")
    sys.stdout.flush()

def main():
    print("=== [1/4] CONNEXION SSH ET SFTP ===")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, port=PORT, username=USER, password=PASS, timeout=15)

    sftp = client.open_sftp()
    
    # Vérifier si l'ISO est déjà sur l'hôte
    iso_exists = False
    try:
        remote_stat = sftp.stat(REMOTE_ISO)
        local_size = os.path.getsize(LOCAL_ISO)
        if remote_stat.st_size == local_size:
            print(f"[OK] L'ISO HexOS existe déjà sur le serveur ({local_size} octets). Pas besoin de re-téléverser.")
            iso_exists = True
        else:
            print(f"[!] L'ISO distante est incomplète ({remote_stat.st_size} vs {local_size}). Re-téléversement nécessaire.")
    except IOError:
        pass

    if not iso_exists:
        print(f"Téléversement de {LOCAL_ISO} vers {REMOTE_ISO}...")
        start_time = time.time()
        sftp.put(LOCAL_ISO, REMOTE_ISO, callback=upload_progress)
        duration = time.time() - start_time
        speed = (os.path.getsize(LOCAL_ISO) / (1024 * 1024)) / duration
        print(f"\n[OK] Téléversement terminé en {duration:.1f}s ({speed:.1f} MB/s)")

    sftp.close()

    # Script de préparation et création de la VM
    SETUP_SCRIPT = """#!/usr/bin/env bash
set -euo pipefail

echo "=== [2/4] REMISE A ZERO DES 3 DISQUES DURS POUR HEXOS/ZFS ==="
DISK_8TB="/dev/disk/by-id/ata-ST8000VN004-3CP101_WWZ2MCD8"
DISK_12TB_1="/dev/disk/by-id/ata-ST12000VN0007-2GS116_ZJV5FBBW"
DISK_12TB_2="/dev/disk/by-id/ata-ST12000VN0008-2PH103_ZLW2KWN5"

# Nettoyage des signatures précédentes
wipefs -a ${DISK_8TB}* || true
wipefs -a ${DISK_12TB_1}* || true
wipefs -a ${DISK_12TB_2}* || true

sgdisk -Z "$DISK_8TB"
sgdisk -Z "$DISK_12TB_1"
sgdisk -Z "$DISK_12TB_2"
partprobe
sleep 2

echo "=== [3/4] CREATION DE LA MACHINE VIRTUELLE HEXOS (VM 100) ==="
# Suppression si elle existe encore
qm stop 100 2>/dev/null || true
qm destroy 100 --purge 2>/dev/null || true

# Création de la VM
qm create 100 \\
  --name HexOS \\
  --ostype l26 \\
  --machine q35 \\
  --bios ovmf \\
  --cpu host \\
  --cores 4 \\
  --memory 16384 \\
  --balloon 0 \\
  --net0 virtio,bridge=vmbr0 \\
  --scsihw virtio-scsi-single \\
  --agent enabled=1 \\
  --onboot 1

# Disque EFI
qm set 100 --efidisk0 local-lvm:0,efitype=4m,pre-enrolled-keys=0

# Disque système dédié pour l installation de HexOS (64 Go sur local-lvm)
qm set 100 --scsi0 local-lvm:64,discard=on,ssd=1

# Lecteur CD-ROM avec l ISO HexOS
qm set 100 --ide2 local:iso/TrueNAS-SCALE-25.10.7-HexOS.iso,media=cdrom

# Passthrough des 3 disques durs pour le pool de stockage ZFS
qm set 100 --scsi1 "$DISK_8TB"
qm set 100 --scsi2 "$DISK_12TB_1"
qm set 100 --scsi3 "$DISK_12TB_2"

# Définition de l ordre de boot (d abord le CD-ROM pour lancer l installateur, puis le disque dur)
qm set 100 --boot order=ide2;scsi0

echo "Configuration de la VM HexOS :"
qm config 100

echo "=== [4/4] DEMARRAGE DE LA VM HEXOS ==="
qm start 100
echo "Statut VM 100 : $(qm status 100)"
"""

    sftp = client.open_sftp()
    with sftp.file("/tmp/setup_hexos.sh", "w") as f:
        f.write(SETUP_SCRIPT)
    sftp.close()

    print("Exécution du script de configuration sur Proxmox...")
    stdin, stdout, stderr = client.exec_command("chmod +x /tmp/setup_hexos.sh && /tmp/setup_hexos.sh", get_pty=True)
    for line in iter(stdout.readline, ""):
        print(line, end="")
    code = stdout.channel.recv_exit_status()
    client.close()
    return code

if __name__ == "__main__":
    sys.exit(main())
