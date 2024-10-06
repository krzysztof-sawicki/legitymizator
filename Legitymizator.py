#!/usr/bin/env python3
from legitymizatorlib import *
from StudentID import StudentID
from lconfig import lConfig
import gc, wx, uuid, tempfile, sqlite3, os, re, shutil

class XLegitymizator(Legitymizator):
	
	PHOTO_WIDTH = 225
	PHOTO_HEIGHT = 307
	
	APPVERSION = '0.2'
	
	VALIDCOLOR = wx.Colour(64, 192, 64)
	INVALIDCOLOR = wx.Colour(255, 127, 0)
	
	bitmapIsLoaded = False
	unsavedChanges = False
	startMousePosition = None
	db = None
	dbFileName = None
	
	subBitmapPosition = [0,0]
	
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.tempdir = tempfile.mkdtemp('_legitymizator')
		self.dataBitmap = wx.Bitmap(self.PHOTO_WIDTH, self.PHOTO_HEIGHT)
		#rozmiar bitmapy powinen być minimum: 225 x 307 (19x26 mm @ 300 dpi)
		self.subBitmapSize = [self.PHOTO_WIDTH, self.PHOTO_HEIGHT]
		
		self.photo.Bind(wx.EVT_LEFT_DOWN, self.photoMouseDown)
		self.photo.Bind(wx.EVT_LEFT_UP, self.photoMouseUp)
		self.photo.Bind(wx.EVT_MOTION, self.photoMotion)
		self.mainPanel.Bind(wx.EVT_MOUSEWHEEL, self.photoMouseWheel)
		
		self.statusbar.SetStatusText("Legitymizator v"+str(self.APPVERSION), 0)
		
		while True:
			dial = wx.MessageDialog(self, "Otworzyć istniejącą bazę czy stworzyć nową?", "Baza danych", wx.YES_NO|wx.CANCEL|wx.STAY_ON_TOP|wx.CENTRE)
			dial.SetYesNoCancelLabels("Istniejąca baza", "Nowa baza", "Zamknij program")
			r = dial.ShowModal()
			
			if r == wx.ID_YES: #istniejąca
				ret = self.openDbDialog()
				if ret:
					break
			elif r == wx.ID_NO: #nowa baza
				ret = self.newDbDialog()
				dbSettingsFrame = XDBSettings(self, wx.ID_ANY, "")
				dbSettingsFrame.Show()
				if ret:
					break
			elif r == wx.ID_CANCEL: #zamknij program
				wx.Exit()
		self.setDefaultFormValues()
	
	def onFrameClose(self, event):
		if os.path.exists(self.tempdir):
			shutil.rmtree(self.tempdir)
		event.Skip()

	def loadBitmap(self, nameOrBuffer, scaleFactor = None, x = 0, y = 0, dx = 0, dy = 0):
		self.bitmapIsLoaded = False
		if isinstance(nameOrBuffer, str):
			self.dataBitmap = wx.Bitmap(nameOrBuffer, type=wx.BITMAP_TYPE_ANY)
		elif isinstance(nameOrBuffer, bytes) or isinstance(nameOrBuffer, bytearray):
			self.dataBitmap = wx.Bitmap.FromPNGData(nameOrBuffer)
		ox = self.dataBitmap.GetWidth()
		oy = self.dataBitmap.GetHeight()
		self.dataBitmap.SetScaleFactor(1.0)
		if ox < self.PHOTO_WIDTH or oy < self.PHOTO_HEIGHT:
			#print("Obraz zbyt mały")
			return False
		else:
			self.subBitmapPosition[0] = x
			self.subBitmapPosition[1] = y
			if scaleFactor is not None:
				self.dataBitmap.SetScaleFactor(scaleFactor)
				self.subBitmapSize[0] = dx
				self.subBitmapSize[1] = dy
			else:
				self.subBitmapSize[0] = self.PHOTO_WIDTH
				self.subBitmapSize[1] = self.PHOTO_HEIGHT
				sfa = ox/(self.PHOTO_WIDTH + 1)
				sfb = oy/(self.PHOTO_HEIGHT + 1)
				if sfa < sfb:
					self.dataBitmap.SetScaleFactor(sfa)
				else:
					self.dataBitmap.SetScaleFactor(sfb)
			self.bitmapIsLoaded = True
			self.reloadBitmap()
			return True

	def reloadBitmap(self):
		os = self.photo.GetSize()
		self.photo.SetBitmap(self.dataBitmap.GetSubBitmap(wx.Rect(int(self.subBitmapPosition[0]),int(self.subBitmapPosition[1]), int(self.subBitmapSize[0]), int(self.subBitmapSize[1]))))
		self.photo.SetSize(wx.Size(self.PHOTO_WIDTH, self.PHOTO_HEIGHT))
		
	def photoMouseDown(self, event):
		self.startMousePosition = wx.GetMousePosition()
		event.Skip()

	def photoMouseUp(self, event):
		self.startMousePosition = None
		event.Skip()

	def photoMotion(self, event):
		if self.editPhotoSwitch.GetValue() and self.startMousePosition is not None:
			actpos = wx.GetMousePosition()
			diffx = actpos[0] - self.startMousePosition[0]
			diffy = actpos[1] - self.startMousePosition[1]
			self.changeSubBitmapPosition(-diffx, -diffy)
			self.reloadBitmap()
			self.startMousePosition = actpos
			self.notifyUnsavedFormChanges()
		event.Skip()
	
	def photoZoom(self, value):
		asf = self.dataBitmap.GetScaleFactor()
		oasf = asf
		try:
			asf += value
			if asf < 1:
				asf = 1
			self.dataBitmap.SetScaleFactor(asf)
			self.reloadBitmap()
		except:
			self.dataBitmap.SetScaleFactor(oasf)
	
	def photoMouseWheel(self, event): 
		if self.editPhotoSwitch.GetValue():
			phs = self.photo.GetSize()
			php = self.photo.GetPosition()
			cursor = event.GetPosition()
			
			if cursor[0] >= php[0] and cursor[0] <= php[0]+phs[0] and cursor[1] >= php[1] and cursor[1] <= php[1]+phs[1]:
				if event.GetWheelRotation() < 0:
					self.photoZoom(0.05)
				else:
					self.photoZoom(-0.05)
				self.notifyUnsavedFormChanges()
		event.Skip()
	
	def validatePESEL(self, pesel):
		if not isinstance(pesel, str) or len(pesel) != 11 or not pesel.isdigit():
			return False
		digits = [int(digit) for digit in pesel]
		
		control_sum = (1 * digits[0] + 3 * digits[1] + 7 * digits[2] + 9 * digits[3] + 1 * digits[4] + 3 * digits[5] + 7 * digits[6] + 9 * digits[7] + 1 * digits[8] + 3 * digits[9]) % 10
		check_digit = 10 - control_sum
		check_digit = 0 if check_digit == 10 else check_digit
		return check_digit == digits[10]
	
	def validateDocumentForm(self):
		if len(self.fStudentName.GetValue()) > 0 and self.validatePESEL(self.fPESEL.GetValue()) and len(self.fSchool.GetValue()) > 0 and len(self.fPrincipal.GetValue()) > 0 and (self.validateIdNumber(self.fIdNumber.GetValue()) or (len(self.fIdNumber.GetValue()) > 0 and self.fIdNumber.IsEnabled() == False)) and self.bitmapIsLoaded:
			return True
		else:
			return False
	
	def validateIdNumber(self, number):
		if len(number) < 1:
			return False
		if self.db:
			cur = self.db.cursor()
			d = cur.execute('select ID from documents where ID = ?', (number,)).fetchall()
			cur.close()
			if len(d) > 0:
				return False
			else:
				return True
		else:
			return False
	
	def PESELtoDateTime(self, pesel):
		if not self.validatePESEL(pesel):
			return wx.DateTime()
		digits = [int(digit) for digit in pesel]
		year = 1900 + digits[0] * 10 + digits[1]
		month = (digits[2] % 2) * 10 + digits[3]
		day = digits[4] * 10 + digits[5]
		century_indicator = digits[2] // 2
		if century_indicator == 1:
			year += 100
		elif century_indicator == 2:
			year += 200
		elif century_indicator == 3:
			year += 300
		return wx.DateTime(day, month-1, year)
	
	def notifyUnsavedFormChanges(self, on = True):
		self.RecordChangeIndicator.Show(on)
		self.unsavedChanges = on
	
	def areUnsavedFormChanges(self):
		return self.unsavedChanges
	
	def onfPESELEnter(self, event):
		self.notifyUnsavedFormChanges()
		if self.validatePESEL(self.fPESEL.GetValue()):
			self.fPESEL.SetBackgroundColour(self.VALIDCOLOR)
			self.fBirthDate.SetDate(self.PESELtoDateTime(self.fPESEL.GetValue()))
		else:
			self.fPESEL.SetBackgroundColour(self.INVALIDCOLOR)
		event.Skip()
		
	def onFStudentNameEnter(self, event):
		self.notifyUnsavedFormChanges()
		event.Skip()

	def onFBirthDateChange(self, event):
		self.notifyUnsavedFormChanges()
		event.Skip()

	def onFSchoolEnter(self, event):
		self.notifyUnsavedFormChanges()
		event.Skip()

	def onFPrincipalEnter(self, event):
		self.notifyUnsavedFormChanges()
		event.Skip()

	def onFIssueDateChange(self, event):
		self.notifyUnsavedFormChanges()
		event.Skip()

	def onFIdNumberEnter(self, event):
		if self.validateIdNumber(self.fIdNumber.GetValue()) or not self.fIdNumber.IsEnabled():
			self.fIdNumber.SetBackgroundColour(self.VALIDCOLOR)
		else:
			self.fIdNumber.SetBackgroundColour(self.INVALIDCOLOR)
		self.notifyUnsavedFormChanges()
		event.Skip()
	
	def onFCardNumberEnter(self, event):
		self.notifyUnsavedFormChanges()
		event.Skip()
		
	def changeSubBitmapPosition(self, x, y):
		self.subBitmapPosition[0] += x
		self.subBitmapPosition[1] += y
		
		if self.subBitmapPosition[0] < 0:
			self.subBitmapPosition[0] = 0
		if self.subBitmapPosition[1] < 0:
			self.subBitmapPosition[1] = 0
		if self.subBitmapPosition[0] >= self.dataBitmap.GetScaledWidth() - self.subBitmapSize[0]:
			self.subBitmapPosition[0] = self.dataBitmap.GetScaledWidth() - self.subBitmapSize[0]
		if self.subBitmapPosition[1] >= self.dataBitmap.GetScaledHeight() - self.subBitmapSize[1]:
			self.subBitmapPosition[1] = self.dataBitmap.GetScaledHeight() - self.subBitmapSize[1]
	
	def openPhotoFileSelector(self, event):
		with wx.FileDialog(self, "Otwórz zdjęcie", wildcard="Zdjęcia (*.jpg)|*.jpg", style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as fileDialog:

			if fileDialog.ShowModal() == wx.ID_CANCEL:
				return
			self.loadBitmap(fileDialog.GetPath())
			self.editPhotoSwitch.Enable()
		event.Skip()
		
	
	def onGenerateFileButton(self, event):
		fStudentName = self.fStudentName.GetValue()
		fBirthDate = self.fBirthDate.GetDate().Format("%d.%m.%Y")
		fPESEL = self.fPESEL.GetValue()
		fSchool = self.fSchool.GetValue()
		fPrincipal = self.fPrincipal.GetValue()
		fIssueDate = self.fIssueDate.GetDate().Format("%d.%m.%Y")
		fIdNumber = self.fIdNumber.GetValue()
		fname = os.path.dirname(self.dbFileName) + '/' + re.sub(r'\W+', '_', fIdNumber) + '.pdf'
		
		if self.validateDocumentForm():
			photoName = self.tempdir + "/" + uuid.uuid4().hex + '.jpg'
			self.dataBitmap.GetSubBitmap(wx.Rect(int(self.subBitmapPosition[0]),int(self.subBitmapPosition[1]), int(self.subBitmapSize[0]), int(self.subBitmapSize[1]))).SaveFile(photoName, wx.BITMAP_TYPE_JPEG)
			StudentID.generate(fStudentName, fBirthDate, fPESEL, fSchool, fPrincipal, fIssueDate, fIdNumber, photoName, fname)
			if os.path.exists(fname):
				dial = wx.MessageDialog(self, f"Plik wygenerowano: {fname}", "Sukces", wx.OK|wx.STAY_ON_TOP|wx.CENTRE)
				dial.ShowModal()
				event.Skip()
				return fname
			else:
				dial = wx.MessageDialog(self, "Nie udało się wygenerować pliku", "Błąd", wx.OK|wx.STAY_ON_TOP|wx.CENTRE)
				dial.ShowModal()
				event.Skip()
				return None
		event.Skip()
		return None
	
	def onViewGenerateButton(self, event):
		fStudentName = self.fStudentName.GetValue()
		fBirthDate = self.fBirthDate.GetDate().Format("%d.%m.%Y")
		fPESEL = self.fPESEL.GetValue()
		fSchool = self.fSchool.GetValue()
		fPrincipal = self.fPrincipal.GetValue()
		fIssueDate = self.fIssueDate.GetDate().Format("%d.%m.%Y")
		fIdNumber = self.fIdNumber.GetValue()
		if self.validateDocumentForm():
			photoName = self.tempdir + "/" + uuid.uuid4().hex + '.jpg'
			self.dataBitmap.GetSubBitmap(wx.Rect(int(self.subBitmapPosition[0]),int(self.subBitmapPosition[1]), int(self.subBitmapSize[0]), int(self.subBitmapSize[1]))).SaveFile(photoName, wx.BITMAP_TYPE_JPEG)
			d = StudentID.generateView(fStudentName, fBirthDate, fPESEL, fSchool, fPrincipal, fIssueDate, fIdNumber, photoName, self.tempdir)
			if d is not None:
				b = wx.Bitmap.FromPNGData(d)
				self.IDView.SetBitmap(b)
		event.Skip()
		
	def onPrintButton(self, event):
		f = self.onGenerateFileButton(event)
		if f is not None and os.path.exists(f):
			self.pdfViewer.LoadFile(f)
			self.pdfViewer.Print()
		event.Skip()
	
	def reloadDocumentListCtrl(self):
		self.documentListCtrl.DeleteAllItems()
		cur = self.db.cursor()
		data = cur.execute('select ID, Name, PESEL, CardNumber from documents order by ID asc').fetchall()
		for i, row in enumerate(data):
			r = list(row)
			if r[3] is None:
				r[3] = ''
			self.documentListCtrl.Append(r)
		cur.close()
	
	def onSaveRecordButton(self, event):
		if not self.db:
			dial = wx.MessageDialog(self, "Brak wskazanej bazy danych", "Błąd", wx.OK|wx.STAY_ON_TOP|wx.CENTRE)
			dial.ShowModal()
		elif not self.validateDocumentForm():
			dial = wx.MessageDialog(self, "Formularz z danymi zawiera błędy", "Błąd", wx.OK|wx.STAY_ON_TOP|wx.CENTRE)
			dial.ShowModal()
		else:
			r = False
			if self.fIdNumber.IsEnabled():
				r = self.saveCurrentRecord()
			else:
				r = self.saveCurrentRecord(self.fIdNumber.GetValue())
			if r:
				self.reloadDocumentListCtrl()
				self.notifyUnsavedFormChanges(False)
		event.Skip()
	
	def onNewRecordButton(self, event):
		self.setDefaultFormValues()
		self.editPhotoSwitch.Disable()
		event.Skip()
	
	def setDefaultFormValues(self):
		cur = self.db.cursor()
		d = cur.execute('select * from metaInfo').fetchall()
		for r in d:
			if r[0] == 'schoolName':
				self.fSchool.SetValue(r[1])
			elif r[0] == 'principal':
				self.fPrincipal.SetValue(r[1])
		cur.close()
		self.fStudentName.SetValue('')
		self.fPESEL.SetValue('')
		self.fBirthDate.SetDate(wx.DateTime.Now())
		self.fIssueDate.SetDate(wx.DateTime.Now())
		self.fIdNumber.SetValue('')
		self.fCardNumber.SetValue('')
		self.fIdNumber.Enable(True)
		self.dataBitmap = wx.Bitmap(self.PHOTO_WIDTH, self.PHOTO_HEIGHT)
		self.subBitmapSize = [self.PHOTO_WIDTH, self.PHOTO_HEIGHT]
		self.subBitmapPosition = [0,0]
		self.reloadBitmap()
		self.IDView.SetBitmap(wx.Bitmap())
		self.notifyUnsavedFormChanges(False)
	
	def onDocumentListCtrlSelect(self, event):
		if self.areUnsavedFormChanges():
			dial = wx.MessageDialog(self, "Bieżący rekord nie został zapisany. Czy chcesz zignorować wprowadzone zmiany?", "Niezapisane zmiany", wx.YES_NO|wx.NO_DEFAULT|wx.STAY_ON_TOP|wx.CENTRE)
			ret = dial.ShowModal()
			if ret == wx.ID_NO:
				event.Skip()
				return
		selectedID = self.documentListCtrl.GetItem(event.GetIndex(), 0).GetText()
		r = self.getRecord(selectedID)
		if r:
			self.setDefaultFormValues()
			self.fIdNumber.Enable(False)
			self.fIdNumber.SetValue(r[0])
			if r[13] is not None:
				self.fCardNumber.SetValue(r[13])
			else:
				self.fCardNumber.SetValue('')
			self.fStudentName.SetValue(r[1])
			dmy = r[2].split('-')
			self.fBirthDate.SetDate(wx.DateTime.FromDMY(int(dmy[2]), int(dmy[1])-1, int(dmy[0])))
			self.fPESEL.SetValue(r[3])
			self.fSchool.SetValue(r[4])
			self.fPrincipal.SetValue(r[5])
			dmy = r[6].split('-')
			self.fIssueDate.SetDate(wx.DateTime.FromDMY(int(dmy[2]), int(dmy[1])-1, int(dmy[0])))
			
			self.loadBitmap(r[7], r[8], r[9], r[10], r[11], r[12])
			self.bitmapIsLoaded = True
			self.editPhotoSwitch.Enable()
			self.notifyUnsavedFormChanges(False)
		event.Skip()
	
	def onDbSettings(self, event):
		dbSettingsFrame = XDBSettings(self, wx.ID_ANY, "")
		dbSettingsFrame.Show()
		event.Skip()
	
	## Baza danych
	def onNewDb(self, event):
		self.newDbDialog()
		event.Skip()
	
	def newDbDialog(self):
		lastPath = os.path.dirname(lConfig.getField('lastDB'))
		with wx.FileDialog(self, "Zapisz nową bazę danych", wildcard="SQLite (*.db)|*.db", style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT) as fileDialog:
			fileDialog.SetDirectory(lastPath)
			if fileDialog.ShowModal() == wx.ID_CANCEL:
				return False
			pathname = fileDialog.GetPath()
			if not pathname.endswith('.db'):
				pathname += ".db"
			if self.createNewDb(pathname):
				self.dbNameStaticText.SetLabel(pathname)
				lConfig.updateField('lastDB', pathname)
				return True
			return False
	
	def onOpenDb(self, event):
		self.openDbDialog()
		event.Skip()
		
	def openDbDialog(self):
		lastPath = os.path.dirname(lConfig.getField('lastDB'))
		with wx.FileDialog(self, "Otwórz bazę danych", wildcard="SQLite (*.db)|*.db", style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as fileDialog:
			fileDialog.SetDirectory(lastPath)
			if fileDialog.ShowModal() == wx.ID_CANCEL:
				return False
			pathname = fileDialog.GetPath()
			if self.openDb(pathname):
				self.dbFileName = pathname
				self.dbNameStaticText.SetLabel(pathname)
				self.reloadDocumentListCtrl()
				lConfig.updateField('lastDB', pathname)
				return True
			return False
	
	def createNewDb(self, name):
		self.db = sqlite3.connect(name, isolation_level = None)
		if not self.db:
			return False
		self.dbFileName = name
		cur = self.db.cursor()
		cur.execute('CREATE TABLE "metaInfo" ("name"	TEXT, "value"	TEXT, PRIMARY KEY("name"))')
		cur.execute('insert into metaInfo (name, value) values ("version", ?)', (self.APPVERSION, ))
		cur.execute('insert into metaInfo (name, value) values ("principal", ?)', ("dyrektor",))
		cur.execute('insert into metaInfo (name, value) values ("schoolName", ?)', ("Nazwa szkoły\nAdres szkoły",))
		cur.execute('CREATE TABLE "documents" ( "ID"	TEXT NOT NULL, "Name"	TEXT NOT NULL, "BirthDate"	TEXT NOT NULL, "PESEL"	TEXT NOT NULL, "SchoolName"	TEXT NOT NULL, "Principal"	TEXT NOT NULL, "IssueDate"	TEXT NOT NULL, "Photo"	BLOB NOT NULL, "PhotoScale"	REAL NOT NULL, "PhotoXOffset"	INTEGER NOT NULL, "PhotoYOffset"	INTEGER NOT NULL, "PhotoXSize"	INTEGER NOT NULL, "PhotoYSize"	INTEGER NOT NULL, "CardNumber" TEXT DEFAULT NULL, PRIMARY KEY("ID"))')
		cur.close()
		return True
	
	def openDb(self, name):
		self.db = sqlite3.connect(name, isolation_level = None)
		if not self.db:
			return False
		cur = self.db.cursor()
		d = cur.execute("select value from metaInfo where name = 'version'").fetchone()
		dbVer = d[0]
		if dbVer == self.APPVERSION:
			pass
		else:
			dial = wx.MessageDialog(self, "Niezgodność wersji bazy danych. Rozpoczynam aktualizację!", "Uwaga!", wx.OK|wx.STAY_ON_TOP|wx.CENTRE)
			dial.ShowModal()
			while dbVer != self.APPVERSION:
				if dbVer == '0.1':
					dbVer = '0.2'
					cur.execute('ALTER TABLE documents ADD COLUMN 	"CardNumber"	TEXT DEFAULT NULL')
					cur.execute('update metaInfo set value = ? where name = "version"', (dbVer,))
			
		cur.close()
		return True
	
	def getRecord(self, ID):
		cur = self.db.cursor()
		d = cur.execute('select * from documents where ID = ?', (ID,)).fetchone()
		cur.close()
		return d
	
	def saveCurrentRecord(self, ID = 0):
		photoName = self.tempdir + "/" + uuid.uuid4().hex + '.png'
		self.dataBitmap.SaveFile(photoName, wx.BITMAP_TYPE_PNG)
		photoFile = open(photoName, 'rb')
		photoData = photoFile.read()
		photoFile.close()
		os.remove(photoName)
		cur = self.db.cursor()
		if ID == 0:
			t = cur.execute('insert into documents (ID, Name, BirthDate, PESEL, SchoolName, Principal, IssueDate, CardNumber, Photo, PhotoScale, PhotoXOffset, PhotoYOffset, PhotoXSize, PhotoYSize) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
			(
				self.fIdNumber.GetValue(),
				self.fStudentName.GetValue(),
				self.fBirthDate.GetDate().FormatISODate(),
				self.fPESEL.GetValue(),
				self.fSchool.GetValue(),
				self.fPrincipal.GetValue(),
				self.fIssueDate.GetDate().FormatISODate(),
				self.fCardNumber.GetValue(),
				photoData,
				self.dataBitmap.GetScaleFactor(),
				self.subBitmapPosition[0],
				self.subBitmapPosition[1],
				self.subBitmapSize[0],
				self.subBitmapSize[1]
			))
		else:
			t = cur.execute('update documents set Name = ?, BirthDate = ?, PESEL = ?, SchoolName = ?, Principal = ?, IssueDate = ?, CardNumber = ?, Photo = ?, PhotoScale = ?, PhotoXOffset = ?, PhotoYOffset = ?, PhotoXSize = ?, PhotoYSize = ? where ID = ?',
			(
				self.fStudentName.GetValue(),
				self.fBirthDate.GetDate().FormatISODate(),
				self.fPESEL.GetValue(),
				self.fSchool.GetValue(),
				self.fPrincipal.GetValue(),
				self.fIssueDate.GetDate().FormatISODate(),
				self.fCardNumber.GetValue(),
				photoData,
				self.dataBitmap.GetScaleFactor(),
				self.subBitmapPosition[0],
				self.subBitmapPosition[1],
				self.subBitmapSize[0],
				self.subBitmapSize[1],
				ID,
			))
		cur.close()
		return bool(t)

class XDBSettings(DBSettings):
	parent = None
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		if args[0] is not None:
			self.parent = args[0]
			self.db = self.parent.db
			cur = self.db.cursor()
			d = cur.execute("select * from metaInfo").fetchall()
			for r in d:
				if r[0] == "schoolName":
					self.schoolNameCtrl.SetValue(r[1])
				elif r[0] == "principal":
					self.principalCtrl.SetValue(r[1])
			cur.close()
		else:
			dial = wx.MessageDialog(self, "Brak wskazanej bazy danych", "Błąd", wx.OK|wx.STAY_ON_TOP|wx.CENTRE)
			dial.ShowModal()
	
	def onSettingsSaveButton(self, event):
		cur = self.db.cursor()
		cur.execute("update metaInfo set value = ? where name = ?", (self.schoolNameCtrl.GetValue(), 'schoolName'))
		cur.execute("update metaInfo set value = ? where name = ?", (self.principalCtrl.GetValue(), 'principal'))
		cur.close()
		self.Destroy()
		event.Skip()

class XLegitymizatorApp(wx.App):
	def OnInit(self):
		self.frame = XLegitymizator(None, wx.ID_ANY, "")
		self.SetTopWindow(self.frame)
		self.frame.Show()
		return True

if __name__ == "__main__":
	gc.enable()
	XLegitymizator = XLegitymizatorApp(0)
	XLegitymizator.MainLoop()
