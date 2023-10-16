odoo.define('grimm_web_editor.html_editor', function (require) {
    "use strict";

    require('summernote/summernote'); // wait that summernote is loaded
    var FieldHtml = require('web_editor.field.html');
    var Wysiwyg = require('web_editor.wysiwyg.root');
    var summernote = require('web_editor.summernote');;
    var dom = $.summernote.core.dom;
    var range = $.summernote.core.range;
    var options = $.summernote.options;
    var config = require('web.config');

    FieldHtml.include({

       /**
         * @override to make textarea bigger (OD-728)
         */
       _createWysiwygIntance: function () {
            var self = this;
            this.wysiwyg = new Wysiwyg(this, this._getWysiwygOptions());

            // by default this is synchronous because the assets are already loaded in willStart
            // but it can be async in the case of options such as iframe, snippets...
            return this.wysiwyg.attachTo(this.$target).then(function () {
                self.$content = self.wysiwyg.$editor.closest('body, odoo-wysiwyg-container');
                self._onLoadWysiwyg();
                self.isRendered = true;
                if (['product.template', 'product.product'].indexOf(self.model) >= 0) {
                    self.$content.find('.note-editable').css({"min-height": "360px"});
                }
            });
        },
        commitChanges: function () {
            var self = this;
            //if (config.isDebug() && this.mode === 'edit') { Removed debug mode condition so every time its commit.
            if (this.mode === 'edit') { // GRIMM START-END
                var layoutInfo = $.summernote.core.dom.makeLayoutInfo(this.wysiwyg.$editor);
                $.summernote.pluginEvents.codeview(undefined, undefined, layoutInfo, false);
            }
            if (this.mode == "readonly" || !this.isRendered) {
                return this._super();
            }
            var _super = this._super.bind(this);
            return this.wysiwyg.saveCroppedImages(this.$content).then(function () {
                return self.wysiwyg.save(self.nodeOptions).then(function (result) {
                    self._isDirty = result.isDirty;
                    _super();
                });
            });
        },
    });

    $.summernote.pluginEvents.enter = function (event, editor, layoutInfo) {
        var $editable = layoutInfo.editable();
        $editable.data('NoteHistory').recordUndo($editable, 'enter');

        var r = range.create();
        if (!r.isContentEditable()) {
            event.preventDefault();
            return false;
        }
        if (!r.isCollapsed()) {
            r = r.deleteContents();
            r.select();
        }

        var br = $("<br/>")[0];

        // set selection outside of A if range is at beginning or end
        var elem = dom.isBR(elem) ? elem.parentNode : dom.node(r.sc);
        if (elem.tagName === "A") {
            if (r.so === 0 && dom.firstChild(elem) === r.sc) {
                r.ec = r.sc = dom.hasContentBefore(elem) || $(dom.createText('')).insertBefore(elem)[0];
                r.eo = r.so = dom.nodeLength(r.sc);
                r.select();
            } else if (dom.nodeLength(r.sc) === r.so && dom.lastChild(elem) === r.sc) {
                r.ec = r.sc = dom.hasContentAfter(elem) || dom.insertAfter(dom.createText(''), elem);
                r.eo = r.so = 0;
                r.select();
            }
        }

        var node;
        var $node;
        var $clone;
        var contentBefore = r.sc.textContent.slice(0,r.so).match(/\S|\u00A0/);
        if (!contentBefore && dom.isText(r.sc)) {
            node = r.sc.previousSibling;
            while (!contentBefore && node && dom.isText(node)) {
                contentBefore = dom.isVisibleText(node);
                node = node.previousSibling;
            }
        }

        node = dom.node(r.sc);
        var exist = r.sc.childNodes[r.so] || r.sc;
        exist = dom.isVisibleText(exist) || dom.isBR(exist) ? exist : dom.hasContentAfter(exist) || (dom.hasContentBefore(exist) || exist);

        // table: add a tr
        var td = dom.ancestor(node, dom.isCell);
        if (td && !dom.nextElementSibling(node) && !dom.nextElementSibling(td) && !dom.nextElementSibling(td.parentNode) && (!dom.isText(r.sc) || !r.sc.textContent.slice(r.so).match(/\S|\u00A0/))) {
            $node = $(td.parentNode);
            $clone = $node.clone();
            $clone.children().html(dom.blank);
            $node.after($clone);
            node = dom.firstElementChild($clone[0]) || $clone[0];
            range.create(node, 0, node, 0).select();
            dom.scrollIntoViewIfNeeded(br);
            event.preventDefault();
            return false;
        }

        var last = node;
        while (node && dom.isSplitable(node) && !dom.isList(node)) {
            last = node;
            node = node.parentNode;
        }

        if (last === node && !dom.isBR(node)) {
            node = r.insertNode(br, true);
            if (isFormatNode(last.firstChild) && $(last).closest(options.styleTags.join(',')).length) {
                dom.moveContent(last.firstChild, last);
                last.removeChild(last.firstChild);
            }
            do {
                node = dom.hasContentAfter(node);
            } while (node && dom.isBR(node));

            // create an other br because the user can't see the new line with only br in a block
            if (!node && (!br.nextElementSibling || !dom.isBR(br.nextElementSibling))) {
                $(br).before($("<br/>")[0]);
            }
            node = br.nextSibling || br;
        } else if (last === node && dom.isBR(node)) {
            $(node).after(br);
            node = br;
        } else if (!r.so && r.isOnList() && !r.sc.textContent.length && !dom.ancestor(r.sc, dom.isLi).nextElementSibling) {
            // double enter on the end of a list = new line out of the list
//            $('<p></p>').append(br).insertAfter(dom.ancestor(r.sc, dom.isList));
            node.removeChild(node.lastChild);
            $(node).after(br);
            node = br;
        } else if (dom.isBR(exist) && $(r.sc).closest('blockquote, pre').length && !dom.hasContentAfter($(exist.parentNode).closest('blockquote *, pre *').length ? exist.parentNode : exist)) {
            // double enter on the end of a blockquote & pre = new line out of the list
            $('<p></p>').append(br).insertAfter($(r.sc).closest('blockquote, pre'));
            node = br;
        } else if (dom.isEditable(dom.node(r.sc))) {
            // if we are directly in an editable, only SHIFT + ENTER should add a newline
            node = null;
        } else if (last === r.sc) {
            if (dom.isBR(last)) {
                last = last.parentNode;
            }
            $node = $(last);
            $clone = $node.clone().text("");
            $node.after($clone);
            node = dom.node(dom.firstElementChild($clone[0]) || $clone[0]);
            $(node).html(br);
            node = br;
        } else {
            node = dom.splitTree(last, {'node': r.sc, 'offset': r.so}) || r.sc;
            if (!contentBefore) {
                // dom.node chooses the parent if node is text
                var cur = dom.node(dom.lastChild(node.previousSibling));
                if (!dom.isBR(cur)) {
                    // We should concat what was before with a <br>
                    $(cur).html(cur.innerHTML + br.outerHTML);
                }
            }
            if (!dom.isVisibleText(node)) {
                node = dom.firstChild(node);
                $(dom.node( dom.isBR(node) ? node.parentNode : node )).html(br);
                node = br;
            }
        }

        if (node) {
            node = dom.firstChild(node);
            if (dom.isBR(node)) {
                range.createFromNode(node).select();
            } else {
                range.create(node,0).select();
            }
            dom.scrollIntoViewIfNeeded(node);
        }
        event.preventDefault();
        return false;
    };
    function isFormatNode(node) {
        return node.tagName && options.styleTags.indexOf(node.tagName.toLowerCase()) !== -1;
    }
});
