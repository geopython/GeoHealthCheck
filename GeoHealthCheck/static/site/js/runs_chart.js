// Setup Chart

function prepData(rawData, hoverTemplate) {
    var xField = 'datetime';
    var yField = 'value';
    var idField = 'id';
    var successField = 'success';
    var x = [];
    var y = [];
    var ids = [];
    var markerColors = [];
    rawData.forEach(function (datum, i) {

        x.push(new Date(datum[xField]));
        y.push(datum[yField]);
        ids.push(datum[idField]);
        if (datum[successField] === 1) {
            markerColors.push('#5CB85C');
        } else {
            markerColors.push('#D9534F');
        }
    });

    return [{
        name: '',
        type: 'scatter',
        mode: 'lines+markers',
        hovertemplate: hoverTemplate,
        hoverlabel: {
            bgcolor: '#EEEEEE'
        },
        line: {
            color: '#0000CC',
            width: 1
        },

        marker: {
            color: markerColors,
            size: 8,
            line: {
                color: '#111111',
                width: 1
            }
        },
        x: x,
        y: y,
        ids: ids
    }];
}

function showRunDetails(runURL) {
    $.ajax({
        type: "GET",
        url: runURL,
        contentType: "application/json; charset=utf-8",
        dataType: "json",
        success: function (data) {
            // Format JSON: http://jsfiddle.net/K83cK
            var runData = data.runs[0];
            $('#run-chart-hover-date').text(runData.checked_datetime);
            $('#run-chart-hover-resptime').text(runData.response_time.toFixed(2) + ' s');
            $('#run-chart-hover-msg').text(runData.message);
            $('#run-open').removeClass('disabled').attr("href", runURL + '.html');
        },
        error: function (errMsg) {
            $('#run-chart-hover').text("Error: " + errMsg);
        }
    });
}

function drawChart(elementId, runData, resourceURL, hoverTemplate) {
    var runChart = document.getElementById(elementId);
    if (!runChart) {
        return;
    }

    var selectorOptions = {
        buttons: [
            {
                step: 'hour',
                stepmode: 'backward',
                count: 1,
                label: '1h'
            },
            {
                step: 'hour',
                stepmode: 'backward',
                count: 6,
                label: '6h'
            },
            {
                step: 'hour',
                stepmode: 'backward',
                count: 24,
                label: '24h'
            },
            {
                step: 'week',
                stepmode: 'backward',
                count: 1,
                label: '1w'
            },
            {
                step: 'month',
                stepmode: 'backward',
                count: 1,
                label: '1m'
            },
            {
                step: 'all',
            }],
    };

    var data = prepData(runData, hoverTemplate);

    var layout = {
        title: 'Probe Runs',
        hovermode: 'closest',
        paper_bgcolor: '#EEEEEE',
        xaxis: {
            type: 'date',
            rangeselector: selectorOptions,
            rangeslider: {
                bgcolor: '#DDDDDD'
            },
            title: {
                text: 'Date'
            }
        },
        yaxis: {
            type: 'linear',
            fixedrange: true,
            title: {
                text: 'Duration (secs)'
            }
        }
    };

    var options = {
        scrollZoom: true, // lets us scroll to zoom in and out - works
        showLink: false, // removes the link to edit on plotly - works
        // Names: https://github.com/plotly/plotly.js/blob/master/src/components/modebar/buttons.js
        modeBarButtonsToRemove: ['lasso2d', 'zoom2d', 'pan', 'pan2d', 'autoScale2d', 'sendDataToCloud', 'hoverCompareCartesian', 'hoverClosestCartesian', 'toggleSpikelines', 'select2d'],
        // modeBarButtonsToAdd: ['lasso2d'],
        displayLogo: false, // this one also seems to not work
        displayModeBar: true, //this one does work
    };

    function waitForPlotly() {
        if (window.Plotly) {
            Plotly.plot(runChart, data, layout, options);

            runChart.on('plotly_hover', function (data) {
                showRunDetails(resourceURL + '/' + data.points[0].id);
            });

            runChart.on('plotly_click', function (data) {
                showRunDetails(resourceURL + '/' + data.points[0].id);
            });
        }
        else {
            if (console) {
                console.log('Wait for Plotly...');
            }
            window.setTimeout("waitForPlotly();", 100);
        }
    }

    // Start drawing when Plotly completely ready
    waitForPlotly();
}