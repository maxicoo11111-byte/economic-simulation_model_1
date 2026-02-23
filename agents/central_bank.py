import mesa

class CentralBank(mesa.Agent):
    """Центральный банк — агрегирует кредиты и депозиты."""
    def __init__(self, unique_id, model, initial_capital):
        super().__init__(unique_id, model)
        self.capital = initial_capital
        self.total_loans = 0
        self.total_deposits = 0

    def step(self):
        # Обновляем статистику после всех операций
        self.update_stats()

    def update_stats(self):
        accounts = self.model.clearing_house.accounts
        self.total_loans = sum(-b for b in accounts.values() if b < 0 and b != 5)
        self.total_deposits = sum(b for b in accounts.values() if b > 0 and b != 5)
        # Баланс банка должен быть равен капиталу, но может отличаться из-за кредитов.
        # Мы не храним активы банка как отдельный счёт, а просто вычисляем.

    def get_capital_adequacy(self):
        if self.total_loans == 0:
            return float('inf')
        return self.capital / self.total_loans