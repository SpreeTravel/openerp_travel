var availableTags = [];

function get_destinations(id, name) {
    if (id.value != '') {
        var request = $.post("/get_destinations/", {name: id.value});

        request.done(function (data) {
            availableTags = [];
            for (var index = 0; index < data['dest'].length; ++index) {
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

function create_option(text) {
    var option = document.createElement('option');
    option.innerHTML = text;
    option.value = text;
    return option
}

function create_label(type, text, number) {
    var adults_label = document.createElement('label');
    adults_label.setAttribute('for', 'input_' + type + '_hotel_' + number.toString());
    adults_label.innerHTML = text + ':';
    return adults_label
}

function create_select(type, number, quantity) {
    var select = document.createElement('select');
    select.setAttribute('class', 'form-control');
    select.setAttribute('id', 'input_' + type + '_hotel_' + number.toString());
    for (var index = 0; index < quantity; index++) {
        var option = create_option(index + 1);
        select.appendChild(option);
    }
    var option = create_option("more");
    select.appendChild(option);
    return select
}

function create_child(number) {
    var div = document.createElement('div');
    div.setAttribute('class', 'form-group form-inline');
    var label_adults = create_label('adults', 'Adults', number);
    div.appendChild(label_adults);
    var select_adults = create_select('adults', number, 5);
    div.appendChild(select_adults);
    var label_children = create_label('children', 'Children', number);
    div.appendChild(label_children);
    var select_children = create_select('children', number, 4);
    div.appendChild(select_children);
    return div
}


$(".autocomplete").on('change paste input', function () {
    get_destinations(this, 'to');
});

$("#input_room_hotel").on('change', function () {
    var room = document.getElementById('input_room_hotel');
    var container = document.getElementById('ad_ch_region');
    while (container.hasChildNodes())
        container.removeChild(container.lastChild);
    for (var index = 0; index < room.value; ++index) {
        container.appendChild(create_child(index + 1));
    }
});
