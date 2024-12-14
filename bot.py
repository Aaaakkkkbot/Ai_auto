
', '-1002440247365'))

Dbclient = AsyncIOMotorClient(DB_URL)
Cluster = Dbclient['Cluster0']
Data = Cluster['users']
Bot = Client(name='AutoApproveBot', api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

async def get_fsub(bot, message):
    target_channel_id = AUTH_CHANNEL  # Your channel ID
    user_id = message.from_user.id
    try:
        # Check if user is a member of the required channel
        await bot.get_chat_member(target_channel_id, user_id)
    except UserNotParticipant:
        # Generate the channel invite link
        channel_link = (await bot.get_chat(target_channel_id)).invite_link
        join_button = InlineKeyboardButton("🔔 Join Our Channel", url=channel_link)

        # Display a message encouraging the user to join
        keyboard = [[join_button]]
        await message.reply(
            f"<b>👋 Hello {message.from_user.mention()}, Welcome!</b>\n\n"
            "📢 <b>Exclusive Access Alert!</b> ✨\n\n"
            "To unlock all the amazing features I offer, please join our updates channel. "
            "This helps us keep you informed and ensures top-notch service just for you! 😊\n\n"
            "<i>🚀 Join now and dive into a world of knowledge and creativity!</i>",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        return False
    else:
        return True

@Bot.on_message(filters.command("start") & filters.private)                    
async def start_handler(c, m):
    user_id = m.from_user.id
    if not await Data.find_one({'id': user_id}):
        await Data.insert_one({'id': user_id})
    # Force Subscription Check
    is_subscribed = await get_fsub(c, m)
    if not is_subscribed:
        return
    button = [[
        InlineKeyboardButton("⇆ ᴀᴅᴅ ᴍᴇ ᴛᴏ ʏᴏᴜʀ ɢʀᴏᴜᴘs ⇆", url=f"https://telegram.me/Shanu_Auto_Approval_Bot?startgroup=true&admin=invite_users"),
    ], [
        InlineKeyboardButton("• ᴜᴩᴅᴀᴛᴇꜱ •", url="https://t.me/AeroBots_Tm"),
        InlineKeyboardButton("• ꜱᴜᴩᴩᴏʀᴛ •", url="https://t.me/AeroBots_Group")
    ], [
        InlineKeyboardButton("⇆ ᴀᴅᴅ ᴍᴇ ᴛᴏ ʏᴏᴜʀ ᴄʜᴀɴɴᴇʟ ⇆", url=f"https://telegram.me/Shanu_Auto_Approval_Bot?startchannel=true&admin=invite_users")
    ]]
    return await m.reply_text(text=START_TEXT.format(m.from_user.mention), disable_web_page_preview=True, reply_markup=InlineKeyboardMarkup(button))

@Bot.on_message(filters.command(["broadcast", "users"]) & filters.user(ADMINS))
async def broadcast(c, m):
    if m.text == "/users":
        total_users = await Data.count_documents({})
        return await m.reply(f"Total Users: {total_users}")
    
    b_msg = m.reply_to_message
    if not b_msg:
        return await m.reply("Please reply to a message to broadcast.")
    
    sts = await m.reply_text("Broadcasting your message...")
    users = Data.find({})
    total_users = await Data.count_documents({})
    done, failed, success = 0, 0, 0
    start_time = time.time()

    async for user in users:
        user_id = int(user['id'])
        try:
            await b_msg.copy(chat_id=user_id)
            success += 1
        except FloodWait as e:
            await asyncio.sleep(e.value)
            await b_msg.copy(chat_id=user_id)
            success += 1
        except (InputUserDeactivated, PeerIdInvalid):
            await Data.delete_many({'id': user_id})
            failed += 1
        except UserIsBlocked:
            failed += 1
        except Exception as e:
            # Optionally log unexpected errors for debugging
            print(f"Error broadcasting to {user_id}: {e}")
            failed += 1
        done += 1

        # Update status for every user
        await sts.edit(f"Broadcast in progress:\n\nTotal Users: {total_users}\nCompleted: {done} / {total_users}\nSuccess: {success}\nFailed: {failed}")
    
    time_taken = datetime.timedelta(seconds=int(time.time() - start_time))
    await sts.delete()
    await m.reply_text(
        f"Broadcast Completed:\nCompleted in {time_taken} seconds.\n\n"
        f"Total Users: {total_users}\nCompleted: {done} / {total_users}\nSuccess: {success}\nFailed: {failed}",
        quote=True
    )

@Bot.on_chat_join_request()
async def req_accept(c, m):
    user_id = m.from_user.id
    chat_id = m.chat.id
    if not await Data.find_one({'id': user_id}): await Data.insert_one({'id': user_id})
    await c.approve_chat_join_request(chat_id, user_id)
    try: await c.send_message(user_id, ACCEPTED_TEXT.format(user=m.from_user.mention, chat=m.chat.title))
    except Exception as e: print(e)

Bot.run()
