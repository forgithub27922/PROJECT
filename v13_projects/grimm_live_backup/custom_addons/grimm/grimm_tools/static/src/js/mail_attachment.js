odoo.define('grimm_tools.mail_attachment_inherit', function (require) {
'use strict';

    var core = require('web.core');
    var Pager = require('web.Pager');
    var datepicker = require('web.datepicker');
    var Dialog = require('web.Dialog');
    //var field_attachment = require('web.many2many_binary');
    var relational_fields = require('web.relational_fields');
    var form_controller = require('web.FormController')
    var _t = core._t;

    var qweb = core.qweb;

    /*
    Form controller inherited to override sorting of line_no_manual field on sale order line.
    line_no_manual is alphanumeric field and during sorting (when user click on column header)
    it return wrong sorting.
    So using java script we forcefully passed line_no_seq field for sorting instead of line_no_manual.
    */
    form_controller.include({
        _onToggleColumnOrder: function (ev) {

            ev.stopPropagation();
            var self = this;
            var field_name = ev.data.name;
            /*Grimm START*/
            if (field_name == "line_no_manual" && ev.data.id.search("sale.order.line_") >= 0){
                field_name = "line_no_seq"
            }
            /*Grimm END*/
            this.model.setSort(ev.data.id, field_name).then(function () {
                var field = ev.data.field;
                var state = self.model.get(self.handle);
                self.renderer.confirmChange(state, state.id, [field]);
            });
        },
    })


    relational_fields.FieldMany2ManyBinaryMultiFiles.include({
        events: {
            'click .o_attach': '_onAttach',
            'click .o_attachment_delete': '_onDelete',
            'change .o_input_file': '_onFileChanged',
        },
        fieldsToFetch: {
            name: {type: 'char'},
            mimetype: {type: 'char'},
            file_size: {type: 'int'},
        },
        reload_size: function (remove_id) {
            var remove = remove_id
            var attachment_ids = this.value.res_ids;
            this._rpc({
                model: 'ir.attachment',
                method: 'get_file_size',
                args: [attachment_ids,remove],
            })
            .then(function (result) { // send the email server side
                $( "#attachment_size" ).html(result)
            });
        },
        _onDelete: function (ev) {
            ev.preventDefault();
            ev.stopPropagation();

            var fileID = $(ev.currentTarget).data('id');
            var record = _.findWhere(this.value.data, {res_id: fileID});
            if (record) {
                this._setValue({
                    operation: 'FORGET',
                    ids: [record.id],
                });
                var metadata = this.metadata[record.id];
                if (!metadata || metadata.allowUnlink) {
                    this._rpc({
                        model: 'ir.attachment',
                        method: 'unlink',
                        args: [record.res_id],
                    });
                }
            }
            this.reload_size(record.res_id)
        },
        _onFileLoaded: function () {
            var self = this;
            // the first argument isn't a file but the jQuery.Event
            var files = Array.prototype.slice.call(arguments, 1);
            // files has been uploaded, clear uploading
            this.uploadingFiles = [];

            var attachment_ids = this.value.res_ids;
            _.each(files, function (file) {
                if (file.error) {
                    self.do_warn(_t('Uploading Error'), file.error);
                } else {
                    attachment_ids.push(file.id);
                    self.uploadedFiles[file.id] = true;
                }
            });

            this._setValue({
                operation: 'REPLACE_WITH',
                ids: attachment_ids,
            });
            this.reload_size(0)
        }
    });
});
