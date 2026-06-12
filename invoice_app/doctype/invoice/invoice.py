import frappe
from frappe.model.document import Document

class Invoice(Document):
  def autoname(self):
    """Generate nama invoice: INV/{inisial_customer}/{yymm}/{#####}"""
    customer_name = frappe.db.get_value("Customer", self.customer, "customer_name")
    initials = self.get_initials(customer_name)
    
    from frappe.utils import nowdate
    date = nowdate()  # format: YYYY-MM-DD
    yymm = date[2:4] + date[5:7]  # ambil YY dan MM
    
    # Buat prefix, misal: INV/MLI/2601/
    prefix = f"INV/{initials}/{yymm}/"
    
    # Frappe akan otomatis tambahkan nomor urut
    self.name = frappe.model.naming.make_autoname(prefix + ".####")
  
  def get_initials(self, name):
    """Ambil huruf pertama setiap kata, contoh: Muat Logistik Indonesia → MLI"""
    words = name.strip().split()
    return "".join(word[0].upper() for word in words if word)