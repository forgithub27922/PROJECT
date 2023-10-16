odoo.define('odoo_advance_search.ControlPanelController', function (require) {
"use strict";

var core = require('web.core');
var session = require('web.session');
var ControlPanelController = require('web.ControlPanelController');
var _t = core._t;

ControlPanelController.include({
	build_search_data: function(search){
		var parent = this.getParent();
		var renderer = parent.renderer;
		/*if (parent.active_view!==undefined && parent.active_view!==null  && parent.active_view.type!==undefined && parent.active_view.type==='list'){*/
        if (renderer){
			self=this;
        	self.cust_seach_domain = [];
        	//var renderer = parent.active_view.controller.renderer;
        	if (!renderer.def_column_val){
            	renderer.def_column_val = {};
            }
        	$('.odoo_field_search_expan').each(function(){
				if (this.value){
					this.value = this.value.trim()
					var cust_field = this;
        			var field_type = this.getAttribute('field_type');
        			for (var i = 0; i < renderer.columns.length; i++ ){
        				if (field_type!==undefined && session.has_advance_search_group && (field_type==='date' || field_type==='datetime')){
        					var field_name_from = renderer.columns[i].attrs.name+'_from';
        					var field_name_to = renderer.columns[i].attrs.name+'_to';
        					if (field_name_from===cust_field.name || field_name_to===cust_field.name){
            					renderer.def_column_val[cust_field.name] = cust_field.value;
            				}
        				}
        				else if (field_type!==undefined && field_type==='many2one'){
        					if (renderer.columns[i].attrs.name===cust_field.name){
        						renderer.def_column_val[cust_field.name] = [cust_field.value, cust_field.title];
        					}
        				}
        				else{
        					if (renderer.columns[i].attrs.name===cust_field.name){
            					renderer.def_column_val[cust_field.name] = cust_field.value;
            				}
        				}
        			}
        			if (field_type!==undefined && field_type==='selection'){
        				self.cust_seach_domain.push([this.name,'=',this.value]);
        			}
        			else if (field_type!==undefined && field_type==='boolean'){
        				if (this.value==='true'){
        					self.cust_seach_domain.push([this.name,'=',true]);
        				}
        				else{
        					self.cust_seach_domain.push([this.name,'=',false]);
        				}
        			}
        			else if (field_type!==undefined && (field_type==='date' || field_type==='datetime')){
        					if (this.name.endsWith('_from')){
            					var field_name = this.name.substring(0,this.name.lastIndexOf('_from'));
            					self.cust_seach_domain.push([field_name,'>=',this.value]);
            				}
            				else if (this.name.endsWith('_to')){
            					var field_name = this.name.substring(0,this.name.lastIndexOf('_to'));
            					self.cust_seach_domain.push([field_name,'<=',this.value]);
            				}
            				renderer.def_column_val[this.name] = this.value;
        			}
        			else if (field_type!==undefined && (field_type==='integer' || field_type==='float' || field_type==='monetary')){
        				var value = this.value;
        				if (field_type==='integer'){
        					value = parseInt(this.value);
        				}else{
        					value = parseFloat(this.value);
        				}
        				self.cust_seach_domain.push([this.name,'=',value]);
        			}
        			else if (field_type!==undefined && (field_type==='many2one')){
        				value = parseInt(this.value);
        				self.cust_seach_domain.push([this.name,'=',value]);
        			}
        			else{
        				self.cust_seach_domain.push([this.name,'ilike',this.value]);
        			}
        		}
        		else{
        			renderer.def_column_val[this.name] = '';
        		}
        	});
        	if (self.cust_seach_domain!==undefined && self.cust_seach_domain.length>0){
        		if (!search.domain){
        			search.domain = [];
        		}
        		search.domain = search.domain.concat(self.cust_seach_domain);
        		if (renderer.noContentHelp!==undefined){
        			renderer.noContentHelp=false;
        		}
        	}
        }
		return search;
	},
});
});