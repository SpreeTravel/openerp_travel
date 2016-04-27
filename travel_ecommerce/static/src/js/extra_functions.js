var availableTags = [];

function get_destinations(id, name) {
    if (id.value != '') {
        var request = $.post("/get_destinations/", {name: id.value});
        
        request.done(function (data) {
            availableTags = [];
            for (index = 0; index < data['dest'].length; ++index) {
                availableTags.push(data['dest'][index]);
            }
        });
        request.error(function (jqXHR, exception) {
            availableTags = [];
            if (jqXHR.status === 0)
                alert('Not connect.\n Verify Network.');
            else if (jqXHR.status == 404)
                alert('Requested page not found. [404]');
            else if (jqXHR.status == 500)
                alert('Internal Server Error [500].');
            else if (exception === 'parsererror')
                alert('Requested JSON parse failed.');
            else if (exception === 'timeout')
                alert('Time out error.');
            else if (exception === 'abort')
                alert('Ajax request aborted.');
            else
                alert('Uncaught Error.\n' + jqXHR.responseText);
        });
        
        $(id).autocomplete({
            source: availableTags
        });
    }
}

$(".autocomplete").on('change paste input', function () {
    get_destinations(this, 'to');
});


