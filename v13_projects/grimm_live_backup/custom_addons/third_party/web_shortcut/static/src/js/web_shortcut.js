/* Copyright 2004-today Odoo SA (<http://www.odoo.com>)
 * License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl). */

odoo.define('web.shortcut', function(require) {
    var Widget = require('web.Widget'),
        UserMenu = require('web.UserMenu'),
        core = require('web.core'),
        qweb = core.qweb,
        session = require('web.session');
    var SystrayMenu = require('web.SystrayMenu');
    var rpc = require('web.rpc');
    var ControlPanelRenderer = require('web.ControlPanelRenderer');
    var FormController = require("web.FormController");

    FormController.include({
        on_attach_callback: function() {
            var self = this;
            var res = this._super.apply(this, arguments);
            try {
                var $shortcut = self._controlPanel.$el.find('.bookmark_shortcut');
                $shortcut.addClass('d-none');
            } catch (e) {
                return res;
            }
            return res;
        },
    });

    var ShortcutMenu = Widget.extend({
        template: 'Systray.ShortcutMenu',

        init: function() {
            this._super();
            this.on('load', this, this.load);
            this.on('add', this, this.add);
            this.on('display', this, this.display);
            this.on('remove', this, this.remove);
            this.model = 'web.shortcut';
        },
        start: function() {
            var self = this;
            this._super();
            this.trigger('load');
        },
        load: function() {
            var self = this;
            this.$el.find('.oe_systray_shortcut_menu').empty();
            var domain = window.location.href.toString().split('#');
            return rpc.query({
                model: 'web.shortcut',
                method: 'get_user_shortcuts',
                args: [domain[0]]
            }).then(function(shortcuts) {
                _.each(shortcuts, function(sc) {
                    self.trigger('display', sc);
                });
            });
        },
        add: function (sc) {
            var self = this;
            rpc.query({
                model: 'web.shortcut',
                method: 'create',
                args: [sc]
                }).then(function(out){
                location.reload();
            });
        },
        display: function(sc) {
            var self = this;
            this.$el.find('.oe_systray_shortcut_menu').append();
            var $sc = $(qweb.render('Systray.ShortcutMenu.Item', {'shortcut': sc}));
            $sc.appendTo(self.$el.find('.oe_systray_shortcut_menu'));
        },
        remove: function (action_id) {
            var self = this;
            rpc.query({
                model: 'web.shortcut',
                method: 'remove_shortcut',
                args: [action_id]
                }).then(function(out){
                location.reload();
            });
        },
        has: function(menu_id) {
            var self = this;
            var $shortcut_menu = $('.oe_systray_shortcut_menu');
            var noOfBookmarks = $('.oe_systray_shortcut_menu').children().length;

            for (var i=1; i<=noOfBookmarks; i++) {
                var dataId = $shortcut_menu.children('li:nth-child(' + i + ')').children().attr('data-id');
                if (dataId == menu_id) {
                    return true
                }
            }
            return false;
        }
    });

    UserMenu.include({
        start: function() {
            var res = this._super.apply(this, arguments);
            this.shortcuts = new ShortcutMenu(self);
            this.shortcuts.prependTo(this.$el.parent());
            return res;
        },
        do_update: function() {
            var self = this;
            this._super.apply(this, arguments);
            this.update_promise.done(function() {
                self.shortcuts.trigger('load');
            });
        },
    });

    ControlPanelRenderer.include({
        template: 'ControlPanel',
        start: function () {
            this._super.apply(this, arguments);
            this.load(this.action.id);
        },
        load: function(action) {
            var $divBookmarkShortcut = this.$el.find('.bookmark_shortcut');
            $divBookmarkShortcut.empty();
            var self = this;
            rpc.query({
                model: 'web.shortcut',
                method: 'check_if_bookmarked',
                args: [action]
            }).then(function(cl) {
                var $sc = $(qweb.render('ControlPanel.BookMark', {'bookmark': cl[0]}));
                $sc.appendTo($divBookmarkShortcut);
                var shortcuts_menu = new ShortcutMenu();
                var action_id = $sc.attr('data-id');
                $sc.click(function() {
                    var link = window.location.href.toString().split('#');
                    if ($sc.hasClass("oe_shortcut_remove")) {
                        shortcuts_menu.trigger('remove', action_id);
                    } else {
                        shortcuts_menu.trigger('add', {
                            'user_id': session.uid,
                            'action_id': action_id,
                            'name': session.name,
                            'link': link[1]
                        });
                    }
                    $sc.toggleClass("oe_shortcut_remove");
                });

            });
        },
    });

    SystrayMenu.Items.push(ShortcutMenu);
    return ShortcutMenu;
});
