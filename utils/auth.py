from config import ADMIN_IDS

def is_admin(user_id):
    """Проверяет, является ли пользователь администратором"""
    return user_id in ADMIN_IDS

async def check_admin(update, context):
    """Проверяет права и отправляет сообщение если нет доступа"""
    user_id = update.effective_user.id
    if not is_admin(user_id):
        if update.message:
            await update.message.reply_text("❌ У вас нет прав для выполнения этой команды")
        else:
            await update.callback_query.answer("❌ Нет прав доступа", show_alert=True)
        return False
    return True