function renderChart(chartContainer) {
    const identifier = chartContainer.getAttribute('data-stretchgoal-chart');
    const label_text = chartContainer.getAttribute('data-chart-label');

    $(chartContainer).css("height", "300px");

    const script = $(chartContainer).find("script");
    const data = JSON.parse(script.innerHTML);
    script.remove();

    new Morris.Area({
        element: identifier + '_chart',
        goals: data.target,
        data: data.data,
        xkey: 'date',
        ykeys: ['price'],
        labels: [label_text],
        yLabelFormat: function (x) { return x.toFixed(2) },
        ymin: data.ymin || "auto",
        postUnits: ' €',
        smooth: false,
        resize: true,
        fillOpacity: 0.3,
        behaveLikeLine: true,
        goalLineColors: ["#33c33c"],
        goalStrokeWidth: 4,
    });
}
$(function () {
    for(const container of document.querySelectorAll('[data-stretchgoal-chart]')) {
        renderChart(container);
    }
});