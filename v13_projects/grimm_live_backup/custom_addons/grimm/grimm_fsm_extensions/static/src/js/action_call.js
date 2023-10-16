odoo.define("task.action_button", function (require) {
"use strict";
var core = require('web.core');
var KanbanController = require('web.KanbanController');
var rpc = require('web.rpc');
var Context = require('web.Context');
var session = require('web.session');
var _t = core._t;
var MapRenderer = require('web_map.MapRenderer');
var Message = require('mail.model.Message');
var MailManager = require('mail.Manager');
var tech_marker = [];
var refreshIntervalId = null;

MailManager.include({
    markMessagesAsRead: function (messageIDs) {
        this._super.apply(this, arguments);
        var self = this;
        var ids = _.filter(messageIDs, function (id) {
            var message = self.getMessage(id);
            // If too many messages, not all are fetched,
            // and some might not be found
            return !message || message.isChannelMessage();
        });
        if (ids.length) {
            this._rpc({
                model: 'mail.message',
                method: 'set_channel_message_done',
                args: [ids],
            });
            window.location.reload();
        } else {
            return Promise.resolve();
        }

    },
});



Message.include({
    init: function (parent, data, emojis) {
            this._super.apply(this, arguments);
            this._need_to_display = data.need_to_display;
        },
    isChannelMessage: function () {
        var channel_id = this._threadIDs[0]
        if(typeof channel_id == "number"){
            return true
        }
        return false;
    },
    need_to_display: function () {
        return this._need_to_display;
    },
});

MapRenderer.include({
    init: function (parent, state, params) {
            this._super.apply(this, arguments);
            this.model_name = params.hasFormView.fieldsView.model
        },
    _reload_marker:function (){
       var self = this;
        tech_marker.forEach(function (marker){
            rpc.query({
                model: 'fleet.vehicle',
                method: 'get_car_latlong',
                args: [marker.bornemann_id],
                }).then(function (datas) {
                datas.forEach(function (data){
                    marker.marker.setLatLng([data.latitude, data.longitude]).update();
                })
            });
        })
    },
    destroy: function () {
        window.clearInterval(refreshIntervalId);
        return this._super.apply(this, arguments);
    },
    _add_custom_marker: function (){
        var self = this;
        tech_marker = [];
        this._rpc({
            model: 'fleet.vehicle',
            method: 'get_car_latlong',
            args: [],
        }).then(function (datas) {
            datas.forEach(function (data){
                var LeafIcon = L.Icon.extend({
                    options: {
                       iconSize:     [30, 60],
                       shadowSize:   [50, 64],
                       iconAnchor:   [22, 94],
                       shadowAnchor: [4, 62],
                       popupAnchor:  [-3, -76]
                    }
                });
                var grimmIcon = new LeafIcon({
                    iconUrl: '/grimm_fsm_extensions/static/src/img/grimm_car.png',
                })
                var marker = L.marker([data.latitude,data.longitude], {icon: grimmIcon});
                var driver_name = _t("Driver Name")
                var car_name = _t("Car")

                var popup_str = "<center><img src=\"data:image/png;base64, "+data.car_image+"\" alt=\"Grimm Car\" /></center>" +
                    "<strong>"+driver_name+" : </strong>"+data.driver_name+"<br/><br/>" +
                    "<strong>"+car_name+" : </strong>"+data.car_name+"<br/><br/>" +
                    "<a class=\"btn btn-primary\" style=\"color:white\" href=\"https://www.google.com/maps/dir/?api=1&amp;destination="+data.latitude+","+data.longitude+"\" target=\"_blank\">navigate to</a>";
                marker.addTo(self.leafletMap).bindPopup(popup_str);
                self.markers.push(marker);
                tech_marker.push({'bornemann_id':data.bornemann_id, 'marker':marker})
            })
            refreshIntervalId = window.setInterval(self._reload_marker,5000)
        });
    },
    /**
     * If there's located records, adds the corresponding marker on the map
     * Binds events to the created markers
     * @private
     * @param {Array} records array that contains the records that needs to be displayed on the map
     * @param {Object} records.partner is the partner linked to the record
     * @param {float} records.partner.partner_latitude latitude of the partner and thus of the record
     * @param {float} records.partner.partner_longitude longitude of the partner and thus of the record
     */
    _addMakers: function (records) {
        var self = this;
        this._super.apply(this, arguments);
        if(this.model_name == "project.task") {
            this._add_custom_marker()
        }
    },
});
KanbanController.include({
    renderButtons: function($node) {
        this._super.apply(this, arguments);
        if (this.$buttons) {
         this.$buttons.find(".oe_action_button").click(this.proxy('action_def')) ;
       }
    },
    action_def: function () {
        var self =this
        var user = session.uid;
        rpc.query({
            model: "project.task",
            method: 'get_backto_link',
            args: [[],window.location],
            }).then(function (e) {
                // self.do_action({
                //     type: 'ir.actions.act_url',
                //     url: e,
                //     target: 'self',
                // });
                self.do_action({
                    name: _t('action_invoices'),
                    type: 'ir.actions.act_window',
                    res_model: "project.task",
                    res_id: e["res_id"],
                    views: [[e["view_id"], 'form']],
                    view_mode: 'form',
                    target: 'self',
                });
                window.location
            });
    },
    });
});