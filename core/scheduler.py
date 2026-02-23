import mesa

class CustomScheduler(mesa.time.RandomActivation):
    """Кастомное расписание, если потребуется особая логика порядка шагов."""
    def __init__(self, model):
        super().__init__(model)

    def step(self):
        """Выполняет шаг всех агентов в порядке, заданном моделью."""
        # Мы будем вызывать step агентов в нужном порядке из метода model.step,
        # поэтому здесь просто вызываем все step по умолчанию.
        # Но для точного контроля можно переопределить.
        super().step()