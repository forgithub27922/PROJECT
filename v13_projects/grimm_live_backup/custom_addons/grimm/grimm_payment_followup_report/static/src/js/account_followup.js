odoo.define('grimm_payment_followup_report.account_report_followup_inherit', function (require) {
'use strict';

    var core = require('web.core');
    var Pager = require('web.Pager');
    var datepicker = require('web.datepicker');
    var Dialog = require('web.Dialog');
    var FollowupFormRenderer = require('account_followup.FollowupFormRenderer');
    var _t = core._t;

    var QWeb = core.qweb;
    var BasicModel = require('web.BasicModel');

    BasicModel.include({
        _applyX2OneChange: function (record, fieldName, data) {
            var self = this;
            if (!data || !data.id) {
                record._changes[fieldName] = false;
                return Promise.resolve();
            }

            // here, we check that the many2one really changed. If the res_id is the
            // same, we do not need to do any extra work. It can happen when the
            // user edited a manyone (with the small form view button) with an
            // onchange.  In that case, the onchange is triggered, but the actual
            // value did not change.
            var relatedID;
            if (record._changes && fieldName in record._changes) {
                relatedID = record._changes[fieldName];
            } else {
                relatedID = record.data[fieldName];
            }
            var relatedRecord = this.localData[relatedID];
            if (relatedRecord && (data.id === this.localData[relatedID].res_id)) {
                return Promise.resolve();
            }
            var rel_data = _.pick(data, 'id', 'display_name');
            var field = record.fields[fieldName];

            // the reference field doesn't store its co-model in its field metadata
            // but directly in the data (as the co-model isn't fixed)
            var coModel = field.type === 'reference' ? data.model : field.relation;
            var def;
            if (rel_data.display_name === undefined) {
                // TODO: refactor this to use _fetchNameGet
                def = this._rpc({
                        model: coModel,
                        method: 'name_get',
                        args: [data.id],
                        context: record.context,
                    })
                    .then(function (result) {
                        rel_data.display_name = result[0][1];
                    });
            }
            // GRIMM_START
            if (fieldName == "grimm_followup_level_id" && confirm(_t("Do you wanted to send an email to customer regarding payment reminder?"))){
               //if click yes do this
                record.context["send_mail_to_customer"] = true
            }else{
                record.context["send_mail_to_customer"] = false
            }
            // GRIMM_END
            return Promise.resolve(def).then(function () {
                var rec = self._makeDataPoint({
                    context: record.context,
                    data: rel_data,
                    fields: {},
                    fieldsInfo: {},
                    modelName: coModel,
                    parentID: record.id,
                });
                record._changes[fieldName] = rec.id;
            });

        },
    });

});
