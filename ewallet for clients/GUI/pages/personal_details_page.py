from PySide6.QtCore import QDate
from PySide6.QtWidgets import QDateEdit, QLineEdit
from GUI.pages.common import Page, add_form, make_button, make_combo, make_input
from GUI.widgets.toast import notify

class PersonalDetailsPage(Page):
    def __init__(self, api, state, parent=None):
        super().__init__("Personal details", "Maintain the additional profile information associated with your account.", parent)
        self.api, self.state = api, state
        self.date_of_birth=QDateEdit(); self.date_of_birth.setCalendarPopup(True); self.date_of_birth.setDisplayFormat("yyyy-MM-dd")
        self.date_of_birth.setDate(QDate.currentDate().addYears(-18)); self.date_of_birth.setMaximumDate(QDate.currentDate().addDays(-1)); self.date_of_birth.setMinimumDate(QDate.currentDate().addYears(-120)); self.date_of_birth.setMinimumHeight(40)
        # Age is display-only; QLineEdit avoids spin-box editing/step behavior.
        self.age=QLineEdit(); self.age.setReadOnly(True); self.age.setPlaceholderText("Automatically calculated"); self.age.setMinimumHeight(40)
        self.date_of_birth.dateChanged.connect(lambda _date: self._update_age())
        self._update_age()
        self.sex=make_combo(["MALE","FEMALE","OTHER"]); self.address=make_input("Street address"); self.job=make_input("Occupation"); self.country=make_input("Country")
        add_form(self,[("Date of birth",self.date_of_birth),("Age (calculated)",self.age),("Sex",self.sex),("Address",self.address),("Occupation",self.job),("Country",self.country)])
        self.layout.addWidget(make_button("Save personal details",self.save)); self.layout.addStretch()
    def _update_age(self):
        dob = self.date_of_birth.date()
        if not dob.isValid():
            self.age.clear()
            return
        today = QDate.currentDate()
        years = today.year() - dob.year()
        if (today.month(), today.day()) < (dob.month(), dob.day()):
            years -= 1
        self.age.setText(str(max(0, years)))
    def refresh(self): self.run_api(self.api.user_profile,self.state.user_id,on_success=self._load_personal_profile)
    def _load_personal_profile(self,profile):
        if not profile: return
        dob=QDate.fromString(str(profile.get("date_of_birth") or ""),"yyyy-MM-dd")
        if dob.isValid(): self.date_of_birth.setDate(dob)
        self._update_age(); self.sex.setCurrentText(profile.get("sex") or "OTHER")
        self.address.setText(profile.get("address") or ""); self.job.setText(profile.get("job") or ""); self.country.setText(profile.get("country") or "")
    def save(self):
        dob=self.date_of_birth.date().toString("yyyy-MM-dd")
        self.run_api(self.api.save_user_profile,self.state.user_id,dob,self.sex.currentText(),self.address.text().strip(),self.job.text().strip(),self.country.text().strip(),write=True,on_success=self._personal_profile_saved)
    def _personal_profile_saved(self,profile):
        notify(self,"Profile saved","Your personal details have been updated.")
        if isinstance(profile,dict): self._load_personal_profile(profile)
