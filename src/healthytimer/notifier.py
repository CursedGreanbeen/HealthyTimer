import asyncio


class Notifier:
    def __init__(self, app, loop):
        self.app = app
        self.loop = loop

    def notify_task(self, task):
        coro = self.app.bot.send_message(chat_id=task.user_id, text=f"Напоминание: {task.name}")
        asyncio.run_coroutine_threadsafe(coro, self.loop)

    def notify_overload(self, date, user_id):
        coro = self.app.bot.send_message(chat_id=user_id,
                                         text=f"Мне не удалось снизить ежедневную нагрузку до лимита. "
                                              f"Оставшиеся задачи будут отправлены на {date}")
        asyncio.run_coroutine_threadsafe(coro, self.loop)
