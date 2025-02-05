window.dashExtensions = Object.assign({}, window.dashExtensions, {
    default: {
        function0: function(clickData) {
            if (clickData && clickData.points[0].customdata) {
                window.open(clickData.points[0].customdata, '_blank');
            }
        }

    }
});