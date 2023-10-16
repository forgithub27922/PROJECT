odoo.define('grimm_web.DocumentViewer', function (require) {
    "use strict";

    var core = require('web.core');
    var Widget = require('web.Widget');
    var ajax = require('web.ajax');
    var DocumentViewer = require('mail.DocumentViewer');
    var Session = require('web.session');
    var QWeb = core.qweb;

    DocumentViewer.include({
        events: _.extend({}, DocumentViewer.prototype.events, {
            'click .o_preview_mail': '_stayOpened',
            'click .o_preview_csv': '_stayOpened',
        }),
        init: function (parent, attachments, activeAttachmentID) {
            this._super.apply(this, arguments);
            this.attachment = _.filter(attachments, function (attachment) {
                var match = attachment.type === 'url' ? attachment.url.match("(youtu|.png|.jpg|.gif)") : attachment.mimetype.match("(image|video|application/pdf|text/csv|text|message/rfc822)");
                if (match) {
                    attachment.fileType = match[1] === "text/csv" ? "csv" : match[1];
                    if (match[1].match("(.png|.jpg|.gif)")) {
                        attachment.fileType = 'image';
                    }
                    if (match[1] === 'youtu') {
                        var youtube_array = attachment.url.split('/');
                        var youtube_token = youtube_array[youtube_array.length-1];
                        if (youtube_token.indexOf('watch') !== -1) {
                            youtube_token = youtube_token.split('v=')[1];
                            var amp = youtube_token.indexOf('&')
                            if (amp !== -1){
                                youtube_token = youtube_token.substring(0, amp);
                            }
                        }
                        attachment.youtube = youtube_token;
                    }
                    return true;
                }
            });
            this.activeAttachment = _.findWhere(attachments, {id: activeAttachmentID});
            this.modelName = 'ir.attachment';
            this.csv_preview();
            this.mail_preview();
            this._reset();
        },
        _updateContent: function () {
            this.$('.o_viewer_content').html(QWeb.render('DocumentViewer.Content', {
                widget: this
            }));
            this.csv_preview();
            this.mail_preview();
            this.$('.o_viewer_img').on("load", _.bind(this._onImageLoaded, this));
            this.$('[data-toggle="tooltip"]').tooltip({delay: 0});
            this._reset();
        },
        mail_preview: function () {
            if (this.activeAttachment.mimetype == "message/rfc822") {
                var self = this;
                Session.rpc('/web/preview/mail', {url: this.activeAttachment.url}).then(function (mail) {
                    mail = JSON.parse(JSON.stringify(mail));
                    var $content = $(QWeb.render('MailHTMLContent'));
                    $content.find('#subject').text(mail.subject);
                    $content.find('#meta-to').text(mail.to);
                    $content.find('#meta-cc').text(mail.cc);
                    $content.find('#meta-from').text(mail.from);
                    $content.find('#meta-date').text(mail.date);
                    $content.find('#body').html(mail.body);
                    self.$('.o_viewer_zoomer').html($content);
                });
            }
        },
        csv_preview: function () {
            if (this.activeAttachment.mimetype == "text/csv") {
                var self = this;
                var $content = $(QWeb.render('CSVHTMLContent'));
                ajax.loadLibs(this).then(function() {
                    Papa.parse(self.activeAttachment.url, {
                        download: true,
                        dynamicTyping: true,
                        complete: function(results) {
                            $content.find('.csv-container').handsontable({
                                data: results.data,
                                colHeaders: true,
                                stretchH: 'all',
                                readOnly: true,
                                columnSorting: true,
                                autoColumnSize: true,
                            });
                            self.$('.o_viewer_zoomer').html($content);
                        }
                    });
                });
            }
        },
        _stayOpened: function (e) {
            e.stopPropagation();
        },
    });
});