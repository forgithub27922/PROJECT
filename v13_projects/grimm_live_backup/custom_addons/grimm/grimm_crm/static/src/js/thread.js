console.log("thread.js is called....!!!")
odoo.define('grimm_crm.DocumentThread', function (require) {
    "use strict";

    var DocumentThread = require('mail.model.DocumentThread');
    var MessagingMenu = require('mail.systray.MessagingMenu');

    DocumentThread.include({
        _markAsRead: function () {
            return true //our colleagues wants message to mark as read only when they click on mark as read button. So here returned when they click on/open message.
            var self = this;
            return this._super.apply(this, arguments).then(function () {
                self.call('mail_service', 'markMessagesAsRead', self._messageIDs);
            });
        },
        grimmMarkAsRead: function () {
            var self = this;
            self.call('mail_service', 'markMessagesAsRead', self._messageIDs);
        },
    });

    MessagingMenu.include({
        _markAsRead: function ($preview) {
            var previewID = $preview.data('preview-id');
            if (previewID === 'mailbox_inbox') {
                var messageIDs = $preview.data('message-ids');

                if (typeof messageIDs === 'string') {
                    messageIDs = messageIDs.split(',').map(id => Number(id));
                } else {
                    messageIDs = [$preview.data('message-ids')];
                }

                this.call('mail_service', 'markMessagesAsRead', messageIDs);
            } else if (previewID === 'mail_failure') {
                var documentModel = $preview.data('document-model');
                var unreadCounter = $preview.data('unread-counter');
                this.do_action('mail.mail_resend_cancel_action', {
                    additional_context: {
                        default_model: documentModel,
                        unread_counter: unreadCounter
                    }
                });
            } else {
                // this is mark as read on a thread
                var thread = this.call('mail_service', 'getThread', previewID);
                if (thread) {
                    //thread.markAsRead();
                    thread.grimmMarkAsRead() //Grimm Override for maras read from System Tray.
                }
            }
        },
    });
});