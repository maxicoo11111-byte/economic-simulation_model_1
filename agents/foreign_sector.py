import mesa

class ForeignSector(mesa.Agent):
    """Внешний мир — импорт и экспорт."""
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.balance = 0

    def step(self):
        # В фазе экспорта получаем деньги от внешнего мира и перечисляем фирмам
        total_export = self.model.config['foreign_trade']['total_export_value']
        export_share_s3 = self.model.config['foreign_trade']['export_sector_3_share']
        # Пока только сектор 3 (добыча)
        firms_s3 = [f for f in self.model.firms if f.sector == 3]
        if firms_s3:
            # Распределяем экспорт между фирмами сектора 3 пропорционально размеру
            sizes = [f.size for f in firms_s3]
            amounts = proportional_split(round(total_export * export_share_s3), sizes)
            for firm, amt in zip(firms_s3, amounts):
                firm.receive_export(amt)
        # Импорт уже учтён при покупках домохозяйств и фирм
        self.balance = self.model.clearing_house.accounts.get(self.unique_id, 0)