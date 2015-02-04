(function () {
    function publish(message){
        parent.postMessage(JSON.stringify(message), '*');
    }

    var channels = {
        'snippet.html.set': function (data, event){
            $('#url').val(data.url);
            $('#xpath').val(data.xpath);
            $('#html').val(data.content);
        }
    };

    window.addEventListener("message", function (event) {
        var data = JSON.parse(event.data);
        var handler = channels[data.channel];
        if (handler){
            handler(data, event);
        }
    }, false);

    $('#copy-css').change(function (){
        publish({
            channel: 'site.options',
            options: {
                css: {
                    copy: $(this).is(':checked')
                }
            }
        });
    });

    /*
    * TODO: fields can not be empty
    * */

    //$('#snippet-form').submit(function (event){
    //    $('input, textarea')
    //});


})();