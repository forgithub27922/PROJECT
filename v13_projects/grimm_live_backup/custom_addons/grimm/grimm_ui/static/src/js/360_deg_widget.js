odoo.define('grimm_ui.image_360', function (require) {
    "use strict";

    var AbstractFieldBinary = require('web.basic_fields').AbstractFieldBinary;
    var field_registry = require('web.field_registry');
    var FieldBinaryImage = require('web.basic_fields').FieldBinaryImage;
    var Dialog = require('web.Dialog');
    var core = require('web.core');
    var _t = core._t;
    var qweb = core.qweb;
    var utils = require('web.utils');
    var field_utils = require('web.field_utils');
    var session = require('web.session');

    var FieldPreviewBinary360 = FieldBinaryImage.include({
        events: _.extend({}, AbstractFieldBinary.prototype.events, {
            'click img': function () {
                if (this.mode === "readonly") {
                    this.trigger_up('bounce_edit');
                }
                if (this.model == "product.template" && this.name == "image_1920") {
                    this.on_image_clicked();
                }
            },
        }),
        _render: function () {
            var self = this;
            var url = this.placeholder;
            if (this.value) {
                if (!utils.is_bin_size(this.value)) {
                    url = 'data:image/png;base64,' + this.value;
                } else {
                    url = session.url('/web/image', {
                        model: this.model,
                        id: JSON.stringify(this.res_id),
                        field: this.nodeOptions.preview_image || this.name,
                        // unique forces a reload of the image when the record has been updated
                        unique: field_utils.format.datetime(this.recordData.__last_update).replace(/[^0-9]/g, ''),
                    });
                }
            }
            var img = "0";
            var img_360 = "0";
            if (this.recordData.barcode && (this.model == "product.template" || this.model == "product.product")) {
                $.ajax({
                    url : 'https://imageserver.partenics.de/odoo/' + self.recordData.barcode + '?format=json',
                    type: 'get',
                    data : {},
                    contentType: false,
                    cache: false,
                    processData:false
                    }).done(function (data) {
                        var res = JSON.parse(data);
                        var image_arr = res["images"];
                        if (res["count"] > 0) {
                            for (var i=0; i<res["count"]; i++) {
                              if(img == "0" && image_arr[i]["type"] == "image") {
                                img = "1";
                              }
                              if(img_360 == "0" && image_arr[i]["type"] == "360") {
                                img_360 = "1";
                              }
                            }
                        }
                        var $img = $(qweb.render("FieldBinaryImage-img", {widget: self, url: url, 'image': img, 'img_360': img_360}));
                        self.$('> img').remove();
                        self.$el.prepend($img);
                        $img.on('error', function () {
                            self.on_clear();
                            $img.attr('src', self.placeholder);
                            self.do_warn(_t("Image"), _t("Could not display the selected image."));
                        });
                    });
            } else {
                var $img = $(qweb.render("FieldBinaryImage-img", {widget: this, url: url, 'image': img, 'img_360': img_360}));
                this.$('> img').remove();
                this.$el.prepend($img);
                $img.on('error', function () {
                    self.on_clear();
                    $img.attr('src', self.placeholder);
                    self.do_warn(_t("Image"), _t("Could not display the selected image."));
                });
            }
        },
        on_image_clicked: function() {
             var self = this;
             if (self.recordData.barcode) {
                 $.ajax({
                    url : 'https://imageserver.partenics.de/odoo/' + self.recordData.barcode + '?format=json',
                    type: 'get',
                    data : {},
                    contentType: false,
                    cache: false,
                    processData:false
                    }).done(function (data) {
                    var res = JSON.parse(data);
                    var image_arr = res["images"];
                    var img_urls = []
                    for (var i=0; i<res["count"]; i++) {
                      img_urls[i] = image_arr[i]["previewUrl"]
                    }
                    if (img_urls.length == 0) {
                        img_urls[0] = "/web/image?model=product.template&id="+self.recordData.id+"&field=image_128"
                    }
                    if (img_urls.length > 0) {
                        var dialog = new Dialog(self, {
                            title: self.recordData.name,
                            size: 'large',
                            $content: core.qweb.render('iframe_image_360', {'image_server': img_urls}),
                        }).open();
                    } else {
                        self.do_warn(_t('No images found!'));
                    }
                });
            } else {
                self.do_warn(_t('No barcode found!'));
            }
        }
    });


    field_registry.add('preview_binary_360', FieldPreviewBinary360);

    return FieldPreviewBinary360;

});