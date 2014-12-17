(function () {
    var _t = openerp.web._t;
    var instance = openerp;

    var doThings = function () {
        openerp.web.DiagramView.include({
            load_diagrams: function (result) {
                this._super(result);
                console.log(this.fields_view.arch);

                var context = (new openerp.web.CompoundContext(self.context || self.dataset.context, this.nodes.attrs.context)).eval();
                console.log(context)
            },

            edit_node: function (node_id) {
                var self = this;
                var title = _t('Activity');
                var pop = new instance.web.form.FormOpenPopup(self);

                var context = (new openerp.web.CompoundContext(self.nodes.attrs.context)).eval();

                pop.show_element(
                    self.node,
                    node_id,
                    $.extend(context, self.context || self.dataset.context),
                    {
                        title: _t("Open: ") + title
                    }
                );

                pop.on('write_completed', self, function () {
                    self.dataset.read_index(_.keys(self.fields_view.fields)).then(self.on_diagram_loaded);
                });

                var form_fields = [self.parent_field];
                var form_controller = pop.view_form;

                form_controller.on("load_record", self, function () {
                    _.each(form_fields, function (fld) {
                        if (!(fld in form_controller.fields)) {
                            return;
                        }
                        var field = form_controller.fields[fld];
                        field.$input.prop('disabled', true);
                        field.$drop_down.unbind();
                    });
                });


            },

            // Creates a popup to add a node to the diagram
            add_node: function () {
                var self = this;
                var title = _t('Activity');
                var pop = new instance.web.form.SelectCreatePopup(self);

                var context = (new openerp.web.CompoundContext(self.nodes.attrs.context)).eval();

                pop.select_element(
                    self.node,
                    {
                        title: _t("Create:") + title,
                        initial_view: 'form',
                        disable_multiple_selection: true
                    },
                    self.dataset.domain,
                    $.extend(context, self.context || self.dataset.context)
                );
                pop.on("elements_selected", self, function (element_ids) {
                    self.dataset.read_index(_.keys(self.fields_view.fields)).then(self.on_diagram_loaded);
                });

                var form_controller = pop.view_form;
                var form_fields = [this.parent_field];

                form_controller.on("load_record", self, function () {
                    _.each(form_fields, function (fld) {
                        if (!(fld in form_controller.fields)) {
                            return;
                        }
                        var field = form_controller.fields[fld];
                        field.set_value(self.id);
                        field.dirty = true;
                    });
                });
            },

            // Creates a popup to edit the connector of id connector_id
            edit_connector: function (connector_id) {
                var self = this;
                var title = _t('Transition');
                var pop = new instance.web.form.FormOpenPopup(self);
                var context = (new openerp.web.CompoundContext(self.connectors.attrs.context)).eval();

                pop.show_element(
                    self.connector,
                    parseInt(connector_id, 10),      //FIXME Isn't connector_id supposed to be an int ?
                    $.extend(context, self.context || self.dataset.context),
                    {
                        title: _t("Open: ") + title
                    }
                );
                pop.on('write_completed', self, function () {
                    self.dataset.read_index(_.keys(self.fields_view.fields)).then(self.on_diagram_loaded);
                });
            },

            // Creates a popup to add a connector from node_source_id to node_dest_id.
            // dummy_cuteedge if not null, will be removed form the graph after the popup is closed.
            add_connector: function (node_source_id, node_dest_id, dummy_cuteedge) {
                var self = this;
                var title = _t('Transition');
                var pop = new instance.web.form.SelectCreatePopup(self);

                var context = (new openerp.web.CompoundContext(self.connectors.attrs.context)).eval();
                pop.select_element(
                    self.connector,
                    {
                        title: _t("Create:") + title,
                        initial_view: 'form',
                        disable_multiple_selection: true
                    },
                    this.dataset.domain,
                    $.extend(context, self.context || self.dataset.context)
                );
                pop.on("elements_selected", self, function (element_ids) {
                    self.dataset.read_index(_.keys(self.fields_view.fields)).then(self.on_diagram_loaded);
                });
                // We want to destroy the dummy edge after a creation cancel. This destroys it even if we save the changes.
                // This is not a problem since the diagram is completely redrawn on saved changes.
                pop.$el.parents('.modal').on('hidden.bs.modal', function (e) {
                    if (dummy_cuteedge) {
                        dummy_cuteedge.remove();
                    }
                });

                var form_controller = pop.view_form;


                form_controller.on("load_record", self, function () {
                    form_controller.fields[self.connectors.attrs.source].set_value(node_source_id);
                    form_controller.fields[self.connectors.attrs.source].dirty = true;
                    form_controller.fields[self.connectors.attrs.destination].set_value(node_dest_id);
                    form_controller.fields[self.connectors.attrs.destination].dirty = true;
                });
            },

        });
    };

    var t = setInterval(function () {
        var target = openerp.web.DiagramView;
        if (!!target) {
            clearInterval(t);
            doThings();
        }
    }, 50);

})();
