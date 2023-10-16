odoo.define('web_editor.summernote_override', function (require) {
'use strict';

var core = require('web.core');
var list = require('summernote/core/list');
var EventHandler = require('summernote/EventHandler');
var Renderer = require('summernote/Renderer');
var renderer = new Renderer();
var eventHandler = new EventHandler();
var session = require('web.session');

require('summernote/summernote'); // wait that summernote is loaded
var _t = core._t;


// disable some editor features
// XXX: this is not working, unfortunately but `options.styleTags` above is. weird :S
$.fn.extend({
    /**
     * @method
     * Initialize summernote
     *  - create editor layout and attach Mouse and keyboard events.
     *
     * ```
     * $("#summernote").summernote( { options ..} );
     * ```
     *
     * @member $.fn
     * @param {Object|String} options reference to $.summernote.options
     * @return {this}
     */
    summernote: function () {
      // check first argument's type
      //  - {String}: External API call {{module}}.{{method}}
      //  - {Object}: init options
      var type = $.type(list.head(arguments));
      var isExternalAPICalled = type === 'string';
      var hasInitOptions = type === 'object';

      // extend default options with custom user options

      var options = hasInitOptions ? list.head(arguments) : {};

      options = $.extend({}, $.summernote.options, options);

        //GRIMM START
        options.toolbar = [
            ["style",["style"]],
            ["font",["bold","italic","underline","clear"]],
            ["fontsize",["fontsize"]],
            ["color",["color"]],
            ["para",["ul","ol","paragraph"]],
            ["table",["table"]],
            ["insert",["link","picture"]],
            ["history",["undo","redo"]],
            ["view",["codeview"]]
        ]

        options.styleTags =["p","pre","small","h1","h2","h3","h4","h5","h6","blockquote"]
        if (session.uid > 2){
            options.styleTags =["p",/*"pre","small",*/"h1","h2","h3"]
            options.toolbar = [
            ["style",["style"]],
            ["font",["bold",/*"italic","underline",*/"clear"]],
            //["fontsize",["fontsize"]],
            //["color",["color"]],
            ["para",["ul"/*,"ol","paragraph"*/]],
            //["table",["table"]],
            ["insert",["link","picture"]],
            ["history",["undo","redo"]],
            ["view",["codeview"]]
        ]
        }

        //GRIMM END
      options.icons = $.extend({}, $.summernote.options.icons, options.icons);

      // Include langInfo in options for later use, e.g. for image drag-n-drop
      // Setup language info with en-US as default
      options.langInfo = $.extend(true, {}, $.summernote.lang['en-US'], $.summernote.lang[options.lang]);

      // override plugin options
      if (!isExternalAPICalled && hasInitOptions) {
        for (var i = 0, len = $.summernote.plugins.length; i < len; i++) {
          var plugin = $.summernote.plugins[i];

          if (options.plugin[plugin.name]) {
            $.summernote.plugins[i] = $.extend(true, plugin, options.plugin[plugin.name]);
          }
        }
      }

      this.each(function (idx, holder) {
        var $holder = $(holder);

        // if layout isn't created yet, createLayout and attach events
        if (!renderer.hasNoteEditor($holder)) {

          renderer.createLayout($holder, options);

          var layoutInfo = renderer.layoutInfoFromHolder($holder);
          $holder.data('layoutInfo', layoutInfo);

          eventHandler.attach(layoutInfo, options);
          eventHandler.attachCustomEvent(layoutInfo, options);
        }
      });

      var $first = this.first();
      if ($first.length) {
        var layoutInfo = renderer.layoutInfoFromHolder($first);

        // external API
        if (isExternalAPICalled) {
          var moduleAndMethod = list.head(list.from(arguments));
          var args = list.tail(list.from(arguments));

          // TODO now external API only works for editor
          var params = [moduleAndMethod, layoutInfo.editable()].concat(args);
          return eventHandler.invoke.apply(eventHandler, params);
        } else if (options.focus) {
          // focus on first editable element for initialize editor
          layoutInfo.editable().focus();
        }
      }

      return this;
    },
  });

return $.summernote;

});