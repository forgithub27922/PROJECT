# -*- coding: utf-8 -*-

"""
Bug fix for mass_editing_wizard
"""

from lxml import etree
from odoo import models, api
from odoo import tools


class MassEditingWizard(models.TransientModel):
    _inherit = 'mass.editing.wizard'

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        result = super(MassEditingWizard, self).fields_view_get(view_id=view_id,
                                                                view_type=view_type,
                                                                toolbar=toolbar,
                                                                submenu=submenu)
        context = self._context
        if context.get('mass_editing_object'):
            mass_obj = self.env['mass.editing']
            editing_data = mass_obj.browse(context.get('mass_editing_object'))
            all_fields = {}
            xml_form = etree.Element('form', {
                'string': tools.ustr(editing_data.name)
            })
            xml_group = etree.SubElement(xml_form, 'group', {
                'colspan': '6',
                'col': '6',
            })
            etree.SubElement(xml_group, 'label', {
                'string': '',
                'colspan': '2',
            })
            xml_group = etree.SubElement(xml_form, 'group', {
                'colspan': '6',
                'col': '6',
            })
            model_obj = self.env[context.get('active_model')]
            field_info = model_obj.fields_get()
            for field in editing_data.field_ids:
                if field.ttype == "many2many":
                    all_fields[field.name] = field_info[field.name]
                    all_fields["selection__" + field.name] = {
                        'type': 'selection',
                        'string': field_info[field.name]['string'],
                        'selection': [('set', 'Set'),
                                      ('remove_m2m', 'Remove'),
                                      ('add', 'Add')]
                    }
                    xml_many2many_group = etree.SubElement(xml_group, 'group', {
                        'colspan': '6',
                        'col': '6',
                    })
                    etree.SubElement(xml_many2many_group, 'separator', {
                        'string': field_info[field.name]['string'],
                        'colspan': '6',
                    })
                    etree.SubElement(xml_many2many_group, 'field', {
                        'name': "selection__" + field.name,
                        'colspan': '6',
                        'nolabel': '1'
                    })
                    etree.SubElement(xml_many2many_group, 'field', {
                        'name': field.name,
                        'colspan': '6',
                        'nolabel': '1',
                        'attrs': ("{'invisible': [('selection__" +
                                  field.name + "', '=', 'remove_m2m')]}"),
                    })
                elif field.ttype == "one2many":
                    all_fields["selection__" + field.name] = {
                        'type': 'selection',
                        'string': field_info[field.name]['string'],
                        'selection': [('set', 'Set'), ('remove', 'Remove')],
                    }
                    all_fields[field.name] = {
                        'type': field.ttype,
                        'string': field.field_description,
                        'relation': field.relation,
                    }
                    etree.SubElement(xml_group, 'separator', {
                        'string': all_fields[field.name]['string'],
                        'colspan': '6',
                    })
                    etree.SubElement(xml_group, 'field', {
                        'name': "selection__" + field.name,
                        'colspan': '4',
                    })
                    etree.SubElement(xml_group, 'field', {
                        'name': field.name,
                        'colspan': '6',
                        'nolabel': '1',
                        'attrs': ("{'invisible':[('selection__" +
                                  field.name + "', '=', 'remove_o2m')]}"),
                    })
                elif field.ttype == "many2one":
                    all_fields["selection__" + field.name] = {
                        'type': 'selection',
                        'string': field_info[field.name]['string'],
                        'selection': [('set', 'Set'), ('remove', 'Remove')],
                    }
                    all_fields[field.name] = {
                        'type': field.ttype,
                        'string': field.field_description,
                        'relation': field.relation,
                    }
                    etree.SubElement(xml_group, 'separator', {
                        'string': all_fields[field.name]['string'],
                        'colspan': '6',
                    })
                    etree.SubElement(xml_group, 'field', {
                        'name': "selection__" + field.name,
                        'colspan': '2',
                    })
                    etree.SubElement(xml_group, 'field', {
                        'name': field.name,
                        'nolabel': '1',
                        'colspan': '4',
                        'attrs': ("{'invisible':[('selection__" +
                                  field.name + "', '=', 'remove')]}"),
                    })
                elif field.ttype == "char":
                    all_fields["selection__" + field.name] = {
                        'type': 'selection',
                        'string': field_info[field.name]['string'],
                        'selection': [('set', 'Set'), ('remove', 'Remove')],
                    }
                    all_fields[field.name] = {
                        'type': field.ttype,
                        'string': field.field_description,
                        'size': field.size or 256,
                    }
                    etree.SubElement(xml_group, 'separator', {
                        'string': all_fields[field.name]['string'],
                        'colspan': '6',
                    })
                    etree.SubElement(xml_group, 'field', {
                        'name': "selection__" + field.name,
                        'colspan': '2',
                    })
                    etree.SubElement(xml_group, 'field', {
                        'name': field.name,
                        'nolabel': '1',
                        'attrs': ("{'invisible':[('selection__" +
                                  field.name + "','=','remove')]}"),
                        'colspan': '4',
                    })
                elif field.ttype == 'selection':
                    all_fields["selection__" + field.name] = {
                        'type': 'selection',
                        'string': field_info[field.name]['string'],
                        'selection': [('set', 'Set'), ('remove', 'Remove')]
                    }
                    etree.SubElement(xml_group, 'separator', {
                        'string': all_fields[field.name]['string'],
                        'colspan': '6',
                    })
                    etree.SubElement(xml_group, 'field', {
                        'name': "selection__" + field.name,
                        'colspan': '2',
                    })
                    etree.SubElement(xml_group, 'field', {
                        'name': field.name,
                        'nolabel': '1',
                        'colspan': '4',
                        'attrs': ("{'invisible':[('selection__" +
                                  field.name + "', '=', 'remove')]}"),
                    })
                    all_fields[field.name] = {
                        'type': field.ttype,
                        'string': field.field_description,
                        'selection': field_info[field.name]['selection'],
                    }
                else:
                    all_fields[field.name] = {
                        'type': field.ttype,
                        'string': field.field_description,
                    }
                    all_fields["selection__" + field.name] = {
                        'type': 'selection',
                        'string': field_info[field.name]['string'],
                        'selection': [('set', 'Set'), ('remove', 'Remove')]
                    }
                    # xml_group = etree.SubElement(xml_group, 'group', {
                    #     'colspan': '6',
                    #     'col': '6',
                    # })
                    etree.SubElement(xml_group, 'separator', {
                        'string': all_fields[field.name]['string'],
                        'colspan': '6',
                    })
                    if field.ttype == 'text':

                        etree.SubElement(xml_group, 'field', {
                            'name': "selection__" + field.name,
                            'colspan': '6',
                            'nolabel': '1',
                        })
                        etree.SubElement(xml_group, 'field', {
                            'name': field.name,
                            'colspan': '6',
                            'nolabel': '1',
                            'attrs': ("{'invisible':[('selection__" +
                                      field.name + "','=','remove')]}"),
                        })
                    else:
                        all_fields["selection__" + field.name] = {
                            'type': 'selection',
                            'string': field_info[field.name]['string'],
                            'selection': [('set', 'Set'), ('remove', 'Remove')]
                        }
                        etree.SubElement(xml_group, 'field', {
                            'name': "selection__" + field.name,
                            'colspan': '2',
                        })
                        etree.SubElement(xml_group, 'field', {
                            'name': field.name,
                            'nolabel': '1',
                            'attrs': ("{'invisible':[('selection__" +
                                      field.name + "','=','remove')]}"),
                            'colspan': '4',
                        })
            # Patch fields with required extra data
            for field in all_fields.values():
                field.setdefault("views", {})
            etree.SubElement(xml_form, 'separator', {
                'string': '',
                'colspan': '6',
                'col': '6',
            })
            xml_group3 = etree.SubElement(xml_form, 'footer', {})
            etree.SubElement(xml_group3, 'button', {
                'string': 'Apply',
                'class': 'btn-primary',
                'type': 'object',
                'name': 'action_apply',
            })
            etree.SubElement(xml_group3, 'button', {
                'string': 'Close',
                'class': 'btn-default',
                'special': 'cancel',
            })
            root = xml_form.getroottree()
            result['arch'] = etree.tostring(root).decode("utf-8")
            result['fields'] = all_fields
        return result
