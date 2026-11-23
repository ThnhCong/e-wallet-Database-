from PySide6.QtWidgets import QSpinBox
from GUI.pages.common import Page, add_form, make_button, make_combo, make_input
from GUI.widgets.toast import notify


class PersonalDetailsPage(Page):
    def __init__(self, api, state, parent=None):
        super().__init__("Personal details", "Maintain the additional profile information associated with your account.", parent)
        self.api, self.state = api, state
        self.age = QSpinBox(); self.age.setRange(1, 120); self.age.setMinimumHeight(40)
        self.sex = make_combo(["MALE", "FEMALE", "OTHER"])
        self.address = make_input("Street address")
        self.job = make_input("Occupation")
        self.country = make_input("Country")
        add_form(self, [("Age", self.age), ("Sex", self.sex), ("Address", self.address),
                        ("Occupation", self.job), ("Country", self.country)])
        self.layout.addWidget(make_button("Save personal details", self.save))
        self.layout.addStretch()

    def refresh(self):
        self.run_api(self.api.user_profile, self.state.user_id, on_success=self._load_personal_profile)

    def _load_personal_profile(self, profile):
        if not profile:
            return
        self.age.setValue(int(profile.get("age") or 1))
        self.sex.setCurrentText(profile.get("sex") or "OTHER")
        self.address.setText(profile.get("address") or "")
        self.job.setText(profile.get("job") or "")
        self.country.setText(profile.get("country") or "")
    def save(self):
        self.run_api(self.api.save_user_profile, self.state.user_id, self.age.value(), self.sex.currentText(),
                     self.address.text().strip(), self.job.text().strip(), self.country.text().strip(),
                     write=True, on_success=self._personal_profile_saved)

    def _personal_profile_saved(self, profile):
        notify(self, "Profile saved", "Your personal details have been updated.")
        if isinstance(profile, dict):
            self.refresh()
