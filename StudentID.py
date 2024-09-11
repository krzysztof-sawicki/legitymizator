"""
Rozmiar ID-1:	85.60 mm × 53.98 mm
				3.370" × 2.125"
				1011 x 637,5 px (@300 dpi)
				2022 x 1275  px (@600 dpi)
"""
from fpdf import FPDF
from pdf2image import convert_from_path
import os

class StudentID:
	def __init__(self):
		pass
	
	@staticmethod
	def generate(name, birthdate, pesel, school, principal, issueDate, idNumber, photo, fileName, background = False):
		pdf = FPDF()
		pdf.add_font(fname='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf')
		pdf.set_font('DejaVuSans-Bold', size=6)
		if background:
			pdf.set_page_background('legitymacja300.png')
		
		pdf.add_page(format=(85.6, 53.98))
		pdf.set_margin(0)
		
		pdf.set_xy(27, 17)
		pdf.cell(None, None, name)
		
		pdf.set_xy(27, 23)
		pdf.cell(None, None, birthdate)
		
		pdf.set_xy(54.5, 23)
		pdf.cell(None, None, pesel)
		
		sn = school.splitlines()
		flp = 29.0
		nlp = 2.4
		for line in sn:
			pdf.set_xy(27, flp)
			pdf.cell(None, None, line)
			flp += nlp
		
		pdf.set_xy(27, 41)
		pdf.cell(None, None, principal)
		
		pdf.set_xy(27, 47)
		pdf.cell(None, None, issueDate)
		
		pdf.set_font('DejaVuSans-Bold', size=8)
		
		pdf.set_xy(9, 47.4)
		pdf.cell(None, None, idNumber)
		
		pdf.image(photo, 5.5, 17, 19, 26)
		
		pdf.output(fileName)

	@staticmethod
	def generateView(name, birthdate, pesel, school, principal, issueDate, idNumber, photo, tempdir):
		fileName = tempdir + "/view.pdf"
		#print(fileName)
		fileNamePng = tempdir + "/view.png"
		StudentID.generate(name, birthdate, pesel, school, principal, issueDate, idNumber, photo, fileName, True)
		
		if os.path.exists(fileName):
			convert_from_path(fileName, dpi=96, output_folder=tempdir, fmt="png", single_file=True, output_file="view")
			if os.path.exists(fileNamePng):
				f = open(fileNamePng, "rb")
				d = f.read()
				f.close()
				return d
		return None
