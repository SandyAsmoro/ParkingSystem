import tkinter as tk
from tkinter import ttk, messagebox
import mysql.connector
from datetime import datetime
import threading
import qrcode
from PIL import Image, ImageTk
import math

def setup_database():
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="parking_system"
        )
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS parking (
                id INT AUTO_INCREMENT PRIMARY KEY,
                plate_number VARCHAR(20) NOT NULL,
                vehicle_type VARCHAR(10) NOT NULL,
                check_in_time DATETIME NOT NULL,
                check_out_time DATETIME,
                total_fee DECIMAL(10, 2)
            )
        ''')
        conn.commit()
    except mysql.connector.Error as err:
        print(f"Error: {err}")
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

def connect_to_database():
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="parking_system"
        )
        return conn
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return None

class ParkingApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Sistem Parkiran")

        self.tab_control = ttk.Notebook(root)
        self.input_tab = ttk.Frame(self.tab_control)
        self.transaction_tab = ttk.Frame(self.tab_control)
        self.report_tab = ttk.Frame(self.tab_control)

        self.tab_control.add(self.input_tab, text="Form Input")
        self.tab_control.add(self.transaction_tab, text="Form Transaksi")
        self.tab_control.add(self.report_tab, text="Form Laporan")
        self.tab_control.pack(expand=1, fill="both")

        self.setup_input_tab()
        self.setup_transaction_tab()
        self.setup_report_tab()

    def setup_input_tab(self):
        tk.Label(self.input_tab, text="ID Parkir:").grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.parking_id_entry = tk.Entry(self.input_tab)
        self.parking_id_entry.grid(row=0, column=1, padx=10, pady=10, sticky="w")

        tk.Button(self.input_tab, text="Search", command=self.search_data).grid(row=0, column=2, padx=10, pady=10)

        tk.Label(self.input_tab, text="Plat Nomor:").grid(row=1, column=0, padx=10, pady=10, sticky="w")
        self.plate_entry = tk.Entry(self.input_tab)
        self.plate_entry.grid(row=1, column=1, padx=10, pady=10)

        tk.Label(self.input_tab, text="Jenis Kendaraan:").grid(row=2, column=0, padx=10, pady=10, sticky="w")
        self.vehicle_type = tk.StringVar(value="Mobil")
        tk.Radiobutton(self.input_tab, text="Mobil", variable=self.vehicle_type, value="Mobil").grid(row=2, column=1, sticky="w")
        tk.Radiobutton(self.input_tab, text="Motor", variable=self.vehicle_type, value="Motor").grid(row=2, column=2, sticky="w")

        tk.Label(self.input_tab, text="Tanggal dan Waktu Masuk:").grid(row=3, column=0, padx=10, pady=10, sticky="w")
        self.check_in_time = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        self.check_in_time_label = tk.Label(self.input_tab, textvariable=self.check_in_time)
        self.check_in_time_label.grid(row=3, column=1, padx=10, pady=10, sticky="w")

        tk.Button(self.input_tab, text="Submit", command=self.submit_data).grid(row=4, column=1, pady=10)

        tk.Button(self.input_tab, text="Update", command=self.update_data).grid(row=4, column=2, pady=10)

        self.qr_label = tk.Label(self.input_tab)
        self.qr_label.grid(row=0, column=3, rowspan=5, padx=10, pady=10)

        self.update_time()

    def update_time(self):
        self.check_in_time.set(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        self.root.after(1000, self.update_time)

    def search_data(self):
        parking_id = self.parking_id_entry.get().strip()
        if not parking_id.isdigit():
            messagebox.showerror("Error", "ID Parkir harus berupa angka!")
            return

        conn = connect_to_database()
        if conn is None:
            return

        cursor = conn.cursor()
        cursor.execute("SELECT plate_number, vehicle_type, check_in_time FROM parking WHERE id = %s AND check_out_time IS NULL", (parking_id,))
        result = cursor.fetchone()
        conn.close()

        if result:
            plate_number, vehicle_type, check_in_time = result
            self.plate_entry.delete(0, tk.END)
            self.plate_entry.insert(0, plate_number)
            self.vehicle_type.set(vehicle_type)
            self.check_in_time.set(check_in_time.strftime("%Y-%m-%d %H:%M:%S"))
        else:
            messagebox.showerror("Error", "Data tidak ditemukan atau kendaraan sudah check out!")

    def generate_qr_code(self, data):
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(data)
        qr.make(fit=True)
        img = qr.make_image(fill='black', back_color='white')
        img = img.resize((150, 150))
        return ImageTk.PhotoImage(img)

    def submit_data(self):
        parking_id = self.parking_id_entry.get().strip()
        plate_number = self.plate_entry.get()
        vehicle_type = self.vehicle_type.get()
        check_in_time = self.check_in_time.get()

        if parking_id and not parking_id.isdigit():
            messagebox.showerror("Error", "ID Parkir harus berupa angka!")
            return

        if not plate_number:
            messagebox.showerror("Error", "Plat nomor tidak boleh kosong!")
            return

        conn = connect_to_database()
        if conn is None:
            return

        cursor = conn.cursor()

        if parking_id:
            parking_id = int(parking_id)
            cursor.execute("INSERT INTO parking (id, plate_number, vehicle_type, check_in_time) VALUES (%s, %s, %s, %s) ON DUPLICATE KEY UPDATE plate_number = %s, vehicle_type = %s, check_in_time = %s", (parking_id, plate_number, vehicle_type, check_in_time, plate_number, vehicle_type, check_in_time))
        else:
            cursor.execute("INSERT INTO parking (plate_number, vehicle_type, check_in_time) VALUES (%s, %s, %s)", (plate_number, vehicle_type, check_in_time))
            parking_id = cursor.lastrowid

        conn.commit()
        conn.close()

        messagebox.showinfo("Sukses", "Data berhasil disimpan!")
        self.parking_id_entry.delete(0, tk.END)
        self.plate_entry.delete(0, tk.END)
        self.vehicle_type.set("Mobil")
        self.check_in_time.set(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

        qr_data = f"ID: {parking_id}\nPlat: {plate_number}\nJenis: {vehicle_type}\nMasuk: {check_in_time}"
        qr_image = self.generate_qr_code(qr_data)
        self.qr_label.config(image=qr_image)
        self.qr_label.image = qr_image

    def update_data(self):
        parking_id = self.parking_id_entry.get().strip()
        plate_number = self.plate_entry.get()
        vehicle_type = self.vehicle_type.get()

        if not parking_id.isdigit():
            messagebox.showerror("Error", "ID Parkir harus berupa angka!")
            return

        if not plate_number:
            messagebox.showerror("Error", "Plat nomor tidak boleh kosong!")
            return

        conn = connect_to_database()
        if conn is None:
            return

        cursor = conn.cursor()
        cursor.execute("UPDATE parking SET plate_number = %s, vehicle_type = %s WHERE id = %s", (plate_number, vehicle_type, parking_id))
        conn.commit()
        conn.close()

        messagebox.showinfo("Sukses", "Data berhasil diperbarui!")

    def setup_transaction_tab(self):
        tk.Label(self.transaction_tab, text="ID Parkir:").grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.transaction_parking_id_entry = tk.Entry(self.transaction_tab)
        self.transaction_parking_id_entry.grid(row=0, column=1, padx=10, pady=10)

        tk.Button(self.transaction_tab, text="Hitung Biaya", command=self.calculate_fee).grid(row=1, column=1, pady=10)

        tk.Label(self.transaction_tab, text="Detail Transaksi:").grid(row=3, column=0, padx=10, pady=10, sticky="w")
        self.transaction_details = tk.Text(self.transaction_tab, width=40, height=10, state="disabled")
        self.transaction_details.grid(row=3, column=1, columnspan=2, padx=10, pady=10)

    def calculate_fee(self):
        parking_id = self.transaction_parking_id_entry.get().strip()

        if not parking_id.isdigit():
            messagebox.showerror("Error", "ID Parkir harus berupa angka!")
            return

        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="parking_system"
        )
        cursor = conn.cursor()
        cursor.execute("SELECT check_in_time, vehicle_type FROM parking WHERE id = %s AND check_out_time IS NULL", (parking_id,))
        result = cursor.fetchone()

        if not result:
            messagebox.showerror("Error", "ID Parkir tidak ditemukan atau kendaraan sudah check out!")
            conn.close()
            return

        check_in_time, vehicle_type = result
        if isinstance(check_in_time, str):
            check_in_time = datetime.strptime(check_in_time, "%Y-%m-%d %H:%M:%S")

        check_out_time = datetime.now()
        duration_seconds = (check_out_time - check_in_time).total_seconds()
        duration_hours = duration_seconds / 3600

        hours = math.ceil(duration_hours)
        rate = 5000 if vehicle_type == "Motor" else 10000
        total_fee = hours * rate

        cursor.execute("UPDATE parking SET check_out_time = %s, total_fee = %s WHERE id = %s", (check_out_time, total_fee, parking_id))
        conn.commit()
        conn.close()

        self.total_fee_label.config(text=f"Rp {total_fee}")
    
        # minutes = int((duration_seconds % 3600) / 60)

        details = (
            f"ID Parkir: {parking_id}\n"
            f"Jenis Kendaraan: {vehicle_type}\n"
            f"Waktu Masuk: {check_in_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"Waktu Keluar: {check_out_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"Total Biaya: Rp {total_fee}"
        )
        self.transaction_details.config(state="normal")
        self.transaction_details.delete("1.0", tk.END)
        self.transaction_details.insert(tk.END, details)
        self.transaction_details.config(state="disabled")

        messagebox.showinfo("Sukses", "Transaksi berhasil disimpan!")


    def setup_report_tab(self):
        tk.Label(self.report_tab, text="Bulan:").grid(row=0, column=0, padx=10, pady=10, sticky="w")
        
        month_names = [
            ("Januari", "01"),
            ("Februari", "02"),
            ("Maret", "03"),
            ("April", "04"),
            ("Mei", "05"),
            ("Juni", "06"),
            ("Juli", "07"),
            ("Agustus", "08"),
            ("September", "09"),
            ("Oktober", "10"),
            ("November", "11"),
            ("Desember", "12")
        ]
        
        self.month_combobox = ttk.Combobox(self.report_tab, values=[name for name, _ in month_names], state="readonly")
        self.month_combobox.grid(row=0, column=1, padx=10, pady=10)

        tk.Button(self.report_tab, text="Tampilkan", command=self.show_report).grid(row=1, column=1, pady=10)

        self.report_table = ttk.Treeview(self.report_tab, columns=("ID", "Plat Nomor", "Jenis", "Masuk", "Keluar", "Biaya"), show="headings")
        self.report_table.heading("ID", text="ID")
        self.report_table.heading("Plat Nomor", text="Plat Nomor")
        self.report_table.heading("Jenis", text="Jenis")
        self.report_table.heading("Masuk", text="Masuk")
        self.report_table.heading("Keluar", text="Keluar")
        self.report_table.heading("Biaya", text="Biaya")

        self.report_table.grid(row=2, column=0, columnspan=2, padx=10, pady=10)

        tk.Button(self.report_tab, text="Hapus", command=self.delete_report_entry).grid(row=3, column=1, pady=10)

        tk.Label(self.report_tab, text="Total Biaya Bulan Ini:").grid(row=4, column=0, padx=10, pady=10, sticky="w")
        self.total_fee_label = tk.Label(self.report_tab, text="Rp 0")
        self.total_fee_label.grid(row=4, column=1, padx=10, pady=10, sticky="w")

    def show_report(self):
        month_name = self.month_combobox.get()

        if not month_name:
            messagebox.showerror("Error", "Pilih bulan terlebih dahulu!")
            return

        month_mapping = {
            "Januari": "01",
            "Februari": "02",
            "Maret": "03",
            "April": "04",
            "Mei": "05",
            "Juni": "06",
            "Juli": "07",
            "Agustus": "08",
            "September": "09",
            "Oktober": "10",
            "November": "11",
            "Desember": "12"
        }

        month = month_mapping[month_name]

        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="parking_system"
        )
        cursor = conn.cursor()
        cursor.execute("SELECT id, plate_number, vehicle_type, check_in_time, check_out_time, total_fee FROM parking WHERE MONTH(check_out_time) = %s", (month,))
        rows = cursor.fetchall()

        total_fee = sum(row[5] for row in rows if row[5] is not None)

        conn.close()

        for i in self.report_table.get_children():
            self.report_table.delete(i)

        for row in rows:
            self.report_table.insert("", "end", values=row)

        self.total_fee_label.config(text=f"Rp {total_fee}")

    def delete_report_entry(self):
        selected_item = self.report_table.selection()

        if not selected_item:
            messagebox.showerror("Error", "Pilih entri yang ingin dihapus!")
            return

        item = self.report_table.item(selected_item)
        parking_id = item['values'][0]

        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="parking_system"
        )
        cursor = conn.cursor()
        cursor.execute("DELETE FROM parking WHERE id = %s", (parking_id,))
        conn.commit()
        conn.close()

        self.report_table.delete(selected_item)
        messagebox.showinfo("Sukses", "Entri berhasil dihapus!")

if __name__ == "__main__":
    root = tk.Tk()
    app = ParkingApp(root)
    root.mainloop()
