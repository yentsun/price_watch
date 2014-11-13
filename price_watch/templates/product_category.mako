<%inherit file="base.mako"/>
<div class="pull-right well well-sm cat-price">
    ${view.currency(req.context.get_price(), u'р.')}
</div>
<h1>
    <%block name="title">${req.context.get_data('keyword')}</%block>
</h1>
<div class="row-fluid marketing">
    <div class="span12">
        <table class="table">
            <thead>
            <tr>
                <th>№</th>
                <th>Продукт</th>
                <th class="price">Цена</th>
            </tr>
            </thead>
            <tbody>
                % for num, product in enumerate(sorted(req.context.get_qualified_products(), \
                                                              key=lambda pr: pr.get_price())):
                    <tr>
                        <td>${num+1}</td>
                        <td>
                            <a href="${req.resource_url(product)}">
                                ${product.title}
                            </a>
                        </td>
                        <td>
                            ${view.currency(product.get_price())}&nbsp;
                            <% delta = product.get_price_delta(view.week_ago) %>
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