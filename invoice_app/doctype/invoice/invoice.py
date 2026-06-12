import frappe
from frappe.model.document import Document

class Invoice(Document):
  def autoname(self):
    """Generate nama invoice: INV/{inisial_customer}/{yymm}/{#####}"""
    customer_name = frappe.db.get_value("Customer", self.customer, "customer_name") # Ambil nama lengkap customer dari DocType "Customer"
    initials = self.get_initials(customer_name) # Mengambil inisial dari customer
    
    from frappe.utils import nowdate
    date = nowdate()  # format: YYYY-MM-DD
    yymm = date[2:4] + date[5:7]  # ambil YY dan MM
    
    # Buat prefix, misal: INV/MLI/2601/
    prefix = f"INV/{initials}/{yymm}/" # membuat prefik untuk penamaan
    
    # Frappe akan otomatis tambahkan nomor urut
    self.name = frappe.model.naming.make_autoname(prefix + ".####") # melengkapi prefik dengan no urut
  
  def get_initials(self, name):
    """Ambil huruf pertama setiap kata, contoh: Muat Logistik Indonesia → MLI"""
    words = name.strip().split() # merapihkan dan memisakan string per kata 
    return "".join(word[0].upper() for word in words if word) # mengambil, mengabungakn, mengkapitalkan setiap hurup pertama pada setiap kata
  
  def before_save(self):
    """Hitung semua field otomatis sebelum disimpan"""
    self.calculate_item_totals() # hitung tiap item dan totalnya
    self.calculate_grand_total() # hitung tiap item dengan pajak nya
    self.update_payment_status() # update status pembayaran
    
  def calculate_item_totals(self):
    """Hitung amount tiap item dan total keseluruhan"""
    total = 0 # Variabel akumulator
    for item in self.item:
      item.amount = item.qty * item.rate # hitung banyak barang denga harganya
      total += item.amount # menggabungkan hasil hitung
    self.total_amount = total
  
  def calculate_grand_total(self):
    """Hitung grand total termasuk pajak"""
    tax_amount = self.total_amount * (self.tax_percentage or 0) / 100 # jika ada hitung nilai pajak, atau nol kan
    self.grand_total = self.total_amount + tax_amount # harga barang dengan pajak
    
    # Inisialisasi outstanding amount jika invoice baru
    if not self.outstanding_amount:
      self.outstanding_amount = self.grand_total
  
  def update_payment_status(self):
    if self.outstanding_amount <= 0: # Kondisi 1: Lunas
      self.payment_status = "paid"
    elif self.outstanding_amount < self.grand_total: # Kondisi 2: Bayar sebagian
      self.payment_status = "Partially Paid"
    else: # Kondisi 3: Belum bayar sama sekali
      self.payment_status = "Unpaid"