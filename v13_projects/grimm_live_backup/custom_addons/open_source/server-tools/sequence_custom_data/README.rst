====================
Sequence custom data
====================

.. !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
   !! This file is generated by oca-gen-addon-readme !!
   !! changes will be overwritten.                   !!
   !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

.. |badge1| image:: https://img.shields.io/badge/maturity-Beta-yellow.png
    :target: https://odoo-community.org/page/development-status
    :alt: Beta
.. |badge2| image:: https://img.shields.io/badge/licence-AGPL--3-blue.png
    :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
    :alt: License: AGPL-3
.. |badge3| image:: https://img.shields.io/badge/github-OCA%2Fserver--tools-lightgray.png?logo=github
    :target: https://github.com/OCA/server-tools/tree/13.0/sequence_custom_data
    :alt: OCA/server-tools
.. |badge4| image:: https://img.shields.io/badge/weblate-Translate%20me-F47D42.png
    :target: https://translation.odoo-community.org/projects/server-tools-13-0/server-tools-13-0-sequence_custom_data
    :alt: Translate me on Weblate
.. |badge5| image:: https://img.shields.io/badge/runbot-Try%20me-875A7B.png
    :target: https://runbot.odoo-community.org/runbot/149/13.0
    :alt: Try me on Runbot

|badge1| |badge2| |badge3| |badge4| |badge5| 

This is a technical module.
The goal is to allow others module to define new variables/codes to use during the sequence generation.

So this module is not useful alone. You have to create your own module to add some values into your sequences.

**Table of contents**

.. contents::
   :local:

Usage
=====

To use this module, you need to:

* depend on this module
* Inherit the `ir.sequence` to fill your custom values

Example:

.. code-block:: python

  class IrSequence(models.Model):
      _inherit = "ir.sequence"

      def _get_special_values(self, date=None, date_range=None):
          values = super()._get_special_values(date=date, date_range=date_range)
          company_code = self.env.company.special_code
          values.update({"company_code": company_code or ""})
          return values`

You can also update the documentation (on the bottom of `ir.sequence` form view) to
describe variables that your add and the purpose of them.

Example:

.. code-block:: XML

  <?xml version="1.0" encoding="utf-8"?>
  <odoo>
      <record model="ir.ui.view" id="ir_sequence_form_view">
          <field name="name">ir.sequence.form (in custom_module)</field>
          <field name="model">ir.sequence</field>
          <field name="inherit_id" ref="base.sequence_view"/>
          <field name="priority" eval="90"/>
          <field name="arch" type="xml">
              <xpath expr="//page[1]" position="inside">
                  <group col="3" name="custom_legend">
                      <group string="Company" name="custom_legend_company">
                          <span colspan="2">Specific company code: {company_code}</span>
                      </group>
                  </group>
              </xpath>
          </field>
      </record>
  </odoo>

Bug Tracker
===========

Bugs are tracked on `GitHub Issues <https://github.com/OCA/server-tools/issues>`_.
In case of trouble, please check there if your issue has already been reported.
If you spotted it first, help us smashing it by providing a detailed and welcomed
`feedback <https://github.com/OCA/server-tools/issues/new?body=module:%20sequence_custom_data%0Aversion:%2013.0%0A%0A**Steps%20to%20reproduce**%0A-%20...%0A%0A**Current%20behavior**%0A%0A**Expected%20behavior**>`_.

Do not contact contributors directly about support or help with technical issues.

Credits
=======

Authors
~~~~~~~

* ACSONE SA/NV

Contributors
~~~~~~~~~~~~

* François Honoré <francois.honore@acsone.eu>

Maintainers
~~~~~~~~~~~

This module is maintained by the OCA.

.. image:: https://odoo-community.org/logo.png
   :alt: Odoo Community Association
   :target: https://odoo-community.org

OCA, or the Odoo Community Association, is a nonprofit organization whose
mission is to support the collaborative development of Odoo features and
promote its widespread use.

This module is part of the `OCA/server-tools <https://github.com/OCA/server-tools/tree/13.0/sequence_custom_data>`_ project on GitHub.

You are welcome to contribute. To learn how please visit https://odoo-community.org/page/Contribute.
