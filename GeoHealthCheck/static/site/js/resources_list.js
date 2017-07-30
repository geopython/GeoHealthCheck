$('#resources-table').dataTable({
    'paging': false,
    'sDom': ''//false // no search box
});
//    Morris.Donut({
//        element: 'totals-chart',
//        colors: ['#5CB85C', '#D9534F'],
//        data: [
//            {label: 'Working', value: {{ response['success']['number']|safe }} },
//            {label: 'Broken', value: {{ response['fail']['number']|safe }} },
//        ],
//        resize: true
//    });


// rudimentary table filter
$('#filter').keyup(function () {
    //var selector = '.searchable tr';
    var selector = 'td.facet-name';
    var term = $(this).val();
    var tokens = [];
    var td_text = null;
    var facet = null;
    var num_results = 0;

    if (term.match('^site:|title:|type:|url:')) {
        if (term.match('^title:')) {
            selector = 'td.facet-name';
        }
        else if (term.match('^type:')) {
            selector = 'td.facet-type';
        }
        else if (term.match('^url:|site:')) {
            selector = 'a.facet-url';
        }
        tokens = term.split(':');
        facet = tokens[0];
        term = tokens[1];
    }

    var rex = new RegExp(term, 'i');
    $('.searchable tr').hide(); // hide all rows

    $(selector).each(function() {
        if (facet === 'url') {
            td_text = $(this).attr('title');
        }
        if (facet === 'site') {
            td_text = $(this).attr('title').split('/')[2];
        }
        else {
            td_text = $(this).text();
        }
        if (rex.test(td_text)) {
            $(this).closest('tr').show();
            num_results += 1;
        }
    });
    $('#resources-table-num-results').html(num_results + ' result' + (num_results === 1 ? '' : 's'));
});
$('select').select2({disabled: true, tags: true});
