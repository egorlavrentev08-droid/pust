async def class_update_paid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Платная смена класса (ИЗМЕНЕНИЕ 9).
    Цена: 100 RF И 10,000 RC одновременно.
    """
    user_id = update.effective_user.id
    session = Session()
    user = session.query(User).filter_by(user_id=user_id).first()

    if not context.args:
        await update.message.reply_text("💰 Смена стоит *100 RF и 10,000 RC*.\n`/class pay [название]`", parse_mode='Markdown')
        return

    new_class = context.args[0].lower()
    if new_class not in AVAILABLE_CLASSES:
        await update.message.reply_text("❌ Такого класса не существует.")
        return

    # ПРОВЕРКА: есть ли обе валюты
    if user.radfragments >= 100 and user.radcoins >= 10000:
        user.radfragments -= 100
        user.radcoins -= 10000
        user.user_class = new_class
        session.commit()
        await update.message.reply_text(f"✅ Оплата принята! Списано 100 RF и 10,000 RC.\nВаш новый класс: *{AVAILABLE_CLASSES[new_class]}*", parse_mode='Markdown')
    else:
        await update.message.reply_text(f"❌ Недостаточно средств. Нужно 100 RF (у вас {user.radfragments}) и 10,000 RC (у вас {int(user.radcoins)}).")
    
    session.close()
