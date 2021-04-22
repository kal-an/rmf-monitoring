$(document).ready(function(){

    //управление полями ввода
  	var login = $('#login')
    var dn = $('#dn')
    var full_name = $('#full-name')

    $("input").on('keyup', function(){
        if ($(login).val().length > 0 && $(dn).val().length > 0 && $(full_name).val().length > 0) {
        $("#save").prop('disabled', false)
        } else {
        $("#save").prop('disabled', true)
        }
    })

    //удалить пользователя
    $("#table-admin").on('click', '#remove', function () {
        var id = $(this).closest('tr')
        $.ajax({
            type: "DELETE",
            url: "/admin",
            data: JSON.stringify({ 'id': id.attr('value')}),
            success: function(response) {
                id.remove();
            }
        });
    });

    //кнопка сохранить
    $('button#save').click(function(e) {
        var login = $('#login').val()
        var dn = $('#dn').val()
        var full_name = $('#full-name').val()
        var role_id = $('#role').val()
        var preloader = $('#preloader');
        
        $.ajax({
            type: "POST",
            url: "/admin",
            data: JSON.stringify({ 'login': login, 'dn': dn, 'full_name': full_name, 'role_id': role_id }),
            beforeSend: function () {
                preloader.fadeIn()
            },
            complete: function () {
                preloader.fadeOut()
            },
            success: function(response) {
                if (!response.error) {
                    $('div.modal-header').after('<div class="alert alert-success">Добавлен</div>');
                            setTimeout(function(){
                                  $('div.modal-header').next().remove();
                            }, 2000);
                    $("#table-admin").children().remove()
                    $.each(response, function(id,elem){
                        $("#table-admin").append('<tr value=' + elem.id + '>' +
                                                    '<td>' + elem.login + '</td>' +
                                                    '<td>' + elem.dn + '</td>' +
                                                    '<td>' + elem.full_name + '</td>' +
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

});