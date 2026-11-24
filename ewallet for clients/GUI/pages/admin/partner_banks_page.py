from PySide6.QtWidgets import QHBoxLayout
from GUI.pages.common import Page,add_table,make_button,make_input
from GUI.widgets.toast import notify
class AdminPartnerBanksPage(Page):
    def __init__(self,api,state,parent=None):
        super().__init__("Partner bank management","Add partner banks and change cooperation status. Historical bank records are never deleted.",parent)
        self.api,self.state=api,state; row=QHBoxLayout(); self.bank_name=make_input("Enter partner bank name (up to 100 characters)"); self.bank_name.setMaxLength(100); self.bank_name.returnPressed.connect(self.create_bank); row.addWidget(self.bank_name,1); row.addWidget(make_button("Add bank",self.create_bank)); self.layout.addLayout(row)
        self.table=add_table(self,[("Bank ID","bank_id"),("Partner bank","name"),("Cooperation date","cooperated_at"),("Currently cooperating","is_valid")])
        actions=QHBoxLayout(); actions.addWidget(make_button("Refresh",self.refresh,"SecondaryButton")); actions.addStretch(1); actions.addWidget(make_button("Activate / deactivate selected",self.toggle_bank,"SecondaryButton")); self.layout.addLayout(actions)
    def refresh(self): self.run_api(self.api.admin_partner_banks,self.state.user_id,on_success=lambda rows:self.table.set_rows(rows or []))
    def create_bank(self):
        name=self.bank_name.text().strip()
        if not name: self.show_error("Enter a partner bank name."); self.bank_name.setFocus(); return
        self.run_api(self.api.admin_create_partner_bank,self.state.user_id,name,write=True,on_success=lambda result:self._created(result,name))
    def _created(self,result,fallback):
        name=(result or {}).get("name",fallback); self.bank_name.clear(); notify(self,"Partner bank added",f"{name} is now available for customer bank linking."); self.refresh()
    def toggle_bank(self):
        row=self.table.currentRow()
        if row<0: self.show_error("Select a partner bank first."); return
        try:
            bank_id=int(self.table.item(row,0).text()); name=self.table.item(row,1).text(); cur=self.table.item(row,3).text().strip().lower(); valid=cur not in ("true","1","yes","active","valid")
        except (AttributeError,TypeError,ValueError): self.show_error("The selected bank row is invalid. Refresh and try again."); return
        self.run_api(self.api.admin_set_partner_bank_valid,self.state.user_id,bank_id,valid,write=True,on_success=lambda _r:self._updated(name,valid))
    def _updated(self,name,valid): notify(self,"Partner bank updated",f"{name} is now {'active' if valid else 'inactive'}. No records were deleted."); self.refresh()
