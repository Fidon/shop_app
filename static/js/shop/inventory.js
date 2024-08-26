$(function () {
    // tabs
    $("#container .product_info ul li a").click(function (e) { 
        e.preventDefault();
        var tab_id = $(this).attr('href').replace('#','');
        $("#container .product_info .tab_container .tab_div").each(function () {
            if (($(this).is(':visible')) && ($(this).attr('id') !== tab_id)) {
                $(this).css('display','none');
                $('#'+tab_id).fadeIn('slow');
            }
        });
    });

    var CSRF_TOKEN = document.querySelector('meta[name="csrf-token"]').getAttribute('content');

    function generate_errorsms(status, sms) {
        return `<div class="alert alert-${status ? 'success' : 'danger'} alert-dismissible fade show px-2 m-0 d-block w-100"><i class='fas fa-${status ? 'check' : 'exclamation'}-circle'></i> ${sms} <button type="button" class="btn-close d-inline-block" data-bs-dismiss="alert"></button></div>`;
    }

    // Register new product
    $("#new_product_form").submit(function (e) { 
        e.preventDefault();
        
        $.ajax({
            type: 'POST',
            url: $(this).attr('action'),
            data: new FormData($(this)[0]),
            dataType: 'json',
            contentType: false,
            processData: false,
            headers: {
                'X-CSRFToken': CSRF_TOKEN
            },
            beforeSend: function() {
                $("#product_cancel_btn").removeClass('d-inline-block').addClass('d-none');
                $("#product_submit_btn").html("<i class='fas fa-spinner fa-pulse'></i> Saving").attr('type', 'button');
            },
            success: function(response) {
                $("#product_cancel_btn").removeClass('d-none').addClass('d-inline-block');
                $("#product_submit_btn").text("Save").attr('type', 'submit');

                var fdback = generate_errorsms(response.success, response.sms);
                
                $("#new_product_canvas .offcanvas-body").animate({ scrollTop: 0 }, 'slow');
                $("#new_product_form .formsms").html(fdback);
                
                if(response.update_success) {
                    // $("#user_info_div").load(location.href + " #user_info_div");
                } else if(response.success) {
                    $("#new_product_form")[0].reset();
                    products_table.draw();
                }
            },
            error: function(xhr, status, error) {
                $("#product_cancel_btn").removeClass('d-none').addClass('d-inline-block');
                $("#product_submit_btn").text("Save").attr('type', 'submit');
                var fdback = generate_errorsms(false, "Operation failed.");
                $("#new_product_canvas .offcanvas-body").animate({ scrollTop: 0 }, 'slow');
                $("#new_product_form .formsms").html(fdback);
            }
        });
    });

    function get_dates(dt, div) {
        var mindate, maxdate, dt_start, dt_end = "";
        if (div == 'exp') {
            mindate = $('#exp_min_date').val();
            maxdate = $('#exp_max_date').val();
        } else if (div == 'reg') {
            mindate = $('#reg_min_date').val();
            maxdate = $('#reg_max_date').val();
        } else {
            mindate = $('#min_date').val();
            maxdate = $('#max_date').val();
        }
        if (mindate) dt_start = mindate + ' 00:00:00.000000';
        if (maxdate) dt_end = maxdate + ' 23:59:59.999999';
        return (dt === 0) ? dt_start : dt_end;
    }

    function clear_dates() {
        $('#min_date').val('');
        $('#max_date').val('');
        $('#reg_min_date').val('');
        $('#reg_max_date').val('');
        $('#exp_min_date').val('');
        $('#exp_max_date').val('');
    }

    $("#products_table thead tr").clone(true).attr('class','filters').appendTo('#products_table thead');
    var products_table = $("#products_table").DataTable({
        fixedHeader: true,
        processing: true,
        serverSide: true,
        ajax: {
            url: $("#inventory_list_url").val(),
            type: "POST",
            data: function (d) {
                d.start_reg = get_dates(0, 'reg');
                d.end_reg = get_dates(1, 'reg');
                d.start_edit = get_dates(0, 'edit');
                d.end_edit = get_dates(1, 'edit');
                d.start_exp = get_dates(0, 'exp');
                d.end_exp = get_dates(1, 'exp');
            },
            dataType: 'json',
            headers: { 'X-CSRFToken': CSRF_TOKEN },
        },
        columns: [
            { data: 'count' },
            { data: 'regdate' },
            { data: 'lastedit' },
            { data: 'names' },
            { data: 'qty' },
            { data: 'price' },
            { data: 'expiry' },
            { data: 'action' },
        ],
        order: [[3, 'asc']],
        paging: true,
        lengthMenu: [[10, 20, 40, 50, 100, -1], [10, 20, 40, 50, 100, "All"]],
        pageLength: 10,
        lengthChange: true,
        autoWidth: true,
        searching: true,
        bInfo: true,
        bSort: true,
        orderCellsTop: true,
        columnDefs: [{
            "targets": [0, 7],
            "orderable": false,
        },
        {
            targets: 3,
            className: 'ellipsis text-start',
        },
        {
            targets: 7,
            className: 'align-middle text-nowrap text-center',
            createdCell: function (cell, cellData, rowData, rowIndex, colIndex) {
                var cell_content = `<a href="${rowData.info}" class="btn btn-color1 text-white btn-sm">View</a>`;
                $(cell).html(cell_content);
            }
        }],
        dom: "lBfrtip",
        buttons: [
            { // Copy button
                extend: "copy",
                text: "<i class='fas fa-clone'></i>",
                className: "btn btn-color1 text-white",
                titleAttr: "Copy",
                title: "Inventory products - ShopApp",
                exportOptions: {
                    columns: [0, 1, 2, 3, 4, 5, 6]
                }
            },
            { // PDF button
                extend: "pdf",
                text: "<i class='fas fa-file-pdf'></i>",
                className: "btn btn-color1 text-white",
                titleAttr: "Export to PDF",
                title: "Inventory products - ShopApp",
                filename: 'inventory-store',
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
                        doc.content[1].table.body[i][2].alignment = 'center';
                        doc.content[1].table.body[i][3].alignment = 'left';
                        doc.content[1].table.body[i][4].alignment = 'center';
                        doc.content[1].table.body[i][5].alignment = 'left';
                        doc.content[1].table.body[i][6].alignment = 'center';
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
                title: "Inventory products - ShopApp",
                exportOptions: {
                    columns: [0, 1, 2, 3, 4, 5, 6]
                }
            },
            { // Print button
                extend: "print",
                text: "<i class='fas fa-print'></i>",
                className: "btn btn-color1 text-white",
                title: "Inventory products - ShopApp",
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
        initComplete: function() {
            var api = this.api();
            api.columns([0, 1, 2, 3, 4, 5, 6, 7]).eq(0).each(function (colIdx) {
                var cell = $(".filters th").eq($(api.column(colIdx).header()).index());
                if (colIdx == 1) {
                    var calendar =`<button type="button" class="btn btn-sm btn-color1 text-white" data-bs-toggle="modal" data-bs-target="#reg_date_filter_modal"><i class="fas fa-calendar-alt"></i></button>`;
                    cell.html(calendar);
                    $("#date_clear").on("click", function() {
                        $("#reg_min_date").val("");
                        $("#reg_max_date").val("");
                    });
                    $("#reg_date_filter_btn").on("click", function() {
                        products_table.draw();
                    });
                } else if (colIdx == 2) {
                    var calendar =`<button type="button" class="btn btn-sm btn-color1 text-white" data-bs-toggle="modal" data-bs-target="#date_filter_modal"><i class="fas fa-calendar-alt"></i></button>`;
                    cell.html(calendar);
                    $("#date_clear").on("click", function() {
                        $("#min_date").val("");
                        $("#max_date").val("");
                    });
                    $("#date_filter_btn").on("click", function() {
                        products_table.draw();
                    });
                } else if (colIdx == 6) {
                    var calendar =`<button type="button" class="btn btn-sm btn-color1 text-white" data-bs-toggle="modal" data-bs-target="#expiry_filter_modal"><i class="fas fa-calendar-alt"></i></button>`;
                    cell.html(calendar);
                    $("#exp_date_clear").on("click", function() {
                        $("#exp_min_date").val("");
                        $("#exp_max_date").val("");
                    });
                    $("#exp_date_filter_btn").on("click", function() {
                        products_table.draw();
                    });
                } else if (colIdx == 0 || colIdx == 7) {
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

    $("#products_search").keyup(function() {
        products_table.search($(this).val()).draw();
    });

    $("#products_filter_clear").click(function (e) { 
        e.preventDefault();
        $("#products_search").val('');
        clear_dates();
        products_table.search('').draw();
    });
});