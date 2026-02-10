from flask import Flask, render_template
from flask import Flask, render_template, request, redirect, url_for
from models import db, Cabang, JenisPenjualan, JenisPengeluaran

app = Flask(__name__)



app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///toko.db'
db.init_app(app)


with app.app_context():
    db.create_all()



@app.route('/')
def home():
    return render_template('home.html')

@app.route('/penjualan')
def penjualan():
    return render_template('penjualan.html')

@app.route('/pengeluaran')
def pengeluaran():
    return render_template('pengeluaran.html')



@app.route('/pengaturan', methods=['GET', 'POST'])
def pengaturan():
    if request.method == 'POST':
        tipe = request.form.get('tipe')
        nama = request.form.get('nama')
        
        if tipe == 'cabang':
            baru = Cabang(nama=nama)
        elif tipe == 'penjualan':
            baru = JenisPenjualan(nama=nama)
        elif tipe == 'pengeluaran':
            baru = JenisPengeluaran(nama=nama)
            
        db.session.add(baru)
        db.session.commit()
        return redirect(url_for('pengaturan'))

    # Ambil data untuk ditampilkan di tabel
    list_cabang = Cabang.query.all()
    list_penjualan = JenisPenjualan.query.all()
    list_pengeluaran = JenisPengeluaran.query.all()
    
    return render_template('pengaturan.html', 
                           cabang=list_cabang, 
                           penjualan=list_penjualan, 
                           pengeluaran=list_pengeluaran)

@app.route('/pengaturan/edit/<string:tipe>/<int:id>', methods=['POST'])
def edit_master(tipe, id):
    nama_baru = request.form.get('nama_baru')
    
    if tipe == 'cabang':
        data = Cabang.query.get(id)
    elif tipe == 'penjualan':
        data = JenisPenjualan.query.get(id)
    elif tipe == 'pengeluaran':
        data = JenisPengeluaran.query.get(id)
    
    if data and nama_baru:
        data.nama = nama_baru
        db.session.commit()
    
    return redirect(url_for('pengaturan'))

@app.route('/pengaturan/hapus/<string:tipe>/<int:id>')
def hapus_master(tipe, id):
    if tipe == 'cabang':
        data = Cabang.query.get(id)
    elif tipe == 'penjualan':
        data = JenisPenjualan.query.get(id)
    elif tipe == 'pengeluaran':
        data = JenisPengeluaran.query.get(id)
    
    if data:
        db.session.delete(data)
        db.session.commit()
        
    return redirect(url_for('pengaturan'))

if __name__ == '__main__':
    app.run(debug=True)