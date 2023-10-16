console.log("chat_manager.js is called....!!!")
odoo.define('grimm_crm.chat_manager', function (require) {
    "use strict";

    var chat_manager = require('mail.chat_manager');
    var original_make_message = chat_manager.make_message;
    
    chat_manager.make_message = function (data) {
        var msg = original_make_message(data);
        msg.partner_ids = data.partner_ids;
        msg.parent_reply_id = data.parent_reply_id[0];

        if (msg.message_type != 'notification' && (!msg.body_short || msg.body_short == '') && data.body.length > 100 && data.body.indexOf('<hr') != -1) {
            msg.body_short = data.body.slice(0, data.body.indexOf('<hr'));
            msg.body_short = msg.body_short.replace(/<br>/g,'') + '<br><a href="#" class="oe_mail_expand">weiterlesen</a>';
        }

        return msg;
    };

});