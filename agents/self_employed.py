import mesa

class SelfEmployed(mesa.Agent):
    """Агент-самозанятый. Упрощённо: один работник."""
    def __init__(self, unique_id, model, params):
        super().__init__(unique_id, model)
        self.region_id = params['region_id']
        self.savings = params.get('savings', 0)
        self.income = params.get('income', 40000)  # среднемесячный доход (до вычета налога)
        self.size = 1  # для совместимости с фирмами

    def step(self):
        # Самозанятые не имеют сложной логики, они просто продают товары.
        # Их доход формируется за счёт покупок домохозяйств.
        pass

    def receive_revenue(self, amount):
        self.model.clearing_house.transfer(0, self.unique_id, amount, is_taxable=False)
        self.savings = self.model.clearing_house.accounts.get(self.unique_id, 0)