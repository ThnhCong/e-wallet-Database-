from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QLabel

from GUI.pages.common import Page, add_table, make_button, make_combo, make_input


class AdminUserProfilePage(Page):
    """Paginated, filterable list of all optional user profile records."""

    def __init__(self, api, state, parent=None):
        super().__init__("Customer profiles", "Browse personal profile records created by registered customers.", parent)
        self.api, self.state = api, state
        self.page = 1
        self.total_pages = 0
        self.total_records = 0

        filters = QHBoxLayout()
        self.search = make_input("Search user ID, name, email, address, occupation...")
        self.search.returnPressed.connect(self.apply_filters)
        filters.addWidget(self.search, 3)
        self.sex_filter = make_combo(["MALE", "FEMALE", "OTHER"], "All sexes")
        filters.addWidget(self.sex_filter, 1)
        self.country_filter = make_input("Country")
        filters.addWidget(self.country_filter, 1)
        self.layout.addLayout(filters)

        options = QHBoxLayout()
        self.sort_by = make_combo(["Created date", "User ID"])
        self.sort_by.setItemData(0, "created_at")
        self.sort_by.setItemData(1, "user_id")
        options.addWidget(QLabel("Sort by"))
        options.addWidget(self.sort_by)
        self.sort_order = make_combo(["Newest / highest first", "Oldest / lowest first"])
        self.sort_order.setItemData(0, "DESC")
        self.sort_order.setItemData(1, "ASC")
        options.addWidget(self.sort_order)
        self.page_size = make_combo(["10", "20", "50", "100"])
        self.page_size.setCurrentText("20")
        options.addWidget(QLabel("Rows per page"))
        options.addWidget(self.page_size)
        options.addStretch(1)
        options.addWidget(make_button("Apply filters", self.apply_filters))
        options.addWidget(make_button("Reset", self.reset_filters, "SecondaryButton"))
        self.layout.addLayout(options)

        self.table = add_table(self, [
            ("Profile ID", "user_profile_id"), ("User ID", "user_id"),
            ("Customer", "user_name"), ("Age", "age"),
            ("Sex", "sex"), ("Address", "address"), ("Occupation", "job"), ("Country", "country"),
            ("Created", "created_at"),
        ])

        self.empty_label = QLabel()
        self.empty_label.setObjectName("MutedLabel")
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_label.setWordWrap(True)
        self.empty_label.setMinimumHeight(180)
        self.empty_label.hide()
        self.layout.addWidget(self.empty_label, 1)

        paging = QHBoxLayout()
        self.result_label = QLabel("No records loaded")
        self.result_label.setObjectName("MutedLabel")
        paging.addWidget(self.result_label)
        paging.addStretch(1)
        self.prev_button = make_button("Previous", self.previous_page, "SecondaryButton")
        self.next_button = make_button("Next", self.next_page, "SecondaryButton")
        self.page_label = QLabel("Page 0 of 0")
        self.page_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        paging.addWidget(self.prev_button)
        paging.addWidget(self.page_label)
        paging.addWidget(self.next_button)
        self.layout.addLayout(paging)

    def load_user(self, user_id):
        # Kept for the existing Customers page shortcut: it filters the list by this user.
        self.search.setText(str(user_id))
        self.page = 1

    def apply_filters(self):
        self.page = 1
        self.refresh()

    def reset_filters(self):
        self.search.clear()
        self.sex_filter.setCurrentIndex(0)
        self.country_filter.clear()
        self.sort_by.setCurrentIndex(0)
        self.sort_order.setCurrentIndex(0)
        self.page_size.setCurrentText("20")
        self.page = 1
        self.refresh()

    def previous_page(self):
        if self.page > 1:
            self.page -= 1
            self.refresh()

    def next_page(self):
        if self.page < self.total_pages:
            self.page += 1
            self.refresh()

    def refresh(self):
        self.run_api(
            self.api.admin_user_profiles,
            self.state.user_id,
            page=self.page,
            page_size=int(self.page_size.currentText()),
            search=self.search.text().strip() or None,
            sex=self.sex_filter.currentData(),
            country=self.country_filter.text().strip() or None,
            sort_by=self.sort_by.currentData() or "created_at",
            sort_order=self.sort_order.currentData() or "DESC",
            on_success=self._render_profiles,
        )

    def _render_profiles(self, result):
        result = result or {}
        items = result.get("items") or []
        self.total_records = int(result.get("total", 0) or 0)
        self.total_pages = int(result.get("total_pages", 0) or 0)
        self.page = int(result.get("page", self.page) or 1)
        self.table.set_rows(items)
        has_items = bool(items)
        self.table.setVisible(has_items)
        self.empty_label.setVisible(not has_items)
        if not has_items:
            has_active_filter = bool(self.search.text().strip() or self.sex_filter.currentData() or self.country_filter.text().strip())
            if self.total_records == 0 and not has_active_filter:
                message = ("There are no customer profiles yet.\n"
                           "Profiles will appear here once users complete their personal information.")
            else:
                message = ("No matching customer profiles found.\n"
                           "Try changing your search keyword or filters and try again.")
            self.empty_label.setText(message)
        self.result_label.setText(f"{self.total_records:,} profile record(s)")
        self.page_label.setText(f"Page {self.page} of {self.total_pages}" if self.total_pages else "Page 0 of 0")
        self.prev_button.setEnabled(self.page > 1 and self.total_pages > 0)
        self.next_button.setEnabled(self.page < self.total_pages)