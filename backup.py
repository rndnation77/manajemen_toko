import shutil
import os
from datetime import datetime

# Konfigurasi path
source = 'instance/toko.db'
backup_dir = 'backups'

# Buat folder backup jika belum ada
if not os.path.exists(backup_dir):
    os.makedirs(backup_dir)

# Nama file backup dengan timestamp
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
destination = f'{backup_dir}/toko_backup_{timestamp}.db'

try:
    shutil.copy2(source, destination)
    print(f"Backup berhasil disimpan di: {destination}")
except FileNotFoundError:
    print("Error: File database tidak ditemukan. Pastikan folder instance sudah benar.")