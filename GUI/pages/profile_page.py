from PySide6.QtWidgets import QLineEdit
from GUI.pages.common import Page, add_form, make_button, make_input
from GUI.widgets.toast import notify


class ProfilePage(Page):
    def __init__(self, api, state, parent=None):
        super().__init__("Profile", "Update the contact information associated with your account.", parent)
        self.api, self.state = api, state
        self.name, self.email, self.phone = make_input(), make_input(), make_input()
        add_form(self, [("Name", self.name), ("Email", self.email), ("Phone", self.phone)])
        self.layout.addWidget(make_button("Save changes", self.save))
        self.layout.addStretch()

    def refresh(self):
        self.run_api(self.api.profile, self.state.user_id, on_success=self._load_profile)

    def _load_profile(self, user):
        self.name.setText(user["user_name"])
        self.email.setText(user["email"])
        self.phone.setText(user["phone"])
    def save(self):
        self.run_api(self.api.update_profile, self.state.user_id, self.name.text(), self.email.text(), self.phone.text(),
                     write=True, on_success=self._profile_saved)

    def _profile_saved(self, user):
        self.state.user.update(user)
        notify(self, "Profile updated", "Your profile has been saved.")
