$(document).ready(function(){

    //выставить часы в селекторе
    date = new Date()
    hour = date.toLocaleString('Ru-RU', {hour: '2-digit', hour12: false, timeZone:'Europe/Moscow'})
    time_selector = $("#start-time option:contains(" + hour +")")
    $(time_selector).prop('selected', true)

    
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


    //запрос данных и обновление графика
    function ajaxRequestUpdateData(data) {
        var preloader = $('#preloader');
        $.ajax({
            type: "POST",
            contentType: 'application/json; charset=utf-8',
            dataType: 'json',
            url: "/reports",
            data: JSON.stringify(data),
            beforeSend: function () {
                preloader.fadeIn()
            },
            complete: function () {
                preloader.fadeOut()
            },
            success: function(response) {
                $('button#submit, button#xls, button#delTemplate, button#compare').prop('disabled', false)
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
                        }
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
                                        text: $("select#templates option:selected").attr("title")
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
                        //обновление значений в селекторах
                        $("#unit-value").val(response.value)
                        $("#unit").val(response.unit)
                        chart.update();

            }
        });
    }

    //выбор из списка шаблонов и нажатие кнопки "показать"
    $("select#templates, button#submit").on('click', function () {
        
        date = $("#datepicker").val()
        time = $("#start-time").val()
        report = $("select#templates option:selected").val()
        data = {}
        //добавляем атрибут кнопке xls
        $("button#xls").data("compare", false)

        if ($(this).attr('id') == 'templates') {
            data = {'report': report, 'start-time': date + " " + time}
        } else {
            unit = $("select#unit option:selected").val()
            unit_value = $("select#unit-value option:selected").val()
            data = {'report': report, 'unit': unit, 'value': unit_value, 'start-time': date + " " + time}
        }
        if ($(this).val() != null) {    // если не пустое значение в списке шаблонов
            ajaxRequestUpdateData(data)  //обновляем данные
        }
    });

    //кнопка выгрузки в xls
    $("button#xls").on('click', function () {
        var preloader = $('#preloader');
        report = $("select#templates option:selected").val()
        unit = $("select#unit option:selected").val()
        unit_value = $("select#unit-value option:selected").val()
        date = $("#datepicker").val()
        time = $("#start-time").val()
        var compare = $("button#xls").data("compare")

        $.ajax({
            type: "POST",
            url: "/get_xls",
            data: JSON.stringify({ 'request_report': report, 'unit': unit, 'value': unit_value, 
                                    'start-time': date + " " + time, 'is-compare': compare}),
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
    })

    //кнопка удаления отчета
    $("button#delTemplate").on('click', function () {
        var id = $("#templates").val()
        var preloader = $('#preloader');
        $.ajax({
            type: "POST",
            url: "/reports/delete",
            data: JSON.stringify({'id': id}),
            beforeSend: function () {
                preloader.fadeIn()
            },
            complete: function () {
                preloader.fadeOut()
            },
            success: function(response) {
                if (response.success) {
                    $("#templates option[value=" + id + "]").remove()
                }
                
            }
        })
    })

    //кнопка сравнения с другими системами
    $("button#compare").on('click', function () {
        date = $("#datepicker").val()
        time = $("#start-time").val()
        report = $("select#templates option:selected").val()
        unit = $("select#unit option:selected").val()
        unit_value = $("select#unit-value option:selected").val()
        data = {'report': report, 'unit': unit, 'value': unit_value, 
                'start-time': date + " " + time, 'is-compare': true}

        ajaxRequestUpdateData(data)  //запрашиваем данные
        //добавляем атрибут кнопке xls для выгрузки сравнительных данных
        $("button#xls").data("compare", true) 
    })
    
});