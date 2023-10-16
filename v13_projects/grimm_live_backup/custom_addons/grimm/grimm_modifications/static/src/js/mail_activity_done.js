odoo.define('grimm_modifications.mail_activity_done', function (require) {
    "use strict";

    var chat_manager = require('mail.chat_manager');

    function get_channel_cache (channel, domain) {
        var stringified_domain = JSON.stringify(domain || []);
        if (!channel.cache[stringified_domain]) {
            channel.cache[stringified_domain] = {
                all_history_loaded: false,
                loaded: false,
                messages: [],
            };
        }
        return channel.cache[stringified_domain];
    }

    chat_manager.get_messages = function (options) {
        var channel;

        if ('channel_id' in options && options.load_more) {
            // get channel messages, force load_more
            channel = this.get_channel(options.channel_id);
            return this._fetchFromChannel(channel, {
                            domain: options.domain || {},
                            load_more: true
                            });
        }
        if ('channel_id' in options) {
            // channel message, check in cache first
            channel = this.get_channel(options.channel_id);
            var channel_cache = get_channel_cache(channel, options.domain);
            if (channel_cache.loaded) {
                return $.when(channel_cache.messages);
            } else {
                return this._fetchFromChannel(channel, {
                domain: options.domain
                });
            }
        }
        if ('ids' in options) {
            // get messages from their ids (chatter is the main use case)
            return this._fetchDocumentMessages(options.ids, options).then(function(result) {
                if (options.shouldMarkAsRead) { // DO NOT FORWARD-PORT
//                    chat_manager.mark_as_read(options.ids); // DO NOT FORWARD-PORT
                } // DO NOT FORWARD-PORT
                return result;
            });
        }
        if ('model' in options && 'res_id' in options) {
            // get messages for a chatter, when it doesn't know the ids (use
            // case is when using the full composer)
            var domain = [['model', '=', options.model], ['res_id', '=', options.res_id]];
            this._rpc({
                    model: 'mail.message',
                    method: 'message_fetch',
                    args: [domain],
                    kwargs: {limit: 30},
                })
                .then(function (msgs) {
                    return _.map(msgs, add_message);
                });
        }
    };
});