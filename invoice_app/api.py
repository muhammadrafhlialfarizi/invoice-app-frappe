import frappe
from frappe import _

@frappe.whitelist(allow_guest=False)
def get_invoice(invoice_number): # fungsi untuk ambil dan mengirim data invoice
  """
    Mendapatkan detail invoice berdasarkan nomor invoice.
    GET /api/method/invoice_app.api.get_invoice?invoice_number=INV/MLI/2601/00001
  """
  # Cek apakah invoice ada sebelum ambil datanya
  if not frappe.db.exists("Invoice", invoice_number):
    frappe.thorow(_(f"Invoice {invoice_number} tidak ditemukan"), frappe.DoesNotExistError) # mengembalikan pesan jika invoice tidak ada

  invoice = frappe.get_doc("Invoice", invoice_number) # mengambil data invoice
  
  return { # return pesan berbentuk JSON
    "invoice_number": invoice.name,
    "customer": invoice.customer,
    "invoice_date": invoice.invoice_date,
    "items": [
      {
        "item_name": item.item_name,
        "qty": item.qty,
        "rate": item.rate,
        "amount": item.amount
      }
      for item in invoice.items # iterasi setiap baris child table
    ],
    "total_amount": invoice.total_amount,
    "tax_percentage": invoice.tax_percentage,
    "grand_total": invoice.grand_total,
    "outstanding_amount": invoice.outstanding_amount,
    "payment_status": invoice.payment_status
  }

@frappe.whitelist(allow_guest=False)
def mark_as_paid(invoice_number, payment_amount): # fungsi untuk memcatat dan memperbaharui pembayaran
  """
    Mencatat pembayaran invoice.
    POST /api/method/invoice_app.api.mark_as_paid
    Body: { "invoice_number": "...", "payment_amount": 100000 }
  """
  payment_amount = float(payment_amount) # mengubah tyoe input jadi float
  
  # validasi input
  if payment_amount <= 0:
    frappe.throw(_("Jumlah pembayaran harus lebih dari 0"))
    
  # cek invoice apakah ada di database
  if not frappe.db.exists("invoice", invoice_number):
    frappe.throw(_(f"Invoice {invoice_number} tidak ditemukan"), frappe.DoesNotExistError)

  invoice = frappe.get_doc("invoice", invoice_number) # ambil data invoice
  
  # Validasi invoice belum lunas
  if invoice.payment_status == "Paid":
    frappe.throw(_("Invoice ini sudah lunas"))
  
  # validasi pembayaran tidak melebihi sisa pembayaran
  if payment_amount > invoice.outstanding_amount:
    frappe.throw(_(f"Jumlah pembayaran melebihi outstanding amount ({invoice.outstanding_amount})"))
    
  # proses pembayran
  invoice.payment_amount = (invoice.payment_amount or 0) + payment_amount
  invoice.outstanding_amount = invoice.grand_total - invoice.payment_amount
  
  # update status pembayaran
  if invoice.outstanding_amount <= 0:
      invoice.payment_status = "Paid" # sudah lunas
  else:
      invoice.payment_status = "Partially Paid" # masih ada sisa pembayaran
      
  # simpan hasil db
  invoice.save(ignore_permissions=True)
  frappe.db.commit()
  
  # respon output ke clien/customer
  return {
    "message": "Pembayaran berhasil dicatat",
    "invoice_number": invoice.name,
    "payment_amount": payment_amount,
    "outstanding_amount": invoice.outstanding_amount,
    "payment_status": invoice.payment_status
  }