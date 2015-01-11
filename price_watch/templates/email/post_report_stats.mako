<h2>Всего отчетов: ${counts['total']}</h2>
<p>Авторы: ${', '.join(reporters)}</p>
<h3>Новые</h3>
<table>
    <tbody>
        <tr>
            <td>отчеты</td><td>${counts['report']}</td>
        </tr>
        <tr>
            <td>продукты</td><td>${counts['product']}</td>
        </tr>
    </tbody>
</table>
<h3>Ошибки: ${counts['error']}</h3>
% for msg in error_msgs:
<p>${msg}</p>
% endfor