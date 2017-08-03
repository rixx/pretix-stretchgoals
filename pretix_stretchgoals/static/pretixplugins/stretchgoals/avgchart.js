/*globals $, Morris, gettext*/
$(function () {
    $(".chart").css("height", "250px");

    new Morris.Area({
        element: 'avg_chart',
        goals: [JSON.parse($("#avg-data").html()).target],
        data: JSON.parse($("#avg-data").html()).data,
        xkey: 'date',
        ykeys: ['price'],
        labels: [gettext('Average ticket price')],
        postUnits: ' €',

        smooth: false,
        resize: true,
        fillOpacity: 0.3,
        behaveLikeLine: true,
        goalLineColors: ["#33c33c"],
        goalStrokeWidth: 4,
    });
});
