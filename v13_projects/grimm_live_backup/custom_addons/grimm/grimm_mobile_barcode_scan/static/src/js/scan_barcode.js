odoo.define('grimm_mobile_barcode_scan.MobileMainMenu', function (require) {
"use strict";

//var $ = require('jquery');
var core = require('web.core');
var AbstractAction = require('web.AbstractAction');
var Dialog = require('web.Dialog');
var Session = require('web.session');
var mobile = require('web_mobile.rpc');
//var NotificationManager = require('web.notification').NotificationManager;
//var sign = require('grimm_mobile_barcode_scan.')

var _t = core._t;

//$('.o_mobile_barcode_main_menu h1, .o_mobile_barcode_main_menu table, .o_mobile_barcode_main_menu .button_product').hide();

var MobileMainMenu = AbstractAction.extend({
    template: 'mobile_main_menu',

    events: {
        "click .button_scan_so": function(){
//            this.$el.find('.button_scan_so').hide();
//            this.$el.find('.button_finish, h1, h3, .button_product, .button_info, .table-product').show();
            this.open_mobile_scanner('service');
        },
        "click .button_product": function(){
            this.open_mobile_scanner('product');
        },
        "click .button_finish": function(){
            this.close_window('product');
        },
        "click a[id^='#del']": function(e){
            this.delete_product($(e.currentTarget).attr('title'));
        },
        "click a[id^='#inc']": function(e){
            this.increase_prod_qty($(e.currentTarget).attr('title'));
        },
        "click a[id^='#dec']": function(e){
            this.decrease_prod_qty($(e.currentTarget).attr('title'));
        },
        "click .serv_row td a": function(e){
            var $arg = $(e.currentTarget);
            var service_barcode = $arg.attr('title');
            var state = $arg.attr('data-id');
            this.change_state(service_barcode, state);
        },
        "click .serv_row td:first-child, .serv_row td:nth-child(2)": function(e){
            var barcode = $(e.currentTarget.parentNode).attr('title');
            console.log('Barcode: ' + barcode);
            this._onBarcodeScanned('', barcode, 'service');
            var other_material_val = this.$el.find('#other_material');
            other_material_val.val('');
            var $st_ap_1 = this.$el.find('#st_ap_1');
            $st_ap_1.click();
        },
        "click .button_info": function(){
            this.open_dialog();
        },
        "change #beleg_info": function(e){
            e.stopImmediatePropagation();
            var $h1 = this.$el.find('h1');
            var serv_code = $h1.text().split(' ')[1];
            var $serv_hdn = this.$el.find('#serv_code_hidden');
            $serv_hdn.val(serv_code);
            console.log('Service: ' + serv_code);
            var $upload_btn = this.$el.find('#file_upload_btn');
            $upload_btn.click();
//            this.beleg_fotografieren();
        },
        "click .button_sign": function(){
            this.open_sign_pad();
        },
        "click .btn-canvas-clear": function(){
            $('.js-signature').jqSignature('clearCanvas');
        },
        "click .btn-canvas-submit": function(){
            var self = this;
            var $h1 = this.$el.find('h1');
            var serv_code = $h1.text().split(' ')[1];
            var sigURL = $('.js-signature').jqSignature('getDataURL');
            Session.rpc('/mobile_barcode/upload_signature', {
            data: sigURL.split(':')[1] + '|' + serv_code,
            }).then(function(result) {
                if(result.info){
                    self.do_notify(_t("Success"), result.notify);
                } else {
                    self.do_warn(result.warning);
                }
            });
        },
//        "focusout #other_material": function(){
//            var self = this;
//            var $h1 = this.$el.find('h1');
//            var serv_code = $h1.text().split(' ')[1];
//            var other_material_val = this.$el.find('#other_material').val();
//            Session.rpc('/mobile_barcode/other_material', {
//            data: other_material_val + '|' + serv_code,
//            }).then(function(result) {
//                if(result.info){
////                    self.do_notify(_t("Success"), result.notify);
//                } else {
//                    self.do_warn(result.warning);
//                }
//            });
//        },

        "click .st_checkboxes": function(e){
//            console.log(e.currentTarget.id + ', ' + $('#' + e.currentTarget.id).is(':checked'));
            var self = this;
            var $h1 = this.$el.find('h1');
            var serv_code = $h1.text().split(' ')[1];
            Session.rpc('/mobile_barcode/st_checkboxes', {
            data: e.currentTarget.id + '|' + $('#' + e.currentTarget.id).is(':checked') + '|' + serv_code,
            }).then(function(result) {
                if(result.info){
                } else {
                    self.do_warn(result.warning);
                }
            });
        },

//        "change #datepicker": function(e) {
//            var self = this;
//            var $h1 = this.$el.find('h1');
//            var serv_code = $h1.text().split(' ')[1];
//            var datepicker = this.$el.find('#datepicker').val();
//            Session.rpc('/mobile_barcode/datepicker', {
//            data: datepicker + '|' + serv_code,
//            }).then(function(result) {
//                if(result.info){
//                } else {
//                    self.do_warn(result.warning);
//                }
//            });
//        },
//
//        "change #duration": function() {
//            var self = this;
//            var $h1 = this.$el.find('h1');
//            var serv_code = $h1.text().split(' ')[1];
//            var duration = this.$el.find('#duration').val();
//            Session.rpc('/mobile_barcode/duration', {
//            data: duration + '|' + serv_code,
//            }).then(function(result) {
//                if(result.info){
//                } else {
//                    self.do_warn(result.warning);
//                }
//            });
//        },

         "click #tabs-block ul li": function(e){
            var $target = $(e.currentTarget);
//            $target.siblings().removeClass('active');
//            $target.addClass('active');
            this.load_tickets($target.text());
//            console.log($target.text());
        },

        "click .button_timesheet": function(){
            var self = this;
            var $h1 = this.$el.find('h1');
            var serv_code = $h1.text().split(' ')[1];
            var other_material_val = this.$el.find('#other_material').val();
            var datepicker = this.$el.find('#datepicker').val();
            var duration = this.$el.find('#duration').val();
            var $ap_1 = this.$el.find('#st_ap_1');
            var $ap_2 = this.$el.find('#st_ap_2');
            var $no_cost = this.$el.find('#st_anfahrt');
            var travel_cost = '';
            travel_cost = $("input[name='travel_cost']:checked").val();
//            if ($ap_1.is(':checked') == true){
//                travel_cost = $ap_1.text();
//            } else if ($ap_2.is(':checked') == true){
//                travel_cost = $ap_2.text();
//            } else if ($no_cost.is(':checked') == true) {
//                travel_cost = $no_cost.text();
//            }
            var user_id = this.$el.find('#staffs_sel').val();
            console.log(serv_code + '|' + other_material_val + '|' + datepicker + '|' + duration + '|' + travel_cost + '|' + user_id);
            Session.rpc('/mobile_barcode/create_timesheet', {
                data: serv_code + '|' + other_material_val + '|' + datepicker + '|' + duration + '|' + travel_cost + '|' + user_id,
            }).then(function(result) {
                if(result.info){
                    self.do_notify(_t("Success"), result.notify);
                    self.load_timesheet_res(serv_code);
                } else {
                    self.do_warn(result.warning);
                }
            });
        },
    },

    init: function(parent, action) {
        // Yet, "_super" must be present in a function for the class mechanism to replace it with the actual parent method.
        this._super.apply(this, arguments);
    },

    start: function() {
        if(!mobile.methods.scanBarcode){
            this.$el.find(".button_scan_so, .button_product").remove();
            $("<span class='button_scan_so btn btn-primary btn-sm disable_click'>Serviceauftrag scannen</span><span class='button_product btn btn-primary btn-sm disable_click'>Produktbarcode scannen</span>").insertBefore(this.$el.find("img"));
        }
//        $("#datepicker").datepicker();
        this.$calendar = this.$("#datepicker");
        this.$calendar.datepicker().datepicker("setDate", new Date());
        this.$el.find('.button_finish, h1, h3, .button_product, .button_info, .table-product, .radio, .form-group, .beleg, .button_sign, .table-checkboxes, .table-action-checks, .table-timesheet-res').hide();
        this.load_tickets('Neu');
        var self = this;
        core.bus.on('barcode_scanned', this, this._onBarcodeScannedDevice);

        var $upload_btn = this.$el.find('#file_upload_btn');
        $upload_btn.click(function() {
            var $file = self.$el.find('#beleg_info');
            var $form = self.$el.find("#file_upload_form");
            $form.submit(function(event){
                console.log(event);
                // console.log($file.val());
                event.preventDefault(); //prevent default action
                if ($file.val()) {
                    var post_url = $(this).attr("action"); //get form action url
                    var request_method = $(this).attr("method"); //get form GET/POST method
                    var form_data = new FormData(this); //Creates new FormData object
                    $.ajax({
                        url : post_url,
                        type: request_method,
                        data : form_data,
                        contentType: false,
                        cache: false,
                        processData:false
                    }).then(function(response){
                        $file.unbind();
                        $form.unbind();
                        self.do_notify(_t("Success"), _t('Attachment created successfully'));
                    });
                }
            });
        });
        return this._super();
    },

    destroy: function () {
        core.bus.off('barcode_scanned', this, this._onBarcodeScannedDevice);
        this._super();
    },

    _onBarcodeScannedDevice: function(barcode) {
        var $h1 = this.$el.find('h1');
        if ($h1.text() == "") {
            console.log('Barcode: ' + barcode);
            this.$el.find('.button_scan_so, #tabs-block').hide();
            this.$el.find('.button_finish, h1, h3, .button_product, .button_info, .table-product, .radio, .form-group, .beleg, .button_sign, .table-checkboxes, .table-action-checks, .table-timesheet-res').show();
            this._onBarcodeScanned('', barcode, 'service');
        } else {
            this._onBarcodeScanned(barcode, $h1.text().split(' ')[1], 'product');
        }
    },

    load_products: function(arr){
        var $table = this.$el.find('.table-product');
        $table.find('tbody').empty();
        for (var i=0; i<arr.length;i++) {
            $table.find('tbody').append('<tr><td><a id="#inc" title="' + arr[i].barcode + '"><i class="fa fa-plus mr-1"></i></a></td><td><a id="#dec" title="' + arr[i].barcode + '"><i class="fa fa-minus"></i></a></td><td>' + arr[i].barcode + '</td><td class="zero-padding desc-width">' + arr[i].name + '</td><td>' + arr[i].qty + '</td><td><a id="#del" title="' + arr[i].barcode + '"><i class="fa fa-trash"></i></a></td></tr>');
        }
    },

    _onBarcodeScanned: function(barcode, serv_code, model) {
//        this.notification_manager = new NotificationManager(this);
        this.$el.find('h1').text('Serviceauftrag: ' + serv_code);
        var $h3 = this.$el.find('h3');
        var self = this;
        if (!$.contains(document, this.el)) {
            return;
        }

        Session.rpc('/mobile_barcode/mobile_main_menu', {
            data: barcode + "|" + model + "|" + serv_code,
        }).then(function(result) {
            if (result.service) {
                $h3.text(result.service.service);
                self.ui_startup();
                self.load_products(result.service.product);
                self.load_users();
                self.load_timesheet_res(serv_code);
            } else if (result.product){
                self.load_products(result.product);
            } else if (result.action){
                self.do_action(result.action)
            } else {
                self.do_warn(result.warning);
                if (model == 'service') {
                    self.close_window();
                }
            }

        });
        Session.rpc('/mobile_barcode/get_service_info', {
            service: serv_code,
        }).then(function(result) {
            if (result.service) {
                self.load_travel(result.service)
            }
        });
    },

    open_mobile_scanner: function(model){
        var self = this;
        var $h1 = this.$el.find('h1');
        mobile.methods.scanBarcode().then(function(response){
            var data = response.data;
            var serv_code = $h1.text().split(' ')[1];
            var barcode = '';
            if (model == 'product') {
                barcode = data;
            } else {
                serv_code = data;
            }
            if(barcode || serv_code){
                self._onBarcodeScanned(barcode, serv_code, model);
                mobile.methods.vibrate({'duration': 100});
            }else{
                mobile.methods.showToast({'message':'Please, Scan again !!'});
                console.log('Bitte scannen Sie nochmal!')
            }
        });
    },
    close_window: function(){
        var $h1 = this.$el.find('h1');
        $h1.empty();
        this.$el.find('.button_scan_so, #tabs-block').show();
        this.$el.find('.button_finish, h1, h3, .button_product, .button_info, .table-product, .radio, .form-group, .beleg, .button_sign, .table-checkboxes, .table-action-checks, .table-timesheet-res').hide();
    },

    ui_startup: function(){
        this.$el.find('.button_scan_so, #tabs-block').hide();
        this.$el.find('.button_finish, h1, h3, .button_product, .button_info, .table-product, .radio, .form-group, .beleg, .button_sign, .table-checkboxes, .table-action-checks, .table-timesheet-res').show();
    },

    delete_product: function(product){
        var $h1 = this.$el.find('h1');
        var self = this;
        Session.rpc('/mobile_barcode/delete_product', {
            data: product + "|" + $h1.text().split(' ')[1],
        }).then(function(result) {
            self.load_products(result.product);
        });
    },

    increase_prod_qty: function(product){
        var $h1 = this.$el.find('h1');
        var self = this;
        Session.rpc('/mobile_barcode/increase_prod_qty', {
            data: product + "|" + $h1.text().split(' ')[1],
        }).then(function(result) {
            self.load_products(result.product);
        });
    },

    decrease_prod_qty: function(product){
        var $h1 = this.$el.find('h1');
        var self = this;
        Session.rpc('/mobile_barcode/decrease_prod_qty', {
            data: product + "|" + $h1.text().split(' ')[1],
        }).then(function(result) {
            self.load_products(result.product);
        });
    },

    open_dialog: function(){
        var $h1 = this.$el.find('h1');
        var serv_code = $h1.text().split(' ')[1];
        var self = this;
        var $table1 = this.$el.find('.table-company');
        $table1.find('tbody').empty();
        var $table2 = this.$el.find('.table-contact');
        $table2.find('tbody').empty();
        var $map = this.$el.find('#gmaps');
        $map.remove();
        Session.rpc('/mobile_barcode/get_customer_info', {
            service: serv_code,
        }).then(function(result) {
           if (result.info) {
                $table1.find('tbody').append('<tr><td>' + _t('Name') + '</td><td>' + result.info.name + '</td></tr><tr><td>' + _t('Address') + '</td><td>' + result.info.street + '</td></tr><tr><td>' + _t('PLZ') + '</td><td>' + result.info.zip + '</td></tr><tr><td>' + _t('Phone') + '</td><td><a href="tel:' + result.info.phone + '">' + result.info.phone + '</a></td></tr><tr><td>' + _t('Mobile') + '</td><td><a href="tel:' + result.info.mobile + '">' + result.info.mobile + '</a></td></tr>');
                $table2.find('tbody').append('<tr><td>' + _t('Name') + '</td><td>' + result.info.contact + '</td></tr><tr><td>' + _t('Phone') + '</td><td>' + result.info.cphone + '</td></tr>');
                $('<a class="btn btn-primary btn-lg" id="gmaps" href="https://www.google.com/maps/search/?api=1&query=' + result.info.address + '" target="_blank"><span class="glyphicon glyphicon-map-marker"></span> Google Maps</a>').insertAfter($table2);
            }
        });

        $('#o_info_popup').modal('show');
    },
    open_sign_pad: function(){
        $('.js-signature').jqSignature('clearCanvas');
        $('.js-signature').jqSignature({height: 500});
        $('#canvas_sign_pad_popup').modal('show');
    },

    load_travel: function(dict_trvl){
        console.log(dict_trvl);
//        var $st_ap_1 = this.$el.find('#st_ap_1');
//        var $st_ap_2 = this.$el.find('#st_ap_2');
//        var $st_anfahrt = this.$el.find('#st_anfahrt');
        var $st_small_pieces = this.$el.find('#st_small_pieces');
        var $st_meters_pack = this.$el.find('#st_meters_pack');
        var $st_clean_and_care = this.$el.find('#st_clean_and_care');
//        var $other_material = this.$el.find('#other_material');
        var $duration = this.$el.find('#duration');
//        var $date = this.$el.find('#datepicker');
//        $st_ap_1.prop('checked', JSON.parse(dict_trvl.st_ap_1));
//        $st_ap_2.prop('checked', JSON.parse(dict_trvl.st_ap_2));
//        $st_anfahrt.prop('checked', JSON.parse(dict_trvl.st_anfahrt));
        $st_small_pieces.prop('checked', JSON.parse(dict_trvl.st_small_pieces));
        $st_meters_pack.prop('checked', JSON.parse(dict_trvl.st_meters_pack));
        $st_clean_and_care.prop('checked', JSON.parse(dict_trvl.st_clean_and_care));
//        $other_material.val(dict_trvl.other_material);
//        $date.val(dict_trvl.date);
        $duration.val(dict_trvl.duration);
    },
    load_tickets: function(state){
        var $table = this.$el.find('.table-ticket');
        $table.find('tbody').empty();
        Session.rpc('/mobile_barcode/get_service_ticket', {
            state: state,
        }).then(function(result) {
           if (result.ticket) {
//                console.log(result.ticket);
                var arr_ticket = result.ticket;
                for (var i=0; i<arr_ticket.length;i++) {
                    var dict_ticket = arr_ticket[i];
                    var converted_arr = Object.values(dict_ticket);
                    var icon_1 = '';
                    var icon_2 = '';
                    if (state == 'Neu') {
                        icon_1 = '<a title="' + converted_arr[2] + '" data-id="23"><i class="fa fa-briefcase"></i></a>';
                    } else if (state == 'Ersatzteile Bestellt') {
                        icon_1 = '<a title="' + converted_arr[2] + '" data-id="22"><i class="fa fa-font"></i></a>';
                    } else {
                        icon_1 = '<a title="' + converted_arr[2] + '" data-id="19" class="btn-lg"><i class="fa fa-check-circle"></i></a>';
                        icon_2 = '<a title="' + converted_arr[2] + '" data-id="23" class="btn-lg"><i class="fa fa-times-circle"></i></a>';
                    }
                    $table.find('tbody').append('<tr class="serv_row" title="' + converted_arr[2] + '"><td>' + converted_arr[1] + '</td><td class="grimm_td_left">' + converted_arr[0] + '</td><td>' + icon_1 + '</a>' + icon_2 + '</td></tr>');
                }
           }
        });
    },

    load_users: function(){
        var $select = this.$el.find('#staffs_sel');
        $select.empty();
        Session.rpc('/mobile_barcode/get_service_users',).then(function(result) {
           if (result.users) {
            var arr_usrs = result.users;

            for (var i=0; i<arr_usrs.length;i++) {
                $select.append(arr_usrs[i])
            }
           }
        });
    },

    load_timesheet_res: function(service){
        var $timesheet_tbl = this.$el.find('.table-timesheet-res');
        $timesheet_tbl.find('tbody').empty();
        Session.rpc('/mobile_barcode/get_timesheets', {
            service: service,
        }).then(function(result) {
           if (result.timesheets) {
            console.log(result.timesheets)
            var arr_timsheets = result.timesheets;

            for (var i=0; i<arr_timsheets.length;i++) {
                $timesheet_tbl.find('tbody').append(arr_timsheets[i])
            }
           }
        });
    },

    change_state: function(service, state) {
        var self = this;
        var $ct_state = this.$el.find('#tabs-block li a.active');
        var old_state = $ct_state.text();
        Session.rpc('/mobile_barcode/change_ticket_state', {
            data: service + '|' + state,
        }).then(function(result) {
            if (result.notify) {
                self.do_notify(_t("Success"), result.notify);
                self.load_tickets(old_state);
            } else {
                self.do_warn(result.warning);
            }
         });
    },
});

core.action_registry.add('mobile_barcode_main_menu', MobileMainMenu);

return {
    MobileMainMenu: MobileMainMenu,
};

});
