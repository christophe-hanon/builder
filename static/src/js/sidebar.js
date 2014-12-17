(function(){
    var _t = openerp.web._t;

    openerp.web.Sidebar.include({

        start: function () {
            var self = this;
            var ids;
            this._super.apply(this, arguments);
            var view = self.getParent();
            var result;

            if (view.fields_view.type == "form") {
                ids = [];
                view.on("load_record", self, function (r) {
                    ids = [r.id];
                    self.add_export_items(view, r.id)
                });
            }

            self.add_import_items(view)
        },

        fetch: function (model, fields, domain, ctx) {
            return new instance.web.Model(model).query(fields).filter(domain).context(ctx).all()
        },

        add_export_items: function(view, res_id){
            var self  = this;

            var ds = new openerp.web.DataSet(self, 'builder.ir.module.module');

            ds.call('get_available_export_formats', []).done(function(formats){
                _.each(formats, function(format){
                    self.add_items('other', [
                            {
                                label: format.name,
                                callback: self.on_export_item_clicked,
                                format: format.type,
                                res_id: res_id,
                                classname: 'action_export_' + format.type
                            }
                        ]
                    )
                });
            });
        },

        add_import_items: function(view, res_id){
            var self  = this;

            var ds = new openerp.web.DataSet(self, 'builder.ir.module.module');

            ds.call('get_available_import_formats', []).done(function(formats){
                _.each(formats, function(format){
                    self.add_items('other', [
                            {
                                label: format.name,
                                callback: self.on_import_item_clicked,
                                format: format.type,
                                res_id: res_id,
                                classname: 'action_import_' + format.type
                            }
                        ]
                    )
                });
            });
        },

        on_export_item_clicked: function(item){
            this.do_action({
                type: 'ir.actions.act_url',
                target: 'self',
                url: '/builder/export/' + item.format + '/' + item.res_id
            });
        },

        on_import_item_clicked: function(item){
            this.do_action({
                type: 'ir.actions.act_url',
                target: 'self',
                url: '/builder/export/' + item.format + '/' + item.res_id
            });
        }
    });

})();

