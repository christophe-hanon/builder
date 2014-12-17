(function (instance) {
    var _t = instance.web._t,
        _lt = instance.web._lt;
    var QWeb = instance.web.qweb;

    var odoo_tags = {
        "!top": ["openerp", 'menuitem'],
        openerp: {
          children: ['data']
        },

        data: {
          attrs: {
            noupdate: ['1', '0']
          },
          children: ['record', 'menuitem', 'template']
        },

        menuitem: {
          attrs: {
            name: null,
            id: function(cm){
              var cur = cm.getCursor(), token = cm.getTokenAt(cur);
              console.log(cur);
              console.log(token);
              window.cm = cm;
              window.cur = cur;
              window.token = token;
              console.log(this);
              return [token.state.tagName + "_1"];
            },
            parent: null,
            action: null,
            sequence: ['1', '2', '3', '4', '5', '6', '7', '8', '9']
          }
        },

        record: {
          attrs: {
            id: null,
            model: null
          },
          children: ['field']
        },

        field: {
          attrs: {
            name: null,
            string: null,
            type: ["xml"],
            eval: null,
            invisible: "1",
            attrs: "{}",
            domain: "[]"
          },
          children: ['tree', 'form', 'kanban', 'search', 'diagram', 'graph']
        },

        tree: {
          attrs: {
            colors: null,
            string: null
          },
          children: ['field']
        }

      };

    instance.builder = instance.builder || {};
    instance.builder.codemirror = {
        hint: {
            schema: {
                odoo: odoo_tags
            }
        }
    };


})(openerp);
