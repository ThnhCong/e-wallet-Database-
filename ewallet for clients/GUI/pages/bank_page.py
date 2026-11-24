from PySide6.QtWidgets import QHBoxLayout
from GUI.pages.common import Page, add_form, add_table, make_button, make_combo, make_input
from GUI.core.formatter import short_time
from GUI.widgets.confirm_dialog import confirm
from GUI.widgets.toast import notify
class BankPage(Page):
    def __init__(self,api,state,parent=None):
        super().__init__("Bank connections","Connect an active wallet to a cooperating partner bank. A bank account number is required.",parent)
        self.api,self.state=api,state; self.wallet=make_combo([]); self.bank=make_combo([]); self.account_number=make_input("Bank account number (6-34 digits)"); self.account_number.setMaxLength(34)
        add_form(self,[("Wallet to connect",self.wallet),("Partner bank",self.bank),("Bank account number",self.account_number)])
        actions=QHBoxLayout(); actions.addWidget(make_button("Connect bank",self.link_bank)); actions.addWidget(make_button("Unlink selected",self.unlink_bank,"DangerButton")); actions.addWidget(make_button("Refresh",self.refresh,"SecondaryButton")); actions.addStretch(); self.layout.addLayout(actions)
        self.layout.addWidget(self.section_label("My bank connections"))
        self.table=add_table(self,[("Link ID","bank_account_id"),("Wallet","wallet_id"),("Currency","currency"),("Bank","bank_name"),("Account number","account_number"),("Status","status"),("Partner active","is_valid"),("Connected",lambda r:short_time(r.get("linked_at")))])
    def refresh(self): self.run_api(self.api.bank_page_data,self.state.user_id,on_success=self._render_bank_data)
    def _render_bank_data(self,data):
        self.wallet.clear()
        for w in data.get("wallets",[]): self.wallet.addItem(f"Wallet #{w['wallet_id']} · {w['currency']} · {w['status']}",w['wallet_id'])
        self.bank.clear()
        for b in data.get("banks",[]): self.bank.addItem(b['name'],b['bank_id'])
        self.table.set_rows(data.get("bank_accounts") or [])
    def link_bank(self):
        wallet_id,bank_id=self.wallet.currentData(),self.bank.currentData(); account=self.account_number.text().strip()
        if wallet_id is None or bank_id is None: self.show_error("Choose a wallet and an active partner bank first."); return
        if not account.isdigit() or not 6<=len(account)<=34: self.show_error("Bank account number must contain 6-34 digits."); self.account_number.setFocus(); return
        self.run_api(self.api.link_bank,self.state.user_id,wallet_id,bank_id,account,write=True,on_success=lambda result:self._bank_linked(result,wallet_id))
    def _bank_linked(self,result,wallet_id):
        self.account_number.clear(); notify(self,"Bank connected",f"{result.get('bank_name','Partner bank')} connected to wallet #{wallet_id}. Reference: {result.get('bank_account_id','—')}"); self.refresh()
    def unlink_bank(self):
        row=self.table.currentRow()
        if row<0: self.show_error("Select a bank link first."); return
        try: link_id=int(self.table.item(row,0).text()); bank_name=self.table.item(row,3).text(); status=self.table.item(row,5).text()
        except (AttributeError,TypeError,ValueError): self.show_error("The selected bank link is invalid. Refresh and try again."); return
        if status!="SUCCESS": self.show_error("Only an active bank link can be cancelled."); return
        if not confirm(self,"Unlink bank",f"Cancel the link to {bank_name}? The history will be preserved."): return
        self.run_api(self.api.unlink_bank,self.state.user_id,link_id,write=True,on_success=lambda _r:self._unlinked(bank_name))
    def _unlinked(self,bank_name): notify(self,"Bank unlinked",f"The link to {bank_name} was cancelled. History was preserved."); self.refresh()
