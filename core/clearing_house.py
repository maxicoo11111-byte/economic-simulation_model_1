from utils.rounding import proportional_split

class ClearingHouse:
    """Централизованный учёт счетов и проведение транзакций."""

    def __init__(self, model):
        self.model = model
        self.accounts = {}  # agent_id -> balance

    def add_account(self, agent_id, initial_balance):
        self.accounts[agent_id] = initial_balance

    def transfer(self, sender_id, recipient_id, amount, is_taxable=False, tax_rate=None):
        """
        Выполняет перевод денег.
        Если is_taxable=True, вычисляется налог tax = round(amount * tax_rate)
        и переводится на счёт налоговой службы (ID=1).
        Возвращает True, если операция выполнена (всегда, даже если уходим в минус).
        """
        tax = 0
        total_debit = amount
        if is_taxable and tax_rate is not None:
            tax = round(amount * tax_rate)
            total_debit = amount + tax

        sender_balance = self.accounts.get(sender_id, 0)
        # Разрешаем отрицательный баланс – просто списываем
        self.accounts[sender_id] = sender_balance - total_debit

        # Зачисление получателю
        self.accounts[recipient_id] = self.accounts.get(recipient_id, 0) + amount

        if tax > 0:
            tax_service_id = 1  # ID налоговой службы
            self.accounts[tax_service_id] = self.accounts.get(tax_service_id, 0) + tax

        return True

    def check_invariant(self, model):
        """
        Проверяет балансовое тождество:
        сумма всех российских счетов + счёт внешнего мира = капитал банка.
        """
        russian_ids = [aid for aid in self.accounts.keys() if aid not in [5]]  # 5 = foreign
        total_russian = sum(self.accounts.get(aid, 0) for aid in russian_ids)
        foreign_balance = self.accounts.get(5, 0)
        total = total_russian + foreign_balance
        capital = model.central_bank.capital
        # Допуск в 1 рубль из-за округлений
        if abs(total - capital) > 1:
            raise ValueError(f"Балансовое тождество нарушено: total={total}, capital={capital}")