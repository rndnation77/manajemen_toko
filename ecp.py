import pandas as pd
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.units import cm

def excel_to_pdf_manual(input_file, output_pdf):
    # 1. Membaca data (Mendukung CSV dan Excel)
    try:
        if input_file.endswith('.csv'):
            df = pd.read_csv(input_file)
        else:
            df = pd.read_excel(input_file)
    except Exception as e:
        print(f"Error membaca file: {e}")
        return

    # 2. REVISI: Hapus tulisan 'nan' dan biarkan kosong untuk tulis manual
    df = df.fillna('')

    # Pastikan nama kolom bersih
    df.columns = [col if not col.startswith('Unnamed') else '' for col in df.columns]

    # 3. Setup Dokumen PDF (A4 Portrait)
    doc = SimpleDocTemplate(output_pdf, pagesize=A4, 
                            rightMargin=1*cm, leftMargin=1*cm, 
                            topMargin=1*cm, bottomMargin=1*cm)
    elements = []

    # 4. Konversi DataFrame ke List
    data = [df.columns.values.tolist()] + df.values.tolist()

    # 5. Atur Lebar Kolom (Total Lebar A4 ~19cm setelah margin)
    # Urutan kolom: No, Kategori, Kode, Nama Barang, STOCK
    col_widths = [0.8*cm, 2.5*cm, 3.5*cm, 10.2*cm, 2.0*cm]

    # 6. Buat Tabel dan Style khusus tulis tangan
    # repeatRows=1 memastikan judul kolom muncul di tiap halaman
    table = Table(data, colWidths=col_widths, repeatRows=1)
    
    style = TableStyle([
        # Header Biru sesuai tema aplikasi Manajemen Toko Anda
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4361ee')), 
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 7),
        
        # REVISI: Garis hitam tegas (GRID) agar mudah dilihat saat menulis manual
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black), 
        
        # REVISI: Tambahkan PADDING (ruang) agar baris lebih tinggi untuk tulisan tangan
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        
        # Baris selang-seling tipis untuk membantu mata melihat baris
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fc')])
    ])
    table.setStyle(style)

    # 7. Bangun PDF
    elements.append(table)
    try:
        doc.build(elements)
        print(f"Berhasil! PDF untuk tulis manual tersimpan di: {output_pdf}")
    except Exception as e:
        print(f"Gagal membuat PDF: {e}")

# Jalankan script
if __name__ == "__main__":
    # Sesuaikan path file sesuai lokasi di Arch/Kali Linux Anda
    file_input = '/home/mazor/Documents/data.xlsx' 
    file_output = 'Daftar_Barang_Manual.pdf'
    
    excel_to_pdf_manual(file_input, file_output)