$(document).ready(function(){

    //показать поле поиска
    $("#search").show()

    //удаление строк в таблице
    $("#table-storage-config").on('click', '#remove', function () {
        var id = $(this).closest('tr')
        $.ajax({
            type: "POST",
            url: "/storage_config/delete",
            data: JSON.stringify({ 'id': id.attr('value')}),
            success: function(response) {
                id.remove();
            }
        });
    });

    //управление чекбоксами по метрикам
    $('#metrics input').on('click', function() {
        var checkbox = $(this)
        var selectValue = $(checkbox).parent().next()
        var selectUnit = $(selectValue).next()
        var addMetrics = $('#addMetrics')
        if ($(checkbox).is(':checked')) {
            $(selectValue).prop('disabled', false)
            $(selectUnit).prop('disabled', false)
            $(addMetrics).prop('disabled', false)
        } else {
            if ($('#metrics input:checked').length == 0) {
                $(addMetrics).prop('disabled', true)
            }
            $(selectValue).prop('disabled', true)
            $(selectUnit).prop('disabled', true)
        }
    })

    //управление чекбоксами по суммированию
    $('#summarization input').on('click', function() {
        var addSumm = $('#addSumm')
        var checkbox = $(this)
        if ($(checkbox).is(':checked')) {
            $(addSumm).prop('disabled', false)
        }
        if ($('#summarization input:checked').length == 0) {
                $(addSumm).prop('disabled', true)
            }
    })


    //кнопка сохранить для логов
    $('#addLogs').click(function(e) {
        var start_time = $('#logs #start-time option:selected').val()
        var selectValue = $('#logs #value').val()
        var selectUnit = $('#logs #unit').val()
        var json = [{ 'value': selectValue,
                      'unit': selectUnit}]
        $.ajax({
            type: "POST",
            url: "/storage_config",
            data: JSON.stringify({ 'name': 'log error ', 'type': 'log', 'params': json,
                                    'start_time': start_time }),
            success: function(response) {
                $('#table-storage-config').children().remove()
                $.each(response.jobs, function(id,elem){
                        $("#table-storage-config").append('<tr value=' + id + '>' +
                                                    '<td>' + elem.title + '</td>' +
                                                    '<td>' + elem.description + '</td>' +
                                                    '<td>' + elem.next_run + '</td>' +
                                                    '<td><button type="button" id="remove" class="btn btn-danger">Удалить</button></td>' +
                                               '</tr>')
                    });
                    $('div.modal-header').after('<div class="alert alert-success">Добавлено</div>');
                            setTimeout(function(){
                                  $('div.modal-header').next().remove();
                            }, 2000);
            },
            error:
                function(data) {
                    $('div.modal-header').after('<div class="alert alert-warning">Ошибка добавления</div>');
                    setTimeout(function(){
                          $('div.modal-header').next().remove();
                    }, 2000);
            }
        })
    })

    //кнопка сохранить для метрик
    $('#addMetrics').click(function(e) {
        var metric = $('#metrics option:selected').val()
        var metricDesc = $('#metrics option:selected').html()
        var json = []
        var start_time = $('#metrics #start-time option:selected').val()
        $('#metrics input:checked').each(function(i,el) {
            var selectValue = $(el).parent().next()
            var checkboxValue = $(el)
            var selectUnit = $(selectValue).next()
            var row = {'data': $(checkboxValue).val(),
                        'value': $(selectValue).val(),
                        'unit': $(selectUnit).val()}
            json.push(row)
        })

        $.ajax({
            type: "POST",
            url: "/storage_config",
            data: JSON.stringify({ 'id': metric, 'name': metricDesc, 'type': 'trunc', 'params': json,
                                    'start_time': start_time }),
            success: function(response) {
                $("#table-storage-config").children().remove()
                    $.each(response.jobs, function(id,elem){
                        $("#table-storage-config").append('<tr value=' + id + '>' +
                                                        '<td>' + elem.title + '</td>' +
                                                        '<td>' + elem.description + '</td>' +
                                                        '<td>' + elem.next_run + '</td>' +
                                                    '<td><button type="button" id="remove" class="btn btn-danger">Удалить</button></td>' +
                                               '</tr>')
                    });
                    $('div.modal-header').after('<div class="alert alert-success">Добавлено</div>');
                            setTimeout(function(){
                                  $('div.modal-header').next().remove();
                            }, 2000);
            },
            error:
                function(data) {
                    $('div.modal-header').after('<div class="alert alert-warning">Ошибка добавления</div>');
                    setTimeout(function(){
                          $('div.modal-header').next().remove();
                    }, 2000);
            }
        })
    })

    //кнопка сохранить для суммирования
    $('#addSumm').click(function(e) {
        var metric = $('#summ option:selected').val()
        var metricDesc = $('#summ option:selected').html()
        var json = []
        var start_time = $('#summarization #start-time option:selected').val()
        $('#summarization input:checked').each(function(i,el) {
            var checkboxValue = $(el).val()
            var row = {'unit': checkboxValue}
            json.push(row)
        })

        $.ajax({
            type: "POST",
            url: "/storage_config",
            data: JSON.stringify({ 'id': metric, 'name': metricDesc, 'type': 'summ', 'params': json,
                                    'start_time': start_time }),
            success: function(response) {
                $("#table-storage-config").children().remove()
                    $.each(response.jobs, function(id,elem){
                        $("#table-storage-config").append('<tr value=' + id + '>' +
                                                    '<td>' + elem.title + '</td>' +
                                                    '<td>' + elem.description + '</td>' +
                                                    '<td>' + elem.next_run + '</td>' +
                                                    '<td><button type="button" id="remove" class="btn btn-danger">Удалить</button></td>' +
                                               '</tr>')
                    });
                    $('div.modal-header').after('<div class="alert alert-success">Добавлено</div>');
                            setTimeout(function(){
                                  $('div.modal-header').next().remove();
                            }, 2000);
            },
            error:
                function(data) {
                    $('div.modal-header').after('<div class="alert alert-warning">Ошибка добавления</div>');
                    setTimeout(function(){
                          $('div.modal-header').next().remove();
                    }, 2000);
            }
        })
    })

    //поиск по таблице
    $("#search").on('keyup', function(){
        var search = $("#search").val().toLowerCase();
        $("tbody tr").filter(function(){
            $(this).toggle($(this).text().toLowerCase().indexOf(search) > -1 )
        })
    })
});