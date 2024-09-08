$(function () {
    $("#reports_menu_btn").click();
    
    var CSRF_TOKEN = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
    
    function get_dates(dt) {
        var mindate = $('#min_date').val();
        var maxdate = $('#max_date').val();
        let dt_start, dt_end = "";
        if (mindate) dt_start = mindate + ' 00:00:00.000000';
        if (maxdate) dt_end = maxdate + ' 23:59:59.999999';
        return (dt === 0) ? dt_start : dt_end;
    }

    function clear_dates() {
        $('#min_date').val('');
        $('#max_date').val('');
    }

    function formatCurrency(num) {
        return num.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) + ' TZS';
    };

    $("#items_report thead tr").clone(true).attr('class','filters').appendTo('#items_report thead');
    var items_report = $("#items_report").DataTable({
        fixedHeader: true,
        processing: true,
        serverSide: true,
        ajax: {
            url: $("#sale_items_report").val(),
            type: "POST",
            data: function (d) {
                d.start_date = get_dates(0);
                d.end_date = get_dates(1);
            },
            dataType: 'json',
            headers: { 'X-CSRFToken': CSRF_TOKEN },
            dataSrc: function (json) {
                var tableFooter = $('#items_report tfoot');
                $(tableFooter).find('tr').eq(1).find('th').eq(5).html(formatCurrency(json.grand_total));
                return json.data;
            },
        },
        columns: [
            { data: 'count' },
            { data: 'saledate' },
            { data: 'product' },
            { data: 'price' },
            { data: 'qty' },
            { data: 'amount' },
            { data: 'user' },
        ],
        order: [[2, 'desc']],
        paging: true,
        lengthMenu: [[10, 20, 40, 50, 100, -1], [10, 20, 40, 50, 100, "All"]],
        pageLength: 10,
        lengthChange: true,
        autoWidth: true,
        searching: true,
        bInfo: true,
        bSort: true,
        orderCellsTop: true,
        dom: "lBfrtip",
        columnDefs: [{
            targets: 0,
            orderable: false,
        },
        {
            targets: 2,
            className: 'ellipsis text-start'
        },
        {
            targets: 6,
            createdCell: function (cell, cellData, rowData, rowIndex, colIndex) {
                var cell_content = `<a href="${rowData.user_info}" class="text-color1">${rowData.user}</a>`;
                $(cell).attr('class', 'ellipsis text-start');
                $(cell).html(cell_content);
            }
        }],
        buttons: [
            { // Copy button
                extend: "copy",
                text: "<i class='fas fa-clone'></i>",
                className: "btn btn-color1 text-white",
                titleAttr: "Copy",
                title: "Sales-items-report - ShopApp",
                exportOptions: {
                    columns: [0, 1, 2, 3, 4, 5, 6]
                }
            },
            { // PDF button
                extend: "pdf",
                text: "<i class='fas fa-file-pdf'></i>",
                className: "btn btn-color1 text-white",
                titleAttr: "Export to PDF",
                title: "Sales report - ShopApp",
                filename: 'sales-items-report',
                orientation: 'landscape',
                pageSize: 'A4',
                footer: true,
                exportOptions: {
                    columns: [0, 1, 2, 3, 4, 5, 6],
                    search: 'applied',
                    order: 'applied'
                },
                tableHeader: {
                    alignment: "center"
                },
                customize: function(doc) {
                    doc.styles.tableHeader.alignment = "center";
                    doc.styles.tableBodyOdd.alignment = "center";
                    doc.styles.tableBodyEven.alignment = "center";
                    doc.styles.tableHeader.fontSize = 7;
                    doc.defaultStyle.fontSize = 6;
                    doc.content[1].table.widths = Array(doc.content[1].table.body[1].length + 1).join('*').split('');

                    var body = doc.content[1].table.body;
                    for (i = 1; i < body.length; i++) {
                        doc.content[1].table.body[i][0].margin = [3, 0, 0, 0];
                        doc.content[1].table.body[i][0].alignment = 'center';
                        doc.content[1].table.body[i][1].alignment = 'center';
                        doc.content[1].table.body[i][2].alignment = 'left';
                        doc.content[1].table.body[i][3].alignment = 'right';
                        doc.content[1].table.body[i][4].alignment = 'right';
                        doc.content[1].table.body[i][5].alignment = 'right';
                        doc.content[1].table.body[i][6].alignment = 'left';
                        doc.content[1].table.body[i][6].margin = [0, 0, 3, 0];

                        for (let j = 0; j < body[i].length; j++) {
                            body[i][j].style = "vertical-align: middle;";
                        }
                    }
                }
            },
            { // Export to excel button
                extend: "excel",
                text: "<i class='fas fa-file-excel'></i>",
                className: "btn btn-color1 text-white",
                titleAttr: "Export to Excel",
                title: "Sales items report - ShopApp",
                exportOptions: {
                    columns: [0, 1, 2, 3, 4, 5, 6]
                }
            },
            { // Print button
                extend: "print",
                text: "<i class='fas fa-print'></i>",
                className: "btn btn-color1 text-white",
                title: "Sales items report - ShopApp",
                orientation: 'landscape',
                pageSize: 'A4',
                titleAttr: "Print",
                footer: true,
                exportOptions: {
                    columns: [0, 1, 2, 3, 4, 5, 6],
                    search: 'applied',
                    order: 'applied'
                },
                tableHeader: {
                    alignment: "center"
                },
                customize: function (win) {
                    $(win.document.body).css("font-size","11pt");
                    $(win.document.body).find("table").addClass("compact").css("font-size","inherit");
                }
            }
        ],
        footerCallback: function (row, data, start, end, display) {
            var api = this.api(), data;
            
            var intVal = function ( i ) {
                return typeof i === 'string' ?
                    i.replace(/[\s,]/g, '')
                     .replace(/TZS/g, '')
                     * 1 :
                    typeof i === 'number' ?
                        i : 0;
            };
            
            var salesTotal = api
                .column(5)
                .data()
                .reduce(function (a, b) {
                    return intVal(a) + intVal(b);
                }, 0);

            var pageTotalValue = formatCurrency(salesTotal);
            var tableFooter = $(api.table().footer());

            $(tableFooter).find('tr').eq(0).find('th').eq(5).html(pageTotalValue);
        },
        initComplete: function() {
            var api = this.api();
            api.columns([0, 1, 2, 3, 4, 5, 6]).eq(0).each(function (colIdx) {
                var cell = $(".filters th").eq($(api.column(colIdx).header()).index());
                if (colIdx == 1) {
                    var calendar =`<button type="button" class="btn btn-sm btn-color1 text-white" data-bs-toggle="modal" data-bs-target="#date_filter_modal"><i class="fas fa-calendar-alt"></i></button>`;
                    cell.html(calendar);
                    $("#date_clear").on("click", function() {
                        $("#min_date").val("");
                        $("#max_date").val("");
                    });
                    $("#date_filter_btn").on("click", function() {
                        items_report.draw();
                    });
                } else if (colIdx == 0) {
                    cell.html("");
                } else {
                    $(cell).html("<input type='text' class='text-color6' placeholder='Filter..'/>");
                    $("input", $(".filters th").eq($(api.column(colIdx).header()).index()))
                    .off("keyup change").on("keyup change", function(e) {
                        e.stopPropagation();
                        $(this).attr('title', $(this).val());
                        var regexr = "{search}";
                        var cursorPosition = this.selectionStart;
                        api.column(colIdx).search(
                            this.value != '' ? regexr.replace('{search}', this.value) : '',
                            this.value != '',
                            this.value == ''
                            ).draw();
                        $(this).focus()[0].setSelectionRange(cursorPosition, cursorPosition);
                    });
                }
            });
        }
    });

    $("#items_search").keyup(function() {
        items_report.search($(this).val()).draw();
    });

    $("#items_filter_clear").click(function (e) {
        e.preventDefault();
        $("#items_search").val('');
        clear_dates();
        items_report.search('').draw();
    });
});