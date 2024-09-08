$(function () {
    // tabs
    $("#container .user_info ul li a").click(function (e) { 
        e.preventDefault();
        var tab_id = $(this).attr('href').replace('#','');
        $("#container .user_info .tab_container .tab_div").each(function () {
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

    // Register new user
    $("#new_user_form").submit(function (e) { 
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
                $("#user_cancel_btn").removeClass('d-inline-block').addClass('d-none');
                $("#user_submit_btn").html("<i class='fas fa-spinner fa-pulse'></i> Saving").attr('type', 'button');
            },
            success: function(response) {
                $("#user_cancel_btn").removeClass('d-none').addClass('d-inline-block');
                $("#user_submit_btn").text("Save").attr('type', 'submit');

                var fdback = generate_errorsms(response.success, response.sms);
                
                $("#new_user_canvas .offcanvas-body").animate({ scrollTop: 0 }, 'slow');
                $("#new_user_form .formsms").html(fdback);
                
                if(response.update_success) {
                    // $("#user_info_div").load(location.href + " #user_info_div");
                } else if(response.success) {
                    $("#new_user_form")[0].reset();
                    users_table.draw();
                }
            },
            error: function(xhr, status, error) {
                $("#user_cancel_btn").removeClass('d-none').addClass('d-inline-block');
                $("#user_submit_btn").text("Save").attr('type', 'submit');
                var fdback = generate_errorsms(false, "Unknown error, reload & try again");
                $("#new_user_canvas .offcanvas-body").animate({ scrollTop: 0 }, 'slow');
                $("#new_user_form .formsms").html(fdback);
            }
        });
    });

    function get_dates(dt) {
        const mindate = $('#min_date').val();
        const maxdate = $('#max_date').val();
        let dt_start = "";
        let dt_end = "";
        if (mindate) dt_start = mindate + ' 00:00:00.000000';
        if (maxdate) dt_end = maxdate + ' 23:59:59.999999';
        return (dt === 0) ? dt_start : dt_end;
    }

    function clear_dates() {
        $('#min_date').val('');
        $('#max_date').val('');
    }

    $("#users_table thead tr").clone(true).attr('class','filters').appendTo('#users_table thead');
    var users_table = $("#users_table").DataTable({
        fixedHeader: true,
        processing: true,
        serverSide: true,
        ajax: {
            url: $("#users_list_url").val(),
            type: "POST",
            data: function (d) {
                d.startdate = get_dates(0);
                d.enddate = get_dates(1);
            },
            dataType: 'json',
            headers: { 'X-CSRFToken': CSRF_TOKEN },
        },
        columns: [
            { data: 'count' },
            { data: 'regdate' },
            { data: 'fullname' },
            { data: 'username' },
            { data: 'phone' },
            { data: 'status' },
            { data: 'action' },
        ],
        order: [[1, 'desc']],
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
            "targets": [0, 6],
            "orderable": false,
        },
        {
            targets: 2,
            className: 'ellipsis text-start',
        },
        {
            targets: 5,
            createdCell: function (cell, cellData, rowData, rowIndex, colIndex) {
                if (rowData.status == 'Blocked') {
                    $(cell).attr('class','text-danger');
                } else {
                    $(cell).attr('class','text-color1');
                }
            }
        },
        {
            targets: 6,
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
                title: "Users - ShopApp",
                exportOptions: {
                    columns: [0, 1, 2, 3, 4, 5]
                }
            },
            { // PDF button
                extend: "pdf",
                text: "<i class='fas fa-file-pdf'></i>",
                className: "btn btn-color1 text-white",
                titleAttr: "Export to PDF",
                title: "Users - ShopApp",
                filename: 'users-udom-ems',
                orientation: 'portrait',
                pageSize: 'A4',
                footer: true,
                exportOptions: {
                    columns: [0, 1, 2, 3, 4, 5],
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
                        doc.content[1].table.body[i][3].alignment = 'left';
                        doc.content[1].table.body[i][4].alignment = 'left';
                        doc.content[1].table.body[i][5].alignment = 'left';
                        doc.content[1].table.body[i][5].margin = [0, 0, 3, 0];

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
                title: "Users - ShopApp",
                exportOptions: {
                    columns: [0, 1, 2, 3, 4, 5]
                }
            },
            { // Print button
                extend: "print",
                text: "<i class='fas fa-print'></i>",
                className: "btn btn-color1 text-white",
                title: "Users - ShopApp",
                orientation: 'portrait',
                pageSize: 'A4',
                titleAttr: "Print",
                footer: true,
                exportOptions: {
                    columns: [0, 1, 2, 3, 4, 5],
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
                        users_table.draw();
                    });
                } else if (colIdx == 5) {
                    var select = document.createElement("select");
                    select.className = "select-filter text-color6 float-start";
                    select.innerHTML = `<option value="">All</option>` +
                    `<option value="Active">Active</option>` +
                    `<option value="Blocked">Blocked</option>`;
                    cell.html(select);
                    
                    // Add change event listener to the select
                    $(select).on("change", function() {
                        api.column(colIdx).search($(this).val()).draw();
                    });
                } else if (colIdx == 0 || colIdx == 6) {
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

    $("#users_search").keyup(function() {
        users_table.search($(this).val()).draw();
    });

    $("#users_filter_clear").click(function (e) { 
        e.preventDefault();
        $("#users_search").val('');
        clear_dates();
        users_table.search('').draw();
    });

    var btn_blocking = false;
    $("#user_block_btn").click(function (e) { 
        e.preventDefault();
        if (btn_blocking == false) {
            var class_attr = $(this).attr('class');
            var btn_text = $(this).text();
            var formdata = new FormData();
            formdata.append('block_user', parseInt($('#get_user_id').val()));

            $.ajax({
                type: 'POST',
                url: $('#new_user_form').attr('action'),
                data: formdata,
                dataType: 'json',
                contentType: false,
                processData: false,
                headers: {
                    'X-CSRFToken': CSRF_TOKEN
                },
                beforeSend: function() {
                    btn_blocking = true;
                    $("#user_block_btn").html("<i class='fas fa-spinner fa-pulse'></i> Updating");
                },
                success: function(response) {
                    btn_blocking = false;
                    if (response.success) {
                        location.reload();
                    } else {
                        $("#user_block_btn").text(btn_text).attr('class', class_attr);
                        window.alert("Failed to block this user account.");
                    }
                },
                error: function(xhr, status, error) {
                    console.log(error);
                }
            });
        }
    });

    var btn_deleting = false;
    $("#confirm_delete_btn").click(function (e) { 
        e.preventDefault();
        if(btn_deleting == false) {
            var formData = new FormData();
            formData.append("delete_user", $("#get_user_id").val());

            $.ajax({
                type: 'POST',
                url: $("#new_user_form").attr('action'),
                data: formData,
                dataType: 'json',
                contentType: false,
                processData: false,
                headers: {
                    'X-CSRFToken': CSRF_TOKEN
                },
                beforeSend: function() {
                    btn_deleting = true;
                    $("#cancel_delete_btn").removeClass('d-inline-block').addClass('d-none');
                    $("#confirm_delete_btn").html("<i class='fas fa-spinner fa-pulse'></i>");
                },
                success: function(response) {
                    btn_deleting = false;
                    if(response.success) {
                        window.alert('User account deleted..!');
                        window.location.href = response.url;
                    } else {
                        $("#cancel_delete_btn").removeClass('d-none').addClass('d-inline-block');
                        $("#confirm_delete_btn").html("<i class='fas fa-check-circle'></i> Yes");

                        var fdback = `<div class="alert alert-danger alert-dismissible fade show px-2 m-0 d-block w-100"><i class='fas fa-exclamation-circle'></i> ${response.sms} <button type="button" class="btn-close d-inline-block" data-bs-dismiss="alert"></button></div>`;

                        $("#confirm_delete_modal .formsms").html(fdback);
                    }
                },
                error: function(xhr, status, error) {
                    console.log(error);
                }
            });
        }
    });

    var btn_resetting = false;
    $("#confirm_reset_btn").click(function (e) { 
        e.preventDefault();
        if(btn_resetting == false) {
            var formData = new FormData();
            formData.append("reset_password", $("#get_user_id").val());

            $.ajax({
                type: 'POST',
                url: $("#new_user_form").attr('action'),
                data: formData,
                dataType: 'json',
                contentType: false,
                processData: false,
                headers: {
                    'X-CSRFToken': CSRF_TOKEN
                },
                beforeSend: function() {
                    btn_resetting = true;
                    $("#cancel_reset_btn").removeClass('d-inline-block').addClass('d-none');
                    $("#confirm_reset_btn").html("<i class='fas fa-spinner fa-pulse'></i>");
                },
                success: function(response) {
                    btn_resetting = false;
                    if(response.success) {
                        $("#confirm_reset_modal").modal('hide');
                        window.alert('Password has been reset to default');
                    } else {
                        $("#cancel_reset_btn").removeClass('d-none').addClass('d-inline-block');
                        $("#confirm_reset_btn").html("<i class='fas fa-check-circle'></i> Yes");

                        var fdback = `<div class="alert alert-danger alert-dismissible fade show px-2 m-0 d-block w-100"><i class='fas fa-exclamation-circle'></i> ${response.sms} <button type="button" class="btn-close d-inline-block" data-bs-dismiss="alert"></button></div>`;

                        $("#confirm_reset_modal .formsms").html(fdback);
                    }
                },
                error: function(xhr, status, error) {
                    console.log(error);
                }
            });
        }
    });
});