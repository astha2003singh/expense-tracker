from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

def create_bank_statement(filename):
    c = canvas.Canvas(filename, pagesize=letter)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(100, 750, "Bank of Python - Monthly Statement")
    
    c.setFont("Helvetica", 12)
    c.drawString(100, 720, "Account Name: John Doe")
    c.drawString(100, 700, "Account Number: 123456789")
    c.drawString(100, 680, "Statement Period: 01/05/2026 - 31/05/2026")
    
    # Header
    c.setFont("Helvetica-Bold", 12)
    c.drawString(100, 640, "Date")
    c.drawString(200, 640, "Description")
    c.drawString(450, 640, "Amount")
    
    c.setFont("Helvetica", 12)
    
    # Transactions
    transactions = [
        ("01/05/2026", "Opening Balance", "5000.00 Cr"),
        ("02/05/2026", "Grocery Store", "150.75"),
        ("05/05/2026", "Electric Bill", "85.20"),
        ("10/05/2026", "Salary Deposit", "3000.00 Cr"),
        ("12/05/2026", "Restaurant", "45.00"),
        ("15/05/2026", "Online Shopping", "120.50"),
        ("18/05/2026", "Gas Station", "40.00"),
        ("20/05/2026", "Internet Bill", "60.00"),
        ("25/05/2026", "Coffee Shop", "5.50"),
        ("28/05/2026", "Gym Membership", "50.00"),
    ]
    
    y = 610
    for date, desc, amt in transactions:
        c.drawString(100, y, date)
        c.drawString(200, y, desc)
        c.drawString(450, y, amt)
        y -= 25
        
    c.save()

if __name__ == "__main__":
    create_bank_statement("dummy_statement.pdf")
    print("Dummy statement created!")
