odoo.define('sky_hr_attendance_custom.ImportAttendanceView', function (require) {
"use strict";

var ImportAttendanceController = require('sky_hr_attendance_custom.ImportAttendanceController');
var ListView = require('web.ListView');
var viewRegistry = require('web.view_registry');

var ImportAttendanceView = ListView.extend({
    config: _.extend({}, ListView.prototype.config, {
        Controller: ImportAttendanceController
    })
});

viewRegistry.add('import_attendance_view', ImportAttendanceView);

});
