import os
import calendar
import pandas as pd
from io import BytesIO
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, send_file
from sqlalchemy import extract
from models import db, Cabang, JenisPenjualan, JenisPengeluaran, JenisPembayaran, Penjualan, RincianPenjualan, Pengeluaran

app = Flask(__name__)

# Konfigurasi Path Database
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'instance', 'toko.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

def clean_date(date_str):
    """Memastikan format tanggal hanya YYYY-MM-DD"""
    try:
        return datetime.strptime(date_str[:10], '%Y-%m-%d').date()
    except (ValueError, TypeError):
        return datetime.now().date()

with app.app_context():
    if not os.path.exists(os.path.join(basedir, 'instance')):
        os.makedirs(os.path.join(basedir, 'instance'))
    db.create_all()

# ================= DASHBOARD =================
@app.route('/')
def home():
    bulan_pilih = request.args.get('bulan', datetime.now().strftime('%Y-%m'))
    cabang_id = request.args.get('cabang_id', 'semua')
    
    try:
        tahun, bulan = map(int, bulan_pilih.split('-'))
    except:
        tahun, bulan = datetime.now().year, datetime.now().month

    num_days = calendar.monthrange(tahun, bulan)[1]
    labels = [str(d) for d in range(1, num_days + 1)]
    
    q_jual_harian = db.session.query(extract('day', Penjualan.tanggal), db.func.sum(Penjualan.total_nominal)).filter(
        extract('year', Penjualan.tanggal) == tahun, extract('month', Penjualan.tanggal) == bulan
    )
    q_keluar_harian = db.session.query(extract('day', Pengeluaran.tanggal), db.func.sum(Pengeluaran.nominal)).filter(
        extract('year', Pengeluaran.tanggal) == tahun, extract('month', Pengeluaran.tanggal) == bulan
    )
    q_kategori = db.session.query(
        JenisPenjualan.nama, 
        db.func.sum(RincianPenjualan.nominal)
    ).join(RincianPenjualan, JenisPenjualan.id == RincianPenjualan.item_id)\
     .join(Penjualan, Penjualan.id == RincianPenjualan.penjualan_id)\
     .filter(extract('year', Penjualan.tanggal) == tahun, extract('month', Penjualan.tanggal) == bulan)

    if cabang_id != 'semua':
        cid = int(cabang_id)
        q_jual_harian = q_jual_harian.filter(Penjualan.cabang_id == cid)
        q_keluar_harian = q_keluar_harian.filter(Pengeluaran.cabang_id == cid)
        q_kategori = q_kategori.filter(Penjualan.cabang_id == cid)

    jual_harian = q_jual_harian.group_by(extract('day', Penjualan.tanggal)).all()
    keluar_harian = q_keluar_harian.group_by(extract('day', Pengeluaran.tanggal)).all()
    stats_kategori = q_kategori.group_by(JenisPenjualan.nama).all()

    data_jual = [0] * num_days
    for d, val in jual_harian: data_jual[int(d)-1] = val
    data_keluar = [0] * num_days
    for d, val in keluar_harian: data_keluar[int(d)-1] = val

    cat_labels = [row[0] for row in stats_kategori]
    cat_values = [row[1] for row in stats_kategori]

    return render_template('home.html', 
                           total_jual=sum(data_jual), 
                           total_keluar=sum(data_keluar), 
                           laba_bersih=sum(data_jual) - sum(data_keluar), 
                           bulan_pilih=bulan_pilih, 
                           cabang_pilih=cabang_id,
                           cabang_list=Cabang.query.all(),
                           labels=labels, 
                           data_jual=data_jual, 
                           data_keluar=data_keluar,
                           cat_labels=cat_labels,
                           cat_values=cat_values,
                           stats_kategori=stats_kategori)

# ================= PENJUALAN =================
@app.route('/penjualan')
def penjualan():
    return render_template('penjualan.html', 
                           cabang=Cabang.query.all(), 
                           master_penjualan=JenisPenjualan.query.all(),
                           master_pembayaran=JenisPembayaran.query.all(),
                           riwayat_penjualan=Penjualan.query.order_by(Penjualan.tanggal.desc()).all())

@app.route('/simpan_penjualan', methods=['POST'])
def simpan_penjualan():
    id_cabang = request.form.get('id_cabang')
    tgl_input = request.form.get('tanggal')
    tanggal_obj = clean_date(tgl_input)

    item_ids = request.form.getlist('id_item[]')
    semua_metode = JenisPembayaran.query.all()
    
    grand_total_transaksi = 0
    list_rincian_bayar_teks = []
    rincian_obj_list = []

    for i in range(len(item_ids)):
        if item_ids[i]:
            nominal_per_item = 0
            for metode in semua_metode:
                key = f'nominal_{i}_{metode.id}'
                nom = request.form.get(key, 0)
                if nom and float(nom) > 0:
                    nominal_per_item += float(nom)
                    list_rincian_bayar_teks.append(f"{metode.nama}: {nom}")

            if nominal_per_item > 0:
                rincian = RincianPenjualan(item_id=item_ids[i], nominal=nominal_per_item)
                rincian_obj_list.append(rincian)
                grand_total_transaksi += nominal_per_item

    if rincian_obj_list:
        baru_penjualan = Penjualan(
            cabang_id=id_cabang,
            tanggal=tanggal_obj,
            total_nominal=grand_total_transaksi,
            rincian_bayar=", ".join(list_rincian_bayar_teks),
            rincian_item=rincian_obj_list
        )
        db.session.add(baru_penjualan)
        db.session.commit()

    return redirect(url_for('penjualan'))

# Fitur Baru: Hapus Penjualan
@app.route('/hapus_penjualan/<int:id>')
def hapus_penjualan(id):
    data = Penjualan.query.get(id)
    if data:
        db.session.delete(data)
        db.session.commit()
    return redirect(url_for('penjualan'))

# ================= PENGELUARAN & PENGATURAN =================
@app.route('/pengeluaran')
def pengeluaran():
    return render_template('pengeluaran.html', 
        cabang=Cabang.query.all(), 
        master_pengeluaran=JenisPengeluaran.query.all(),
        riwayat_pengeluaran=Pengeluaran.query.order_by(Pengeluaran.tanggal.desc()).all())

@app.route('/simpan_pengeluaran', methods=['POST'])
def simpan_pengeluaran():
    id_cabang = request.form.get('id_cabang')
    tgl_input = request.form.get('tanggal')
    items = request.form.getlist('id_item[]')
    nominals = request.form.getlist('nominal[]')
    tanggal_obj = clean_date(tgl_input)
    for i in range(len(items)):
        if items[i] and nominals[i]:
            db.session.add(Pengeluaran(cabang_id=id_cabang, item_id=items[i], nominal=float(nominals[i]), tanggal=tanggal_obj))
    db.session.commit()
    return redirect(url_for('pengeluaran'))

# Fitur Baru: Hapus Pengeluaran
@app.route('/hapus_pengeluaran/<int:id>')
def hapus_pengeluaran(id):
    data = Pengeluaran.query.get(id)
    if data:
        db.session.delete(data)
        db.session.commit()
    return redirect(url_for('pengeluaran'))

@app.route('/pengaturan', methods=['GET', 'POST'])
def pengaturan():
    if request.method == 'POST':
        tipe = request.form.get('tipe')
        nama = request.form.get('nama')
        mapping = {
            'cabang': Cabang, 'penjualan': JenisPenjualan, 
            'pengeluaran': JenisPengeluaran, 'pembayaran': JenisPembayaran
        }
        if tipe in mapping and nama:
            db.session.add(mapping[tipe](nama=nama))
            db.session.commit()
        return redirect(url_for('pengaturan'))
    return render_template('pengaturan.html', 
        cabang=Cabang.query.all(), penjualan=JenisPenjualan.query.all(), 
        pengeluaran=JenisPengeluaran.query.all(), pembayaran=JenisPembayaran.query.all())

@app.route('/pengaturan/edit/<string:tipe>/<int:id>', methods=['POST'])
def edit_master(tipe, id):
    nama_baru = request.form.get('nama_baru')
    mapping = {'cabang': Cabang, 'penjualan': JenisPenjualan, 'pengeluaran': JenisPengeluaran, 'pembayaran': JenisPembayaran}
    model = mapping.get(tipe)
    data = model.query.get(id) if model else None
    if data and nama_baru:
        data.nama = nama_baru
        db.session.commit()
    return redirect(url_for('pengaturan'))

@app.route('/pengaturan/hapus/<string:tipe>/<int:id>')
def hapus_master(tipe, id):
    mapping = {'cabang': Cabang, 'penjualan': JenisPenjualan, 'pengeluaran': JenisPengeluaran, 'pembayaran': JenisPembayaran}
    model = mapping.get(tipe)
    data = model.query.get(id) if model else None
    if data:
        db.session.delete(data)
        db.session.commit()
    return redirect(url_for('pengaturan'))

# ================= LAPORAN (Multiple Sheets & Pivot) =================
@app.route('/laporan', methods=['GET'])
def laporan():
    cabang_id = request.args.get('cabang_id')
    tgl_mulai = request.args.get('tgl_mulai')
    tgl_akhir = request.args.get('tgl_akhir')
    export = request.args.get('export')

    query_jual = RincianPenjualan.query.join(Penjualan)
    query_keluar = Pengeluaran.query

    if cabang_id and cabang_id != "semua":
        cabang_id = int(cabang_id)
        query_jual = query_jual.filter(Penjualan.cabang_id == cabang_id)
        query_keluar = query_keluar.filter(Pengeluaran.cabang_id == cabang_id)
        nama_cabang = Cabang.query.get(cabang_id).nama
    else:
        nama_cabang = "SEMUA CABANG"

    if tgl_mulai and tgl_akhir:
        query_jual = query_jual.filter(Penjualan.tanggal.between(tgl_mulai, tgl_akhir))
        query_keluar = query_keluar.filter(Pengeluaran.tanggal.between(tgl_mulai, tgl_akhir))

    data_jual = query_jual.all()
    data_keluar = query_keluar.all()

    if export == "excel":
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            workbook = writer.book
            money_fmt = workbook.add_format({'num_format': '"Rp "#,##0', 'align': 'right'})
            title_fmt = workbook.add_format({'bold': True, 'font_size': 14})

            if data_jual:
                rows = [{'Tanggal': d.penjualan.tanggal, 'Kategori': d.item.nama, 'Jumlah': d.nominal} for d in data_jual]
                df = pd.DataFrame(rows)
                pivot_kategori = df.pivot_table(index='Tanggal', columns='Kategori', values='Jumlah', aggfunc='sum', fill_value=0).reset_index()
                pivot_kategori.to_excel(writer, sheet_name='Penjualan', startrow=4, index=False)
                ws = writer.sheets['Penjualan']
                ws.write('A1', 'LAPORAN PENJUALAN', title_fmt)
                ws.write('A2', f'Cabang: {nama_cabang}')
                for col in range(1, len(pivot_kategori.columns)):
                    ws.set_column(col, col, 18, money_fmt)
                ws.set_column(0, 0, 12)

            if data_keluar:
                rows_k = [{'Tanggal': k.tanggal, 'Kategori': k.item.nama, 'Jumlah': k.nominal} for k in data_keluar]
                df2 = pd.DataFrame(rows_k)
                pivot_kategori2 = df2.pivot_table(index='Tanggal', columns='Kategori', values='Jumlah', aggfunc='sum', fill_value=0).reset_index()
                pivot_kategori2.to_excel(writer, sheet_name='Pengeluaran', startrow=4, index=False)
                ws2 = writer.sheets['Pengeluaran']
                ws2.write('A1', 'LAPORAN PENGELUARAN', title_fmt)
                ws2.write('A2', f'Cabang: {nama_cabang}')
                for col in range(1, len(pivot_kategori2.columns)):
                    ws2.set_column(col, col, 18, money_fmt)
                ws2.set_column(0, 0, 12)

        output.seek(0)
        return send_file(output, download_name=f"Laporan_{nama_cabang}_{datetime.now().strftime('%Y%m%d')}.xlsx", as_attachment=True)

    return render_template('laporan.html', cabang=Cabang.query.all(), data_jual=data_jual, data_keluar=data_keluar)

if __name__ == '__main__':
    app.run(debug=True)