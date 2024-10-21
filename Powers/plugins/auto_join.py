from traceback import format_exc

from pyrogram import filters
from pyrogram.enums import ChatMemberStatus as CMS
from pyrogram.types import CallbackQuery, ChatJoinRequest
from pyrogram.types import InlineKeyboardButton as ikb
from pyrogram.types import InlineKeyboardMarkup as ikm
from pyrogram.types import Message

from Powers import DEV_USERS, LOGGER, SUDO_USERS, WHITELIST_USERS
from Powers.bot_class import Gojo
from Powers.database.autojoin_db import AUTOJOIN
from Powers.utils.custom_filters import admin_filter, auto_join_filter, command


@Gojo.on_message(command(["joinreq"]) & admin_filter)
async def accept_join_requests(c: Gojo, m: Message):
    if m.chat.id == m.from_user.id:
        await m.reply_text("Use it in groups")
        return

    split = m.command
    a_j = AUTOJOIN()

    try:
        status = (await m.chat.get_member(c.me.id)).status
        if status != CMS.ADMINISTRATOR:
            await m.reply_text("I should be admin to accept and reject join requests")
            return
    except Exception as ef:
        await m.reply_text(f"Some error occured, report it using `/bug`\n<b>Error:</b> <code>{ef}</code>")
        LOGGER.error(ef)
        LOGGER.error(format_exc())
        return
    if len(split) == 1:
        txt = "**USAGE**\n/joinreq [on | off]"
        await m.reply_text(txt)
        return
    else:
        yes_no = split[1].lower()
        if yes_no not in ["on","off"]:
            txt = "**USAGE**\n/joinreq [on | off]"
            await m.reply_text(txt)
            return
        
        else:
            if yes_no == "on":
                is_al = a_j.load_autojoin(m.chat.id)
                
                if is_al:
                    txt = "Now I will approve all the join request of the chat\nIf you want that I will just notify admins about the join request use command\n//joinreqmode [manual | auto]"
                    await m.reply_text(txt)
                    return
                else:
                    txt = "Auto approve join request is already on for this chat\nIf you want that I will just notify admins about the join request use command\n/joinreqmode [manual | auto]"
                    await m.reply_text(txt)
                    return

            elif yes_no == "off":
                a_j.remove_autojoin(m.chat.id)
                txt = "Now I will neither auto approve join request nor notify any admins about it"
                await m.reply_text(txt)
                return

@Gojo.on_message(command("joinreqmode") & admin_filter)
async def join_request_mode(c: Gojo, m: Message):
    if m.chat.id == m.from_user.id:
        await m.reply_text("Use it in groups")
        return
    u_text = "**USAGE**\n/joinreqmode [auto | manual]\nauto: auto approve joins\nmanual: will notify admin about the join request"
        
    split = m.command
    a_j = AUTOJOIN()
        
    if len(split) == 1:
        await m.reply_text(u_text)
        return

    else:
        auto_manual = split[1]
        if auto_manual not in ["auto","manual"]:
            await m.reply_text(u_text)
            return
        else:
            a_j.update_join_type(m.chat.id,auto_manual)
            txt = "Changed join request type"
            await m.reply_text(txt)
            return


@Gojo.on_chat_join_request(auto_join_filter)
async def join_request_handler(c: Gojo, j: ChatJoinRequest):
    user = j.from_user.id
    userr = j.from_user
    chat = j.chat.id
    aj = AUTOJOIN()
    join_type = aj.get_autojoin(chat)
    SUPPORT_STAFF = DEV_USERS.union(SUDO_USERS).union(WHITELIST_USERS)

    if not join_type:
        return
    if join_type == "auto" or user in SUPPORT_STAFF:
        try:
            await c.approve_chat_join_request(chat,user)
        except Exception as ef:
            await c.send_message(chat,f"Some error occured while approving request, report it using `/bug`\n<b>Error:</b> <code>{ef}</code>")
            LOGGER.error(ef)
            LOGGER.error(format_exc())
    elif join_type == "manual":
        txt = "New join request is available\n**USER's INFO**\n"
        txt += f"Name: {userr.first_name} {userr.last_name if userr.last_name else ''}"
        txt += f"Mention: {userr.mention}"
        txt += f"Id: {user}"
        txt += f"Scam: {'True' if  userr.is_scam else 'False'}"
        if userr.username:
            txt+= f"Username: @{userr.username}"
        kb = [
            [
                ikb("Accept",f"accept_joinreq_uest_{user}"),
                ikb("Decline",f"decline_joinreq_uest_{user}")
            ]
        ]
        await c.send_message(chat,txt,reply_markup=ikm(kb))
        return

@Gojo.on_callback_query(filters.regex("^accept_joinreq_uest_") | filters.regex("^decline_joinreq_uest_"))
async def accept_decline_request(c:Gojo, q: CallbackQuery):
    user_id = q.from_user.id
    chat = q.message.chat.id
    user_status = (await q.message.chat.get_member(user_id)).status
    if user_status not in {CMS.OWNER, CMS.ADMINISTRATOR}:
        await q.answer(
            "You're not even an admin, don't try this explosive shit!",
            show_alert=True,
        )
        return

    split = q.data.split("_")
    chat = q.message.chat.id
    user = int(split[-1])
    data = split[0]

    if data == "accept":
        try:
            await c.approve_chat_join_request(chat,user)
            await q.answer(f"APPROVED: {user}",True)
        except Exception as ef:
            await c.send_message(chat,f"Some error occured while approving request, report it using `/bug`\n<b>Error:</b> <code>{ef}</code>")
            LOGGER.error(ef)
            LOGGER.error(format_exc())
            
    elif data == "decline":
        try:
            await c.decline_chat_join_request(chat,user)
            await q.answer(f"DECLINED: {user}")
        except Exception as ef:
            await c.send_message(chat,f"Some error occured while approving request, report it using `/bug`\n<b>Error:</b> <code>{ef}</code>")
            LOGGER.error(ef)
            LOGGER.error(format_exc())

    return

__PLUGIN__ = "auto join"

__alt_name__ = ["join_request"]


__HELP__ = """
**Auto join request**

**Admin commands:**
• /joinreq [on | off]: To switch on auto accept join request 
• /joinreqmode [auto | manual]: `auto` to accept join request automatically and `manual` to get notified when new join request is available
"""