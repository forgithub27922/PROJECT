odoo.define('grimm_web.account_move_doc', function(require) {
    "use strict";

    var config = require('web.config');
    var dom = require('web.dom');
    var FormRenderer = require('web.FormRenderer');

    FormRenderer.include({
        _interchangeChatter: function (enablePreview) {
            if (config.device.size_class < config.device.SIZES.XXL) {
                return;
            }

            var $sheet = this.$('.o_form_sheet_bg');
            if (!this.$attachmentPreview) {
                if (this.chatter !== undefined) {
                    this.$('.o_form_sheet').css('max-width', '100%');
                    this.chatter.$el.insertAfter($sheet.parent());
                }
                return;
            }

            if (enablePreview) {
                this.$attachmentPreview.insertAfter($sheet);
                dom.append($sheet, this.chatter.$el, {
                    callbacks: [{ widget: this.chatter }],
                    in_DOM: this._isInDom,
                });
            } else {
                this.chatter.$el.insertAfter($sheet);
                dom.append($sheet, this.$attachmentPreview, {
                    callbacks: [],
                    in_DOM: this._isInDom,
                });
            }
        },
    });
});