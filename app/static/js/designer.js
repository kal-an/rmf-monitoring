$(document).ready(function(){

    //выставить часы в селекторе
    date = new Date()
    hour = date.toLocaleString('Ru-RU', {hour: '2-digit', hour12: false, timeZone:'Europe/Moscow'})
    time_selector = $("#start-time option:contains(" + hour +")")
    $(time_selector).prop('selected', true)

    //загрузка селекторов
    $("div#params select").not("select[name=metric]").on('change', function (e) {
        var preloader = $('#preloader');
        current_select = $(this)
        rtype = $("select[name=rtype]").val()
        rname = $("select[name=rname]").val()
        metric = $("select[name=metric]").val()
        request_type = $(this).parents().next().find("select").attr("name")
        $(this).parent("div").nextAll().find("option:not([value='-'])").remove()
        hideTemplateElements()
        $('button#submit, button#xls, button#addTemplate').prop('disabled', true)
        if ($(this).val() != '-') {
            $.ajax({
                    type: "POST",
                    contentType: 'application/json; charset=utf-8',
                    dataType: 'json',
                    url: "/designer",
                    data: JSON.stringify({ 'rtype': rtype, 'metric': metric,
                                           'rname': rname, 'request_type': request_type}),
                    beforeSend: function () {
                        preloader.fadeIn()
                    },
                    complete: function () {
                        preloader.fadeOut()
                    },
                    success: function(response) {
                        hideTemplateElements()
                        next_select = $(current_select).parent().next().find("select")
                        $(next_select).children('option:not(:first)').remove()
                        $.each(response.values, function(i,value){
                            v = value
                            t = value
                            if (request_type == 'metric') {
                                v = value[0]
                                t = value[1]
                            }
                            $("<option/>", {
                                value: v,
                                text: t
                            }).appendTo(next_select)
                        });
                        $(next_select).parent().show()
                    },
                    error: function(data) {
                        console.log('Ошибка загрузки данных')
                    },
                    timeout: 10000
                });
            }
    });


    //состояние кнопки "показать"
    $("select[name=metric]").on('change', function (e) {
        $("#element").children('option').remove()
        if ($(this).val() != '-') {
            $('button#submit, button#xls, button#addTemplate').prop('disabled', false)
        } else {
            $('button#submit, button#xls, button#addTemplate').prop('disabled', true)
        }
    })

    //при изменении любого списка скрывать элементы
    $("div#params select").on('change', function (e) {
        hideTemplateElements()
    })

    //обновление списка элементов по отчету
    function templateElementsUpdater(list) {
        let select = $("#template-elements");
        let searchElement = $("#searchElement");
        $(select).children('option').remove();
        $.each(list, function(index,value){ //вставить значения в селектор
            $(select).append($("<option></option>")
                    .attr("value", value)
                    .text(value))
            })

        if (list[0] == '-') { //если 1 элемент, то список не показывать и выбрать его
            $("#template-elements option:first").prop('selected', true)
            $(select).parent().hide()
            $(searchElement).hide()
        } else {
            $(select).parent().show();
            $(searchElement).show();
        }
    }

    //скрыть список элементов
    function hideTemplateElements() {
        let select = $("#template-elements");
        let searchField = $("#searchElement");
        $(select).children('option').remove();
        $(select).parent().hide()
        $(searchField).hide()
    }

    //подготовка графика
    var ctx = $('#pChart');
    var chart = new Chart(ctx, {
        type:'line',
        data: {},
        options: {}
    })

    //управление кликом по легенде
    function LegendClickHandler(e, legendItem) {
        var index = legendItem.datasetIndex;
        var chart = this.chart;
        var meta = chart.getDatasetMeta(index);
        meta.hidden = meta.hidden === null ? !chart.data.datasets[index].hidden: null;
        chart.update();
    }


    //календарь
    $("#datepicker").datepicker({
        weekStart: 1,
        autoclose: true,
        daysOfWeekHighligheted: "6,0",
        todayHighlight: true,
        language: "ru"
    });
    $("#datepicker").datepicker("setDate", new Date())
    
    // выбор значений по метрике
    $("button#submit").on('click', function (e) {
        var preloader = $('#preloader');
        rtype = $("select[name=rtype]").val()
        rname = $("select[name=rname]").val()
        metric = $("select[name=metric]").val()
        unit = $("select#unit option:selected").val()
        unit_value = $("select#unit-value option:selected").val()
        date = $("#datepicker").val()
        time = $("#start-time").val()
        elements = $("#template-elements").val()

        if (metric != "-") {
                $.ajax({
                    type: "POST",
                    contentType: 'application/json; charset=utf-8',
                    dataType: 'json',
                    url: "/designer",
                    data: JSON.stringify({ 'rtype': rtype, 'metric': metric, 'elements': elements,
                                           'rname': rname, 'request_type': 'perform',
                                           'start-time': date + " " + time, 
                                           'unit': unit, 'value': unit_value }),
                    beforeSend: function () {
                        preloader.fadeIn()
                    },
                    complete: function () {
                        preloader.fadeOut()
                    },
                    success: function(response) {
                        
                        chart.data.datasets = []
                        all_values = response.values
                        
                        for (let i in all_values) {
                            //цвет линии графика
                            var r = Math.floor(Math.random() * 255);
                            var g = Math.floor(Math.random() * 255);
                            var b = Math.floor(Math.random() * 255);
                            var a = 1
                            data = []
                            var dataset = {
                                label: i,
                                borderColor: [
                                    'rgba(' + r + ',' + g + ',' + b + ',' + a + ')',
                                ],
                                borderWidth: 1,
                                data: data,
                                fill: false
                            };
                            for (let key in all_values[i]) {
                                //координаты точки на графике
                                var coordinate_t_y = {t: key, y: all_values[i][key]}
                                data.push(coordinate_t_y)
                            }
                            chart.data.datasets.push(dataset)
                        }
                        if (Object.keys(all_values).length > 20) {
                            legen_position = 'bottom'
                        } else {
                            legen_position = 'right'
                        }
                        displayLegend = true;
                        if (Object.keys(all_values)[0] == '-') { //если "-" то не показывать легенду
                            displayLegend = false;
                        }
                        chart.options.legend = {
                                        display: displayLegend,
                                        position: legen_position,
                                        onClick: LegendClickHandler
                        },
                        chart.options.tooltips = {
                            mode: 'point',
                            callbacks: {
                                footer: function(tooltipItems, data) {
                                    let numberOfElements = data.datasets[tooltipItems[0].datasetIndex].data.length
                                    let avgValue = 0
                                    let minValue = Math.min(...data.datasets[tooltipItems[0].datasetIndex].data.map(item => item.y))
                                    let maxValue = Math.max(...data.datasets[tooltipItems[0].datasetIndex].data.map(item => item.y))
                                    
                                    data.datasets[tooltipItems[0].datasetIndex].data.forEach(function(el){
                                        avgValue += parseFloat(el.y)
                                    });

                                    return 'Среднее: ' + (avgValue/numberOfElements).toPrecision(3) +
                                           '\nМинимальное: ' + minValue + 
                                           '\nМаксимальное: ' + maxValue;
                                },
                            },
                            footerFontStyle: 'normal'
                        }
                        chart.options.title = {
                                        display: true,
                                        text: $("select[name=metric] option:selected").html()
                        }
                        chart.options.scales.xAxes = [{
                                            display: true,
                                            type: 'time',
                                            time: {
                                                displayFormats: {
                                                    'minute': 'HH:mm',
                                                    'hour': 'H',
                                                    'day': 'MM-DD'}
                                                },
                                            unit: 'minute',
                                            unitStepSize: '10'
                                        }]
                        chart.options.scales.yAxes = [{
                                            ticks: {
                                                beginAtZero: true
                                            }
                        }]
                        templateElementsUpdater(Object.keys(all_values))
                        chart.update();
                    },
                    error: function(data) {
                        console.log('Ошибка загрузки данных')
                    },
                    timeout: 10000
                });
            }
        });

    //кнопка выгрузки в xls
    $("button#xls").on('click', function () {
        var preloader = $('#preloader');
        rtype = $("select[name=rtype]").val()
        rname = $("select[name=rname]").val()
        metric = $("select[name=metric]").val()
        unit = $("select#unit option:selected").val()
        unit_value = $("select#unit-value option:selected").val()
        date = $("#datepicker").val()
        time = $("#start-time").val()
        elements = $("#template-elements").val()

        $.ajax({
            type: "POST",
            url: "/get_xls",
            data: JSON.stringify({ 'rtype': rtype, 'metric': metric, 'elements': elements,
                                           'rname': rname, 'request_type': 'perform',
                                           'start-time': date + " " + time, 
                                           'unit': unit, 'value': unit_value }),
            xhrFields: {
                responseType: 'blob'
            },
            beforeSend: function () {
                preloader.fadeIn()
            },
            complete: function () {
                preloader.fadeOut()
            },
            success: function(blob, response, xhr) {
                var filename = "";
                var disposition = xhr.getResponseHeader('Content-Disposition');
                if (disposition && disposition.indexOf('attachment') !== -1) {
                    var filenameRegex = /filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/;
                    var matches = filenameRegex.exec(disposition);
                    if (matches != null && matches[1]) filename = matches[1].replace(/['"]/g, ''); }

                if (typeof window.navigator.msSaveBlob !== 'undefined') {
                    window.navigator.msSaveBlob(blob, filename); } else {
                    var URL = window.URL || window.webkitURL;
                    var downloadUrl = URL.createObjectURL(blob);

                    if (filename) {
                        var a = document.createElement("a");
                        if (typeof a.download === 'undefined') {
                            window.location.href = downloadUrl;
                        } else {
                            a.href = downloadUrl;
                            a.download = filename;
                            document.body.appendChild(a);
                            a.click();
                        }
                    } else {
                        window.location.href = downloadUrl;
                    }

                    setTimeout(function () { URL.revokeObjectURL(downloadUrl); }, 100);  }
            }
        });
    });

    //кнопка сохранения шаблона
    $("#saveTemplate").on('click', function () {
        rtype = $("select[name=rtype]").val()
        rname = $("select[name=rname]").val()
        metric = $("select[name=metric]").val()
        title = $("select[name=metric] option:selected").html()
        desc = $("#desc").val()
        elements = $("select#template-elements").val()
        unit = $("select#unit option:selected").val()
        unit_value = $("select#unit-value option:selected").val()
        if ($("#template-elements").val().length == 0) {
            $("#template-elements option").each(function() {
            $(this).prop('selected', true)
            });
        }
        elements = $("#template-elements").val()

        $.ajax({
            type: "POST",
            contentType: 'application/json; charset=utf-8',
            dataType: 'json',
            url: "/add_template",
            data: JSON.stringify({ 'rtype': rtype, 'rname': rname, 'metric_id': metric,
                                    'desc': desc, 'elements': elements, 'title': title,
                                    'unit': unit, 'value': unit_value}),
            success: function(response) {
                if (response.success) {
                    $('div.modal-header').after('<div class="alert alert-success">Добавлено</div>');
                    setTimeout(function(){
                            $('div.modal-header').next().remove();
                    }, 2000);
                } else {
                    $('div.modal-header').after('<div class="alert alert-warning">Ошибка:<br>Ошибка сохранения</div>');
                    setTimeout(function(){
                        $('div.modal-header').next().remove();
                    }, 3000);
                }
            },
            error: function(data) {
                $('div.modal-header').after('<div class="alert alert-warning">Ошибка сохранения</div>');
                setTimeout(function(){
                        $('div.modal-header').next().remove();
                }, 3000);
            },
            timeout: 10000
        })
    })


    //поиск по списку элементов
    $("#searchElement").on('keyup', function(){
        let search = $("#searchElement").val().toLowerCase();
        $("#template-elements option").filter(function(){
            $(this).toggle($(this).text().toLowerCase().indexOf(search) > -1 )
        })
    })
});