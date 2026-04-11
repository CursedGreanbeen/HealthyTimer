from dotenv import load_dotenv
import os
from dateutil import parser
import asyncio
from telegram import Update
from telegram.ext import Application, filters, ContextTypes
from telegram.ext import ConversationHandler, MessageHandler, CommandHandler, CallbackQueryHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from healthytimer.controller import TaskService
from healthytimer.scheduler import Scheduler
from healthytimer.storage import Storage
from healthytimer.rearranger import Rearranger
from healthytimer.notifier import Notifier
from healthytimer.models import Task, Routine, TimeUnit, Importance


load_dotenv()
TOKEN = os.getenv("TOKEN")
ASK_MAX_TASKS = 100


def main_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("Добавить рутину", callback_data="new_routine")],
        [InlineKeyboardButton("Добавить задание", callback_data="new_single_time")],
        [InlineKeyboardButton("Посмотреть недельный план", callback_data="view_tasks")],
        [InlineKeyboardButton("Изменить лимит", callback_data="max_per_day")],
    ]
    return InlineKeyboardMarkup(keyboard)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет, я твой личный таск-менеджер! "
                                    "Сколько дел ты планируешь выполнять ежедневно?")
    return ASK_MAX_TASKS

async def switch_message(query, text, reply_markup=None):
    await query.message.delete()
    await query.message.chat.send_message(text, reply_markup=reply_markup)

async def get_max_per_day(update, context):
    chat_id = update.effective_user.id  # ??
    max_per_day = int(update.message.text)
    storage = context.bot_data['storage']
    storage.init_user(chat_id, max_per_day)

    await update.message.reply_text(f"Хорошо, я буду стараться составлять график на ближайшую "
                                    f"неделю так, чтобы у тебя было не больше {update.message.text} "
                                    f"дел в день (по возможности)", reply_markup=main_menu_keyboard())
    return ConversationHandler.END

async def menu(update, context):
    await update.message.reply_text(f"Что хочешь сделать дальше?", reply_markup=main_menu_keyboard())
    return ConversationHandler.END

async def handle_menu(update, context):
    query = update.callback_query
    await query.answer()

    if query.data == "new_routine":
        await query.message.reply_text("Добавим регулярную задачу")
    elif query.data == "new_single_time":
        await query.message.reply_text("Добавим разовую задачу")
    elif query.data == "view_tasks":
        await query.message.reply_text("Все твои задачи на ближайшую неделю")
    else:
        await query.message.reply_text("Сколько задач в день всё-таки хочешь делать?")

# ROUTINE CONVERSATION
#region
(ROUTINE_NAME, ROUTINE_UNIT, ROUTINE_INTERVAL,
 ROUTINE_IMPORTANCE, ROUTINE_FLEXIBLE) = range(5)

async def ask_routine_name(update, context):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text("Введи название")
    return ROUTINE_NAME

async def ask_routine_unit(update, context):
    context.user_data["routine_name"] = update.message.text
    keyboard = [
        [InlineKeyboardButton("Мины", callback_data="minutes")],
        [InlineKeyboardButton("Часы", callback_data="hours")],
        [InlineKeyboardButton("Дни", callback_data="days")],
        [InlineKeyboardButton("Недели", callback_data="weeks")],
        [InlineKeyboardButton("Месяцы", callback_data="months")],
        [InlineKeyboardButton("Годы", callback_data="years")],
    ]
    await update.message.reply_text("Единица времени", reply_markup=InlineKeyboardMarkup(keyboard))
    return ROUTINE_UNIT

async def ask_routine_interval(update, context):
    context.user_data["routine_unit"] = update.callback_query.data
    await update.callback_query.message.reply_text("Интервал (числом)")
    return ROUTINE_INTERVAL

async def ask_routine_importance(update, context):
    context.user_data["routine_interval"] = update.message.text
    keyboard = [
        [InlineKeyboardButton("Низкая", callback_data="low")],
        [InlineKeyboardButton("Средняя", callback_data="medium")],
        [InlineKeyboardButton("Высокая", callback_data="high")],
    ]
    await update.message.reply_text("Важность", reply_markup=InlineKeyboardMarkup(keyboard))
    return ROUTINE_IMPORTANCE

async def ask_routine_flexible(update, context):
    context.user_data["routine_importance"] = update.callback_query.data
    keyboard = [[
        InlineKeyboardButton("Да", callback_data="true"),
        InlineKeyboardButton("Нет", callback_data="false"),
    ]]
    await update.callback_query.message.reply_text("Можно ли переносить дату/время выполнения?", reply_markup=InlineKeyboardMarkup(keyboard))
    return ROUTINE_FLEXIBLE

async def save_routine(update, context):
    user_id = update.callback_query.from_user.id
    storage = context.bot_data['storage']
    controller = context.bot_data["controller"]
    max_per_day = storage.get_max_per_day(user_id)
    context.user_data["routine_flexible"] = update.callback_query.data == "true"
    importance_map = {
        'low': Importance.LOW,
        'medium': Importance.MEDIUM,
        'high': Importance.HIGH
    }
    unit_map = {
        'minutes': TimeUnit.MINUTES,
        'hours': TimeUnit.HOURS,
        'days': TimeUnit.DAYS,
        'weeks': TimeUnit.WEEKS,
        'months': TimeUnit.MONTHS,
        'years': TimeUnit.YEARS
    }
    importance = importance_map[context.user_data["routine_importance"]]
    unit = unit_map[context.user_data["routine_unit"]]
    controller.create_routine(
        user_id=user_id,
        name=context.user_data["routine_name"],
        interval_time=float(context.user_data["routine_interval"]),
        unit=unit,
        importance=importance,
        is_flexible=context.user_data["routine_flexible"],
        max_per_day=max_per_day
    )
    await update.callback_query.message.reply_text(f"Готово! Добавлена задача {context.user_data["routine_name"]}")
    return ConversationHandler.END
#endregion

# SINGLE-TIME CONVERSATION
#region
(SINGLE_TIME_NAME, SINGLE_TIME_DATE,
 SINGLE_TIME_IMPORTANCE, SINGLE_TIME_FLEXIBLE) = range(4)

async def ask_single_time_name(update, context):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text("Введи название")
    return SINGLE_TIME_NAME

async def ask_single_time_date(update, context):
    context.user_data["single_time_name"] = update.message.text
    await update.message.reply_text("Дата")
    return SINGLE_TIME_DATE

async def ask_single_time_importance(update, context):
    context.user_data["single_time_date"] = update.message.text
    keyboard = [
        [InlineKeyboardButton("Низкая", callback_data="low")],
        [InlineKeyboardButton("Средняя", callback_data="medium")],
        [InlineKeyboardButton("Высокая", callback_data="high")],
    ]
    await update.message.reply_text("Важность выполнения", reply_markup=InlineKeyboardMarkup(keyboard))
    return SINGLE_TIME_IMPORTANCE

async def ask_single_time_flexible(update, context):
    context.user_data["single_time_importance"] = update.callback_query.data
    keyboard = [[
        InlineKeyboardButton("Да", callback_data="true"),
        InlineKeyboardButton("Нет", callback_data="false"),
    ]]
    await update.callback_query.message.reply_text("Можно ли переносить дату/время выполнения?",
                                                   reply_markup=InlineKeyboardMarkup(keyboard))
    return SINGLE_TIME_FLEXIBLE

async def save_single_time(update, context):
    user_id = update.callback_query.from_user.id
    storage = context.bot_data['storage']
    controller = context.bot_data["controller"]
    max_per_day = storage.get_max_per_day(user_id)
    context.user_data["single_time_flexible"] = update.callback_query.data == "true"
    importance_map = {
        'low': Importance.LOW,
        'medium': Importance.MEDIUM,
        'high': Importance.HIGH
    }
    importance = importance_map[context.user_data["single_time_importance"]]
    date_str = context.user_data["single_time_date"]
    try:
        due_date = parser.parse(date_str, dayfirst=True).date()
        if context.user_data.get("mode") == "edit":
            controller.update_single_time(
                user_id=user_id,
                name=context.user_data["single_time_name"],
                importance=importance,
                is_flexible=context.user_data["single_time_flexible"],
                date=due_date,
                max_per_day=max_per_day
            )
            await update.callback_query.message.reply_text(f"Готово! Задача {context.user_data["single_time_name"]}"
                                                           f" обновлена")

        else:
            controller.create_single_time(
                user_id=user_id,
                name=context.user_data["single_time_name"],
                importance=importance,
                is_flexible=context.user_data["single_time_flexible"],
                date=due_date,
                max_per_day=max_per_day
            )
            await update.callback_query.message.reply_text(f"Готово! Добавлена задача "
                                                           f"{context.user_data["single_time_name"]}")

    except (ValueError, OverflowError, parser.ParserError):
        await update.callback_query.message.reply_text(
            "Не удалось распознать дату. Правильный формат: ДД.ММ.ГГГГ"
        )
    return ConversationHandler.END
#endregion

# VIEW TASKS CONVERSATION
#region
async def view_tasks(update, context):
    query = update.callback_query
    controller = context.bot_data["controller"]
    user_id = update.effective_user.id
    week = controller.collect_week(user_id)
    # importance_map = {
    #     Importance.LOW: 'Низкая важность',
    #     Importance.MEDIUM: 'Средняя важность',
    #     Importance.HIGH: 'Высокая важность',
    # }

    for day, tasks in week.items():
        if tasks:
            keyboard = []
            for task in tasks:
                # task_info = f"{task.name} - {importance_map[task.importance]}"
                task_info = f"{task.name}"
                keyboard.append([InlineKeyboardButton(task_info, callback_data=f"task_{task.id}")])
            await update.callback_query.message.reply_text(
                f"Все дела на {day}:",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        else:
            await update.callback_query.message.reply_text(f"Нет задач на {day}")
#endregion


(CHOSEN_FIELD, ENTERED_VALUE) = range(2)
async def manage_task(update, context):
    await update.callback_query.answer()
    storage = context.bot_data['storage']
    importance_map = {
        Importance.LOW: 'Низкая важность',
        Importance.MEDIUM: 'Средняя важность',
        Importance.HIGH: 'Высокая важность',
    }
    task_id = int(update.callback_query.data.split("_")[1])
    task = storage.find_task(task_id)
    importance = importance_map[task.importance]
    if isinstance(task, Routine):
        keyboard = [
            [InlineKeyboardButton("Изменить", callback_data="edit_routine")],
            [InlineKeyboardButton("Отменить", callback_data="cancel_routine")],
            [InlineKeyboardButton("Удалить", callback_data="delete_routine")],
        ]
        await update.callback_query.message.reply_text(f"<b>Задача:</b> {task.name}\n\n"
                                                       f"📅 Интервал: {int(task.interval_time)} {task.unit}\n"
                                                       f"⭐ {importance}\n"
                                                       f"🔄 Гибкая: {task.is_flexible}",
                                                       parse_mode="HTML",
                                                       reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        keyboard = [
            [InlineKeyboardButton("Изменить", callback_data="edit_single_task")],
            [InlineKeyboardButton("Удалить", callback_data="delete_single_task")],
        ]
        await update.callback_query.message.reply_text(f"<b>Задача:</b> {task.name}\n\n"
                                                       f"📅 {task.due_date.date()}\n"
                                                       f"⭐ {importance}\n"
                                                       f"🔄 Гибкая: {task.is_flexible}",
                                                       parse_mode="HTML",
                                                       reply_markup=InlineKeyboardMarkup(keyboard))

async def edit_routine(update, context):
    await update.callback_query.answer()
    storage = context.bot_data['storage']
    task_id = int(update.callback_query.data.split("_")[1])
    task = storage.find_task(task_id)

    context.user_data["mode"] = "edit"
    context.user_data["task_id"] = task_id
    keyboard = [
        [InlineKeyboardButton("Название", callback_data="routine_name")],
        [InlineKeyboardButton("Интервал", callback_data="routine_interval")],
        [InlineKeyboardButton("Единицы времени", callback_data="routine_unit")],
        [InlineKeyboardButton("Важность", callback_data="routine_importance")],
        [InlineKeyboardButton("Гибкость", callback_data="routine_flexible")],
    ]
    await update.callback_query.message.reply_text(f"Что хочешь изменить?\n\n"
                                                   f"<b>Задача:</b> {task.name}\n"
                                                   f"📅 Интервал: {int(task.interval_time)} {task.unit}\n"
                                                   f"⭐ {task.importance}\n"
                                                   f"🔄 Гибкая: {task.is_flexible}",
                                                   parse_mode="HTML",
                                                   reply_markup=InlineKeyboardMarkup(keyboard))

async def edit_single_time(update, context):
    await update.callback_query.answer()
    storage = context.bot_data['storage']
    task_id = int(update.callback_query.data.split("_")[1])
    task = storage.find_task(task_id)
    keyboard = [
        [InlineKeyboardButton("Название", callback_data="single_time_name")],
        [InlineKeyboardButton("Дата", callback_data="single_time_date")],
        [InlineKeyboardButton("Важность", callback_data="single_time_importance")],
        [InlineKeyboardButton("Гибкость", callback_data="single_time_flexible")],
    ]
    await update.callback_query.message.reply_text(f"Что хочешь изменить?\n\n"
                                                   f"<b>Задача:</b> {task.name}\n"
                                                   f"📅 {task.due_date.date()}\n"
                                                   f"⭐ {task.importance}\n"
                                                   f"🔄 Гибкая: {task.is_flexible}",
                                                   parse_mode="HTML",
                                                   reply_markup=InlineKeyboardMarkup(keyboard))

async def delete_task(update, context):
    await update.callback_query.answer()
    storage = context.bot_data['storage']
    task_id = int(update.callback_query.data.split("_")[1])
    task = storage.find_task(task_id)
    keyboard = [
        [InlineKeyboardButton("Да", callback_data="true")],
        [InlineKeyboardButton("Нет", callback_data="false")],
    ]
    await update.callback_query.message.reply_text(f"Удаляем {task.name}?",
                                                   reply_markup=InlineKeyboardMarkup(keyboard))


# CONVERSATION HANDLERS
#region
registration_handler = ConversationHandler(
    entry_points=[CommandHandler("start", start)],
    states={
        ASK_MAX_TASKS: [MessageHandler(filters.TEXT, get_max_per_day)]
    },
    fallbacks=[],
    per_message=False
)

menu_handler = CommandHandler("menu", menu)

routine_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(ask_routine_name, pattern="^new_routine$")],
    states={
        ROUTINE_NAME: [MessageHandler(filters.TEXT, ask_routine_unit)],
        ROUTINE_UNIT: [CallbackQueryHandler(ask_routine_interval)],
        ROUTINE_INTERVAL: [MessageHandler(filters.TEXT, ask_routine_importance)],
        ROUTINE_IMPORTANCE: [CallbackQueryHandler(ask_routine_flexible)],
        ROUTINE_FLEXIBLE: [CallbackQueryHandler(save_routine)],
    },
    fallbacks=[],
    per_message=False
)

single_time_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(ask_single_time_name, pattern="^new_single_time$")],
    states={
        SINGLE_TIME_NAME: [MessageHandler(filters.TEXT, ask_single_time_date)],
        SINGLE_TIME_DATE: [MessageHandler(filters.TEXT, ask_single_time_importance)],
        SINGLE_TIME_IMPORTANCE: [CallbackQueryHandler(ask_single_time_flexible)],
        SINGLE_TIME_FLEXIBLE: [CallbackQueryHandler(save_single_time)],
    },
    fallbacks=[],
    per_message=False
)

view_tasks_handler = CallbackQueryHandler(view_tasks, pattern="^view_tasks$")

edit_tasks_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(manage_task, pattern=r"^task_\d+$")],
    states={
        CHOSEN_FIELD: [CallbackQueryHandler(edit_routine, pattern=r"^task_\d+$")],
        # ENTERED_VALUE: [MessageHandler(filters.TEXT, _)],
    },
    fallbacks=[],
    per_message=False
)
#endregion

db_path = os.path.join(os.path.dirname(__file__), "tasks_users.db")

async def startup(app):
    loop = asyncio.get_running_loop()

    notifier = Notifier(app, loop)
    storage = Storage(db_path)
    scheduler = Scheduler(notifier=notifier, storage=storage)
    rearranger = Rearranger(notify_callback=notifier.notify_overload, week={})
    controller = TaskService(storage=storage, scheduler=scheduler, rearranger=rearranger)

    app.bot_data['storage'] = storage
    app.bot_data['controller'] = controller

app = Application.builder().token(TOKEN).post_init(startup).build()
app.add_handler(registration_handler)
app.add_handler(menu_handler)
app.add_handler(routine_handler)
app.add_handler(single_time_handler)
app.add_handler(view_tasks_handler)
app.add_handler(edit_tasks_handler)
app.run_polling()
