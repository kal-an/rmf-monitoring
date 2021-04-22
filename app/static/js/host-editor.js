$(document).ready(function(){

    //показать поле поиска
    $("#search").show()

    
    //удалить хост
    $("#table-host-editor").on('click', '#remove', function () {
        var id = $(this).closest('tr')
        $.ajax({
            type: "POST",
            url: "/host_editor/delete",
            data: JSON.stringify({ 'host': id.attr('value')}),
            success: function(response) {
                id.remove();
            }
        });
    });

    //кнопка закрыть
    $('button#close').click(function(e) {
        $('#host').val('').prop('disabled', false)
        $('button#save').prop('disabled', true)
    });

    //кнопка сохранить
    $('button#save').click(function(e) {
        var hostname = $('#host').val().toUpperCase()
        $.ajax({
            type: "POST",
            url: "/host_editor",
            data: JSON.stringify({ 'host': hostname }),
            success: function(response) {
                if (response.hosts) {
                    $('div.modal-header').after('<div class="alert alert-success">Добавлен</div>');
                            setTimeout(function(){
                                  $('div.modal-header').next().remove();
                            }, 2000);
                    $("#table-host-editor").children().remove()
                    $.each(response.hosts, function(id,elem){
                        $("#table-host-editor").append('<tr value=' + elem + '>' +
                                                    '<td>' + elem + '</td>' +
                                                    '<td><button type="button" id="remove" class="btn btn-danger">Удалить</button></td>' +
                                               '</tr>')
                    });
                }
                else {
                    $('div.modal-header')
                        .after('<div class="alert alert-warning">Ошибка:<br>'+ response.error +'</div>');
                        setTimeout(function(){
                              $('div.modal-header').next().remove();
                        }, 2000);
                }
                $('#host').val('').prop('disabled', false)
                $('button#save').prop('disabled', true)
                // $('#hostEditorModal').modal('toggle')
            },
            error:
                function(data) {
                    $('div.modal-header').after('<div class="alert alert-warning">Ошибка:<br>'+ data.error +'</div>');
                    setTimeout(function(){
                          $('div.modal-header').next().remove();
                    }, 3000);
            }
        })
    })

    //проверить хост
    $('button#check').click(function(e) {
        e.preventDefault();
        var hostname = $('#host').val().toUpperCase()
        var preloader = $('#preloader');

        $.ajax({
            type: "POST",
            url: "/host_editor",
            data: JSON.stringify({ 'host': hostname,'request_type': 'root' }),
            beforeSend: function () {
                preloader.fadeIn()
            },
            complete: function () {
                preloader.fadeOut()
            },
            success: function(response) {
                if (response.success == 1) {
                    $('div.modal-header').after('<div class="alert alert-success">Проверен</div>');
                            setTimeout(function(){
                                  $('div.modal-header').next().remove();
                            }, 2000);
                        $('button#save').prop('disabled', false)
                        $('#host').prop('disabled', true)
                    } else {
                        $('div.modal-header')
                            .after('<div class="alert alert-warning">Ошибка:<br>'+ response.error +'</div>');
                            setTimeout(function(){
                                  $('div.modal-header').next().remove();
                            }, 2000);
                    }
            },
            error: function(data) {
                    $('div.modal-header').after('<div class="alert alert-warning">Ошибка:<br>хост не ответил</div>');
                    setTimeout(function(){
                          $('div.modal-header').next().remove();
                    }, 3000);
            },
            timeout: 10000
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