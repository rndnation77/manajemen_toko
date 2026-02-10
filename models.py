from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

# ================= MASTER DATA =================

class Cabang(db.Model):
    """Model untuk menyimpan daftar cabang toko"""
    id = db.Column(db.Integer, primary_key=True)
    nama = db.Column(db.String(100), nullable=False)

class JenisPenjualan(db.Model):
    """Model untuk kategori barang (Accessories, Titanium, dll)"""
    id = db.Column(db.Integer, primary_key=True)
    nama = db.Column(db.String(100), nullable=False)

class JenisPengeluaran(db.Model):
    """Model untuk kategori biaya (Gaji, Listrik, dll)"""
    id = db.Column(db.Integer, primary_key=True)
    nama = db.Column(db.String(100), nullable=False)

class JenisPembayaran(db.Model):
    """Model untuk metode pembayaran (Cash, Transfer, QRIS, dll)"""
    id = db.Column(db.Integer, primary_key=True)
    nama = db.Column(db.String(100), nullable=False)


# ================= DATA TRANSAKSI =================

class Penjualan(db.Model):
    """Header transaksi penjualan per hari per cabang"""
    id = db.Column(db.Integer, primary_key=True)
    cabang_id = db.Column(db.Integer, db.ForeignKey('cabang.id'), nullable=False)
    tanggal = db.Column(db.Date, nullable=False)
    total_nominal = db.Column(db.Float, nullable=False) # Total gabungan semua rincian_item
    rincian_bayar = db.Column(db.Text) # String rincian metode: "Cash: 10000, TF: 5000"
    
    # Relationship: Menghubungkan satu header penjualan ke banyak rincian barang
    rincian_item = db.relationship('RincianPenjualan', backref='penjualan', cascade="all, delete-orphan")
    cabang = db.relationship('Cabang', backref='penjualan_header')

class RincianPenjualan(db.Model):
    """Detail nominal untuk setiap kategori barang dalam satu transaksi"""
    id = db.Column(db.Integer, primary_key=True)
    penjualan_id = db.Column(db.Integer, db.ForeignKey('penjualan.id'), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('jenis_penjualan.id'), nullable=False)
    nominal = db.Column(db.Float, nullable=False) # Nominal khusus untuk item ini
    
    item = db.relationship('JenisPenjualan')

class Pengeluaran(db.Model):
    """Model untuk mencatat pengeluaran operasional cabang"""
    id = db.Column(db.Integer, primary_key=True)
    cabang_id = db.Column(db.Integer, db.ForeignKey('cabang.id'), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('jenis_pengeluaran.id'), nullable=False)
    nominal = db.Column(db.Float, nullable=False)
    tanggal = db.Column(db.Date, nullable=False)

    cabang = db.relationship('Cabang', backref='pengeluaran_list')
    item = db.relationship('JenisPengeluaran', backref='pengeluaran_detail')