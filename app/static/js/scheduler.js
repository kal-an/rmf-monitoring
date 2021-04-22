$(document).ready(function(){

    //показать поле поиска
    $("#search").show()

    //отменить
    $('button#close').click(function(e) {
        $("select[name=hosts] option:first").prop('selected', true);
        $("div.container-fluid div.row:not(:first, :last)").remove()
    });

    //сохранить
    $('button#save').click(function(e) {
        var host = $('select[name=hosts]').val()
        json = []
        $("div.container-fluid div.row:not(:first)").each(function(i,r) {
            resource_url = $(r).find('select[name=resource]').val()
            resource_name = $(r).find('select[name=resource] option:selected').html()
            metric_id = $(r).find('select[name=metric-list]').val()
            metric_description = $(r).find('select[name="metric-list"] option:selected').html()
            metric_format = $(r).find('select[name="metric-list"] option:selected').data('format')
            interval = $(r).find('select[name="interval"]').val()
            row = { 'resource_name': resource_name,
                    'resource_url': resource_url,
                    'metric_id': metric_id,
                    'metric_description': metric_description,
                    'metric_format': metric_format,
                    'interval': interval,
                    'host': host
                    }
            if (resource_url != '-' && interval != '-') {
                json.push(row)
            }
            });
        if (json.length != 0) {
            $.ajax({
                type: "POST",
                contentType: 'application/json; charset=utf-8',
                dataType: 'json',
                url: "/scheduler",
                data: JSON.stringify({ 'resources': json }),
                success: function(response) {
                    $('#table-scheduler').children().remove()
                    $.each(response.jobs, function(id,elem){
                        $('#table-scheduler').append('<tr value=' + id + '>' +
                                                    '<td>' + elem.host.slice(0, 4) + '</td>' +
                                                    '<td>' + elem.resource_name + '</td>' +
                                                    '<td>' + elem.metric_description + '</td>' +
                                                    '<td>' + elem.metric_id + '</td>' +
                                                    '<td>' + elem.interval + '</td>' +
                                                    '<td>' + elem.next_run + '</td>' +
                                                    '<td><button type="button" id="remove" class="btn btn-danger">Удалить</button></td>' +
                                               '</tr>')
                    });
                    $('div.modal-header').after('<div class="alert alert-success">Добавлено</div>');
                            setTimeout(function(){
                                  $('div.modal-header').next().remove();
                            }, 2000);
                },
                error: function(data) {
                    $('div.modal-header').after('<div class="alert alert-warning">Ошибка:<br>Ошибка сохранения</div>');
                    setTimeout(function(){
                          $('div.modal-header').next().remove();
                    }, 3000);
                },
                timeout: 10000
            });
        }
    });

    //удалить из таблицы
    $("#table-scheduler").on('click', '#remove', function () {
        var id = $(this).closest('tr')
        $.ajax({
            type: "POST",
            dataType: 'json',
            contentType: 'application/json; charset=utf-8',
            url: "/scheduler/delete",
            data: JSON.stringify({ 'job_id': id.attr('value') }),
            success: function(response) {
                id.remove();
            }
        });
    });

    //выбор хостов
    $("select[name=hosts]").on("change", function(e) {
        //удалить строки
        $(this).parents("div.row").nextAll("div.row:not(:first)").remove()
         host = $("select[name=hosts]").val()
         var preloader = $('#preloader');
         request_type = 'root'
         value = ''
         next_row = $(this).parent().next()
         if ($(this).val() != '-') { // если ничего не выбрано
            $.ajax({
                type: "POST",
                url: "/get_resources",
                data: JSON.stringify({ 'host': host, 'contained': value, 'request_type': request_type }),
                beforeSend: function () {
                    preloader.fadeIn()
                },
                complete: function () {
                    preloader.fadeOut()
                },
                success: function(response) {
                    if (response.resources.length > 0) {
                        next_resource_select = $(next_row).find("select:first")
                        //удалить элементы списка
                        $(next_row).find("select:first").children("option:not(:first)").remove()
                        $.each(response.resources, function(index,value){
                            $("<option/>", {
                                value: value.reslabelurl,
                                text: value.reslabel
                            }).appendTo(next_resource_select)
                        });
                        $(next_row).show()
                    }
                },
                error: function(data) {
                    $('div.modal-header').after('<div class="alert alert-warning">Таймаут соединения, данные не получены</div>');
                    setTimeout(function(){
                          $('div.modal-header').next().remove();
                        }, 3000);
                },
                timeout: 10000
            })
         } else {
            $(this).parents("div.row").nextAll("div.row:not(:first)").remove()
            $(next_row).hide()
         }
         $(this).parents('div.row').next().find('select[name=metric-list]').children('option').remove();
    })

    //выбор ресурса
    $("select[name=resource]").on("change", function(e) {
        $(this).parents("div.row").nextAll("div.row").remove()
         host = $("select[name=hosts]").val()
         var preloader = $('#preloader');
         request_type = 'contained'
         value = $(this).val()
         current_row = $(this).parent()
         if ($(this).val() != '-') {
            $.ajax({
                type: "POST",
                url: "/get_resources",
                data: JSON.stringify({ 'host': host, 'contained': value, 'request_type': request_type }),
                beforeSend: function () {
                    preloader.fadeIn()
                },
                complete: function () {
                    preloader.fadeOut()
                },
                success: function(response) {
                    current_row = $(current_row).parent()
                    metric_select = $(current_row).find("select[name=metric-list]")
                    $(metric_select).children('option').remove()
                    //Заполнение метрик
                    $.each(response.listmetrics, function(index,value){
                        $(metric_select).append($("<option></option>")
                                .attr("data-format", value.format)
                                .attr("value", value.id)
                                .text(value.description))
                        })
                    if (response.resources.length > 0) { //если есть дочерние элементы
                        //клонировать последнюю строку
                        $(current_row).clone(true).appendTo("div.container-fluid")
                        next_row = $(current_row).next()
                        next_metric_select = $(next_row).find("select[name=metric-list]").children("option").remove()
                        //удалить элементы списка метрик
//                        $(next_metric_select).children("option").remove()
                        next_resource_select = $(next_row).find("select:first")
                        //удалить элементы списка
                        $(next_row).find("select:first").children("option:not(:first)").remove()
                        $.each(response.resources, function(index,value){
                            $("<option/>", {
                                value: value.reslabelurl,
                                text: value.reslabel
                            }).appendTo(next_resource_select)
                        });
                        $(next_row).show()
                    }
                },
                error: function(data) {
                    $('div.modal-header').after('<div class="alert alert-warning">Таймаут соединения, данные не получены</div>');
                    setTimeout(function(){
                          $('div.modal-header').next().remove();
                        }, 3000);
                },
                timeout: 10000
            })
         }
    })

    //поиск по таблице
    $("#search").on('keyup', function(){
        var search = $("#search").val().toLowerCase();
        $("tbody tr").filter(function(){
            $(this).toggle($(this).text().toLowerCase().indexOf(search) > -1 )
        })
    })
});