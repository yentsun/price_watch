<%inherit file="base.mako"/>
<div class="pull-right well well-sm cat-price">
    ${median_price}
</div>
<h1>
    <%block name="title">${cat_title}</%block>
</h1>
<div class="row-fluid marketing">
    <div class="span12">
        <div id="chart_div" style="width: 700px; height: 300px;"></div>
        <table class="table">
            <thead>
            <tr>
                <th>№</th>
                <th>Продукт</th>
                <th class="price">Цена</th>
            </tr>
            </thead>
            <tbody>
                % for num, product, url, price, delta in products:
                    <tr>
                        <td>${num}</td>
                        <td>
                            <a href="${url}">
                                ${product.title}
                            </a>
                        </td>
                        <td>
                            ${price}
                            % if delta > 0:
                            <span class="glyphicon glyphicon-arrow-up" style="color:red"></span>
                            % elif delta < 0:
                                <span class="glyphicon glyphicon-arrow-down" style="color:green"></span>
                            % endif
                        </td>
                    </tr>
                % endfor
            </tbody>
        </table>
    </div>
</div>
<%def name="js()">
    <script type="text/javascript" src="https://www.google.com/jsapi"></script>
    <script type="text/javascript">
        google.load("visualization", "1", {packages:["corechart"]});
        google.setOnLoadCallback(drawChart);
        function drawChart() {
            var headers = [['Дата', 'Средняя цена, руб.']];
            var data = google.visualization.arrayToDataTable(
                headers.concat(${price_data|n})
            );
            var options = {
                title: 'Динамика цен',
                curveType: 'function',
                legend: {position: 'top'},
                chartArea:{left:50, top:50, width:'90%', height:'75%'}
            };

            var chart = new google.visualization.LineChart(document.getElementById('chart_div'));

            chart.draw(data, options);
        }
    </script>
</%def>