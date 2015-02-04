if (window.jQuery) {
    window.jQuery.noConflict();
}

(function () {

    function script(url, callback) {
        var new_script = document.createElement('script');
        new_script.src = url + '?__stamp=' + Math.random();
        new_script.type = 'text/javascript';
        new_script.onload = new_script.onreadystatechange = callback;
        document.getElementsByTagName('head')[0].appendChild(new_script);
    }

    function loadCss(url) {
        $('<link />').attr({
            "rel": "stylesheet",
            "type": "text/css",
            "href": url + '?__stamp=' + Math.random()
        }).appendTo('head');
    }

    function iframe(url, callback) {
        var iframe = $('#odooIframe');
        if (!iframe.length) {
            iframe = $('<iframe/>').attr('id', 'odooIframe').appendTo('body');
        }
        iframe.on('load', callback);
        iframe.attr('src', url);
        return iframe;
    }

    var odoo;

    function publish(message) {
        odoo.get()[0].contentWindow.postMessage(JSON.stringify(message), '*');
    }

    script(window.odooUrl + '/builder/static/lib/jquery.js', function () {
        odoo = iframe(window.newSnippetUrl);
        var options = {
            css: {
                copy: true
            }
        };

        var channels = {
            'site.options': function (data, event) {
                options = $.extend(options, data.options);
            }
        };



        window.addEventListener("message", function (event) {
            var data = JSON.parse(event.data);
            var handler = channels[data.channel];
            if (handler) {
                handler(data, event);
            }
        }, false);

        /* Create iframe */
        loadCss(window.odooUrl + '/builder/static/src/css/bookmarklet.css');


        function css(element) {
            var css_rules = {};
            var rules = window.getMatchedCSSRules(element.get(0));
            for (var rule in rules) {
                if (rules.hasOwnProperty(rule)) {
                    css_rules = $.extend(css_rules, css2json(rules[rule].style), css2json(element.attr('style')));
                }
            }
            return css_rules;
        }

        function css2json(css) {
            var s = {};
            if (!css) return s;
            if (css instanceof CSSStyleDeclaration) {
                for (var i in css) {
                    if (css.hasOwnProperty(i)) {
                        if ((css[i]).toLowerCase) {
                            s[(css[i]).toLowerCase()] = (css[css[i]]);
                        }
                    }
                }
            }
            else if (typeof css == "string") {
                css = css.split("; ");
                for (i in css) {
                    if (css.hasOwnProperty(i)) {
                        var l = css[i].split(": ");
                        s[l[0].toLowerCase()] = (l[1]);
                    }
                }
            }
            return s;
        }

        function applyCssInline($elem) {
            if (options.css.copy) {
                $elem.css(css($elem));
            }
        }


        function getXPath(node) {
            var comp, comps = [];
            var xpath = '';
            var getPos = function (node) {
                var position = 1, curNode;
                if (node.nodeType == Node.ATTRIBUTE_NODE) {
                    return null;
                }
                for (curNode = node.previousSibling; curNode; curNode = curNode.previousSibling) {
                    if (curNode.nodeName == node.nodeName) {
                        ++position;
                    }
                }
                return position;
            };

            if (node instanceof Document) {
                return '/';
            }

            for (; node && !(node instanceof Document); node = node.nodeType == Node.ATTRIBUTE_NODE ? node.ownerElement : node.parentNode) {
                comp = comps[comps.length] = {};
                switch (node.nodeType) {
                    case Node.TEXT_NODE:
                        comp.name = 'text()';
                        break;
                    case Node.ATTRIBUTE_NODE:
                        comp.name = '@' + node.nodeName;
                        break;
                    case Node.PROCESSING_INSTRUCTION_NODE:
                        comp.name = 'processing-instruction()';
                        break;
                    case Node.COMMENT_NODE:
                        comp.name = 'comment()';
                        break;
                    case Node.ELEMENT_NODE:
                        comp.name = node.nodeName;
                        break;
                }
                comp.position = getPos(node);
            }

            for (var i = comps.length - 1; i >= 0; i--) {
                comp = comps[i];
                xpath += '/' + comp.name;
                if (comp.position != null) {
                    xpath += '[' + comp.position + ']';
                }
            }

            return xpath;

        }

        var fixed = false,
            $copy = $("<img />").attr({
                src: window.odooUrl + "/builder/static/src/img/gear.png",
                title: "Copy",
                alt: "Copy"
            }).addClass('bookmarklet-gear').on('click', processElement).appendTo('head');

        function drawActive(elem) {
            var $this = $(elem);
            $('.bookmarklet-active').removeClass('bookmarklet-active');
            $this.addClass('bookmarklet-active');
            if (fixed) {
                $this.prepend($copy.show());
            } else {
                $copy.hide().appendTo('head');
            }
        }

        function processElement(event) {
            if (event) {
                event.stopPropagation();
                event.preventDefault();
            }

            var $fixed = $(fixed);
            $copy.hide().appendTo('body');
            $fixed.removeClass('bookmarklet-active');
            applyCssInline($fixed);
            $fixed.find('*').each(function (index, value) {
                applyCssInline($(value));
            });

            publish({
                channel: 'snippet.html.set',
                xpath: getXPath(fixed),
                content: $fixed[0].outerHTML,
                url: window.location.href
            });
            fixed = false;

        }

        $(document).on('mouseenter', '*', function (event) {
            if (fixed) {
                return;
            }
            event.stopPropagation();
            event.preventDefault();

            drawActive(this);

        }).on('click', '*', function (event) {
            event.stopPropagation();
            event.preventDefault();

            if (!fixed) {
                fixed = this;
                drawActive(this);
            } else if (fixed == this) {
                fixed = false;
            } else {
                fixed = this;
                drawActive(this);
            }
        });
    });


})();