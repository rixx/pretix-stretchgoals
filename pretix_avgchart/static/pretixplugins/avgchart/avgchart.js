/*globals $, Morris, gettext*/
$(function () {
    $(".chart").css("height", "250px");
    new Morris.Area({
        element: 'avg_chart',
        data: JSON.parse($("#avg-data").html()),
        xkey: 'date',
        ykeys: ['price'],
        labels: [gettext('Average ticket price')],
        smooth: false,
        resize: true,
        fillOpacity: 0.3,
        behaveLikeLine: true
    });
});
