$(document).ready(function(){
    //управление полями ввода
  	var name = $('#username')
    var pass = $('#password')
    $("input").on('keyup', function(){
    	if ($(name).val().length > 0 && $(pass).val().length > 0) {
          $("#submit").prop('disabled', false)
        } else {
          $("#submit").prop('disabled', true)
        }
    })
})